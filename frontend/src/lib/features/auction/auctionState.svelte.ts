/* eslint-disable svelte/prefer-svelte-reactivity -- every Map and Set here is rebuilt by $derived, never mutated. */
import { saveFile } from '$lib/api';
import {
	amendPurchase,
	cancelPurchase,
	completeAuction,
	exportAuctionReport,
	getAuction,
	recordPurchase,
	reopenAuction,
	setAuctionStrategy,
	startAuction,
	type Auction,
	type Purchase
} from '$lib/auctions';
import { confirmDialog, type DialogOptions } from '$lib/dialog.svelte';
import { t } from '$lib/i18n';
import { getPlayers, type Player } from '$lib/players';
import {
	getStrategies,
	getStrategy,
	percentageToCredits,
	strategyIndex,
	type Strategy,
	type StrategySummary
} from '$lib/strategies';
import { pushErrorToast } from '$lib/toast.svelte';

/** The state and the actions of the auction page; the page only lays them out. */
export class AuctionState {
	auction = $state<Auction>();
	players = $state<Player[]>([]);
	strategies = $state<StrategySummary[]>([]);
	viewedStrategy = $state<Strategy>();
	viewingStrategyId = $state('');
	#calledPlayerId = $state('');
	loading = $state(true);
	saving = $state(false);

