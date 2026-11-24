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
	type Participant,
	type Purchase
} from '$lib/auctions';
import { confirmDialog } from '$lib/dialog.svelte';
import { sortMantraRoles } from '$lib/mantraRoles';
import { getPlayers, type Player, type Role } from '$lib/players';
import { matchesSearch, nameMatchRank } from '$lib/search';
import {
	byMaxPercentageDesc,
	getStrategies,
	getStrategy,
	percentageToCredits,
	strategyIndex,
	type Strategy,
	type StrategySummary
} from '$lib/strategies';
import { pushErrorToast } from '$lib/toast.svelte';

type CatalogSort = 'tier' | 'quotation';

/** The state and the actions of the auction page; the page only lays them out. */
export class AuctionState {
	auction = $state<Auction>();
	players = $state<Player[]>([]);
	strategies = $state<StrategySummary[]>([]);
	viewedStrategy = $state<Strategy>();
	viewingStrategyId = $state('');
	playerSearch = $state('');
	selectedPlayerId = $state('');
	selectedParticipantId = $state('');
	price = $state(1);
	editingPurchaseId = $state('');
	editedParticipantId = $state('');
	editedPrice = $state(1);
	registryOpen = $state(false);
	registrySearch = $state('');
	strategyRole = $state<Role>('P');
	catalogRole = $state<Role>('P');
	catalogMantraRoles = $state<string[]>([]);
	catalogSort = $state<CatalogSort>('tier');
	loading = $state(true);
	saving = $state(false);

	#playersById = $derived(new Map(this.players.map((player) => [player.id, player])));
	#strategyIndex = $derived(this.viewedStrategy && strategyIndex(this.viewedStrategy));
	purchasedIds = $derived(new Set(this.auction?.purchased_player_ids ?? []));