	#playersById = $derived(new Map(this.players.map((player) => [player.id, player])));
	#strategyIndex = $derived(this.viewedStrategy && strategyIndex(this.viewedStrategy));
	sortedTiers = $derived(this.#strategyIndex?.sortedTiers ?? []);
	purchasedIds = $derived(new Set(this.auction?.purchased_player_ids ?? []));

	calledPlayer = $derived(this.#playersById.get(this.#calledPlayerId));
	callablePlayers = $derived(
		this.players.filter((player) => player.active && !this.purchasedIds.has(player.id))
	);
	/** All purchases across every participant, newest first. */
	allPurchases = $derived.by(() => {
		if (!this.auction) return [];
		return this.auction.participants
			.flatMap((participant) =>
				participant.purchases.map((purchase) => ({ purchase, participant }))
			)
			.sort((first, second) => (first.purchase.created_at < second.purchase.created_at ? 1 : -1));
	});
	#purchaseByPlayerId = $derived(
		new Map(this.allPurchases.map((record) => [record.purchase.player_id, record]))
	);

	readonly #getAuctionId: () => string | undefined;

	constructor(getAuctionId: () => string | undefined) {
		this.#getAuctionId = getAuctionId;
	}

	async load(): Promise<void> {
		this.loading = true;
		try {
			[this.auction, this.players, this.strategies] = await Promise.all([
				getAuction(this.#currentAuctionId()),
				getPlayers({ includeInactive: true }),
				getStrategies()
			]);
			this.viewingStrategyId = this.auction.strategy_id ?? '';
			await this.viewSelectedStrategy();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			this.loading = false;
		}
	}

	async viewSelectedStrategy(): Promise<void> {
		const strategyId = this.viewingStrategyId;
		try {
			const strategy = strategyId ? await getStrategy(strategyId) : undefined;
			// Another strategy may have been chosen while this one was loading.
			if (this.viewingStrategyId === strategyId) this.viewedStrategy = strategy;
		} catch (caught) {
			if (this.viewingStrategyId !== strategyId) return;
			this.viewingStrategyId = this.viewedStrategy?.id ?? '';
			pushErrorToast(caught);
		}
	}

	async fixViewedStrategy(): Promise<void> {
		await this.#runMutation((auctionId) =>
			setAuctionStrategy(auctionId, this.viewingStrategyId || null)
		);
	}

	async changeStatus(action: 'start' | 'complete' | 'reopen'): Promise<void> {
		if (
			action === 'complete' &&
			!(await confirmDialog({
				title: t.auction.endAuction,
				message: t.auction.endAuctionMessage,
				confirmLabel: t.auction.endAuction,
				danger: true
			}))
		)
			return;
		await this.#runMutation(async (auctionId) => {
			if (action === 'start') await startAuction(auctionId);
			if (action === 'complete') {
				await completeAuction(auctionId);
				this.cancelCall();
			}
			if (action === 'reopen') await reopenAuction(auctionId);
		});
	}

	canCall(playerId: string): boolean {
		return (
			this.auction?.status === 'live' &&
			!!this.#playersById.get(playerId)?.active &&
			!this.purchasedIds.has(playerId)
		);
	}

	callPlayer(playerId: string): void {
		if (this.canCall(playerId)) this.#calledPlayerId = playerId;
	}

	cancelCall(): void {
		this.#calledPlayerId = '';
	}

	async registerPurchase(participantId: string, price: number): Promise<boolean> {
		const playerId = this.#calledPlayerId;
		return this.#runMutation(async (auctionId) => {
			await recordPurchase(auctionId, playerId, participantId, price);
			// Another player may have been called in the meantime.
			if (this.#calledPlayerId === playerId) this.cancelCall();
		});
	}

	entryForPlayer(playerId: string) {
		return this.#strategyIndex?.entryByPlayerId.get(playerId);
	}

	tierForPlayer(playerId: string) {
		const tierId = this.entryForPlayer(playerId)?.tier_id;
		return tierId == null ? undefined : this.#strategyIndex?.tierById.get(tierId);
	}

	purchaseOfPlayer(playerId: string) {
		return this.#purchaseByPlayerId.get(playerId);
	}

	maximumPriceCredits(percentage: number | null | undefined): number | null {
		return percentage != null && this.auction
			? percentageToCredits(percentage, this.auction.initial_credits)
			: null;
	}

	async savePurchase(purchaseId: string, participantId: string, price: number): Promise<boolean> {
		if (this.auction?.status !== 'live' || this.saving) return false;
		return this.#runMutation((auctionId) =>
			amendPurchase(auctionId, purchaseId, participantId, price)
		);
	}

	async deletePurchase(purchase: Purchase): Promise<void> {
		await this.#confirmPurchaseCancellation(purchase.id, {
			title: t.auction.cancelPurchase,
			message: t.auction.cancelPurchaseMessage(purchase.player_name),
			cancelLabel: t.auction.keepPurchase
		});
	}

	async undoLastPurchase(): Promise<void> {
		const latest = this.allPurchases[0];
		if (!latest) return;
		const { purchase, participant } = latest;
		await this.#confirmPurchaseCancellation(purchase.id, {
			title: t.auction.undoLastPurchaseTitle,
			message: t.auction.undoLastPurchaseMessage(
				purchase.player_name,
				participant.name,
				purchase.price
			),
			cancelLabel: t.auction.keepPurchase
		});
	}

	async #confirmPurchaseCancellation(
		purchaseId: string,
		options: Pick<DialogOptions, 'title' | 'message' | 'cancelLabel'>
	): Promise<void> {
		if (this.auction?.status !== 'live' || this.saving) return;
		const confirmed = await confirmDialog({
			...options,
			confirmLabel: t.auction.cancelPurchase,
			danger: true
		});
		if (!confirmed || this.auction?.status !== 'live' || this.saving) return;
		await this.#runMutation((auctionId) => cancelPurchase(auctionId, purchaseId));
	}

	// Through fetch, like the strategy export: the app window has no Back button, so navigating
	// to the report (HTML, which the window could display) must never replace the interface.
	async downloadReport(): Promise<void> {
		try {
			saveFile(await exportAuctionReport(this.#currentAuctionId()));
		} catch (caught) {
			pushErrorToast(caught);
		}
	}

	async #runMutation(mutation: (auctionId: string) => Promise<unknown>): Promise<boolean> {
		this.saving = true;
		try {
			const auctionId = this.#currentAuctionId();
			await mutation(auctionId);
			this.auction = await getAuction(auctionId);
			return true;
		} catch (caught) {
			pushErrorToast(caught);
			return false;
		} finally {
			this.saving = false;
		}
	}

	#currentAuctionId(): string {
		const auctionId = this.#getAuctionId();
		if (!auctionId) throw new Error(t.errors.auction_not_found);
		return auctionId;
	}
}