	/** Tiers for the selected strategy role, with their entries resolved once. */
	strategyRoleTiers = $derived.by(() => {
		const strategy = this.viewedStrategy;
		if (!strategy || !this.#strategyIndex) return [];
		return this.#strategyIndex.sortedTiers.map((tier) => {
			const entries = strategy.entries
				.filter((entry) => entry.role === this.strategyRole && entry.tier_id === tier.id)
				.sort(byMaxPercentageDesc((entry) => entry.maximum_price_percentage));
			return {
				tier,
				entries,
				availableCount: entries.filter((entry) => !this.purchasedIds.has(entry.player_id)).length
			};
		});
	});
	matchingPlayers = $derived.by(() => {
		const search = this.playerSearch;
		return this.players
			.filter(
				(player) =>
					player.active &&
					!this.purchasedIds.has(player.id) &&
					matchesSearch(search, player.name, player.team)
			)
			.sort(
				(first, second) => nameMatchRank(first.name, search) - nameMatchRank(second.name, search)
			)
			.slice(0, 20);
	});
	/** All purchases across every participant, newest first, for the purchase registry. */
	allPurchases = $derived.by(() => {
		if (!this.auction) return [];
		return this.auction.participants
			.flatMap((participant) =>
				participant.purchases.map((purchase) => ({ purchase, participant }))
			)
			.sort((first, second) => (first.purchase.created_at < second.purchase.created_at ? 1 : -1));
	});
	filteredRegistryPurchases = $derived(
		this.allPurchases.filter(({ purchase }) =>
			matchesSearch(this.registrySearch, purchase.player_name)
		)
	);
	selectedPlayer = $derived(this.#playersById.get(this.selectedPlayerId));
	selectedStrategyEntry = $derived(this.#strategyIndex?.entryByPlayerId.get(this.selectedPlayerId));
	selectedMaximumPriceCredits = $derived(
		this.maximumPriceCredits(this.selectedStrategyEntry?.maximum_price_percentage)
	);
	selectedTier = $derived(this.tierForPlayer(this.selectedPlayerId));
	#catalogRolePlayers = $derived(
		this.players.filter(
			(player) =>
				player.role === this.catalogRole && (player.active || this.purchasedIds.has(player.id))
		)
	);
	catalogMantraCodes = $derived(
		sortMantraRoles([...new Set(this.#catalogRolePlayers.flatMap((player) => player.mantra_roles))])
	);
	catalogPlayers = $derived.by(() => {
		return this.#catalogRolePlayers
			.filter(
				(player) =>
					this.catalogMantraRoles.length === 0 ||
					this.catalogMantraRoles.some((role) => player.mantra_roles.includes(role))
			)
			.sort((first, second) => {
				if (this.catalogSort === 'tier' && this.viewedStrategy) {
					const firstPosition = this.#tierPosition(first.id);
					const secondPosition = this.#tierPosition(second.id);
					if (firstPosition < secondPosition) return -1;
					if (firstPosition > secondPosition) return 1;
				}
				const quotationDifference = (second.quotation ?? -1) - (first.quotation ?? -1);
				return quotationDifference || first.name.localeCompare(second.name, 'it');
			});
	});

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
			this.selectedParticipantId ||= this.auction.participants[0]?.id ?? '';
			this.viewingStrategyId = this.auction.strategy_id ?? '';
			await this.#loadViewedStrategy();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			this.loading = false;
		}
	}

	async viewSelectedStrategy(): Promise<void> {
		try {
			await this.#loadViewedStrategy();
		} catch (caught) {
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
				title: 'Termina asta',
				message: 'Terminare questa asta? Potrai riaprirla in seguito.',
				confirmLabel: 'Termina asta'
			}))
		)
			return;
		await this.#runMutation(async (auctionId) => {
			if (action === 'start') await startAuction(auctionId);
			if (action === 'complete') await completeAuction(auctionId);
			if (action === 'reopen') await reopenAuction(auctionId);
		});
	}

	async registerPurchase(): Promise<void> {
		if (!this.selectedPlayerId || !this.selectedParticipantId) return;
		await this.#runMutation(async (auctionId) => {
			await recordPurchase(
				auctionId,
				this.selectedPlayerId,
				this.selectedParticipantId,
				this.price
			);
			this.selectedPlayerId = '';
			this.playerSearch = '';
			this.price = 1;
		});
	}

	selectPlayer(player: Player): void {
		this.selectedPlayerId = player.id;
		this.playerSearch = player.name;
	}

	selectTopMatch(): void {
		const [topMatch] = this.matchingPlayers;
		if (topMatch) this.selectPlayer(topMatch);
	}

	callPlayer(playerId: string): boolean {
		if (this.auction?.status !== 'live' || this.purchasedIds.has(playerId)) return false;
		const player = this.#playersById.get(playerId);
		if (!player) return false;
		this.selectPlayer(player);
		return true;
	}

	tierForPlayer(playerId: string) {
		const tierId = this.#strategyIndex?.entryByPlayerId.get(playerId)?.tier_id;
		return tierId == null ? undefined : this.#strategyIndex?.tierById.get(tierId);
	}

	maximumPriceCredits(percentage: number | null | undefined): number | null {
		return percentage != null && this.auction
			? percentageToCredits(percentage, this.auction.initial_credits)
			: null;
	}

	toggleCatalogMantraRole(code: string): void {
		this.catalogMantraRoles = this.catalogMantraRoles.includes(code)
			? this.catalogMantraRoles.filter((role) => role !== code)
			: [...this.catalogMantraRoles, code];
	}

	resetRegistry(): void {
		this.registrySearch = '';
		this.editingPurchaseId = '';
	}

	beginEdit(purchase: Purchase, participant: Participant): void {
		this.editingPurchaseId = purchase.id;
		this.editedParticipantId = participant.id;
		this.editedPrice = purchase.price;
	}

	async savePurchase(purchaseId: string): Promise<void> {
		await this.#runMutation(async (auctionId) => {
			await amendPurchase(auctionId, purchaseId, this.editedParticipantId, this.editedPrice);
			this.editingPurchaseId = '';
		});
	}

	async deletePurchase(purchase: Purchase): Promise<void> {
		const confirmed = await confirmDialog({
			title: 'Annulla acquisto',
			message: `Annullare l'acquisto di ${purchase.player_name}?`,
			confirmLabel: 'Annulla acquisto',
			danger: true
		});
		if (!confirmed) return;
		await this.#runMutation((auctionId) => cancelPurchase(auctionId, purchase.id));
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

	async #loadViewedStrategy(): Promise<void> {
		this.viewedStrategy = this.viewingStrategyId
			? await getStrategy(this.viewingStrategyId)
			: undefined;
		if (!this.viewedStrategy) this.catalogSort = 'quotation';
	}

	#tierPosition(playerId: string): number {
		return this.tierForPlayer(playerId)?.position ?? Number.POSITIVE_INFINITY;
	}

	async #runMutation(mutation: (auctionId: string) => Promise<unknown>): Promise<void> {
		this.saving = true;
		try {
			const auctionId = this.#currentAuctionId();
			await mutation(auctionId);
			this.auction = await getAuction(auctionId);
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			this.saving = false;
		}
	}

	#currentAuctionId(): string {
		const auctionId = this.#getAuctionId();
		if (!auctionId) throw new Error('Asta non trovata.');
		return auctionId;
	}
}
