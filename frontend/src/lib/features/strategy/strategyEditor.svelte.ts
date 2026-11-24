import { confirmDialog } from '$lib/dialog.svelte';
import { getPlayers, type Player, type Role } from '$lib/players';
import {
	addTier,
	byMaxPercentageDesc,
	getStrategy,
	removeTier,
	renameStrategy,
	reorderTiers,
	strategyIndex,
	tierColors,
	updateStrategyEntry,
	updateTier,
	type Strategy,
	type Tier
} from '$lib/strategies';
import { pushErrorToast } from '$lib/toast.svelte';

type EntryDraft = {
	tierId: string;
	note: string;
	maximumPricePercentage: number | undefined;
};

// Every field saves itself shortly after the user stops changing it.
const ENTRY_SAVE_DEBOUNCE_MS = 500;
const TIER_SAVE_DEBOUNCE_MS = 400;

/** Delays the save of each id until its changes settle. `persist` must handle its own errors. */
class DebouncedSaver {
	readonly #timers = new Map<string, ReturnType<typeof setTimeout>>();
	readonly #inFlight = new Set<Promise<void>>();
	readonly #delay: number;
	readonly #persist: (id: string) => Promise<void>;

	constructor(delay: number, persist: (id: string) => Promise<void>) {
		this.#delay = delay;
		this.#persist = persist;
	}

	schedule(id: string): void {
		clearTimeout(this.#timers.get(id));
		this.#timers.set(
			id,
			setTimeout(() => void this.saveNow(id), this.#delay)
		);
	}

	/** Saves now if a save is waiting on its debounce (e.g. on blur), otherwise a no-op. */
	async flush(id: string): Promise<void> {
		if (this.#timers.has(id)) await this.saveNow(id);
	}

	async saveNow(id: string): Promise<void> {
		clearTimeout(this.#timers.get(id));
		this.#timers.delete(id);
		const request = this.#persist(id);
		this.#inFlight.add(request);
		await request;
		this.#inFlight.delete(request);
	}

	/** Starts every waiting save synchronously, so that it also works while the page unloads. */
	async flushAll(): Promise<void> {
		await Promise.all([
			...this.#inFlight,
			...Array.from(this.#timers.keys(), (id) => this.flush(id))
		]);
	}
}

/** The state, the autosave and the actions of the strategy editor; the page only lays them out. */
export class StrategyEditor {
	strategy = $state<Strategy>();
	players = $state<Player[]>([]);
	strategyName = $state('');
	entryDrafts = $state<Record<string, EntryDraft>>({});
	entrySaved = $state<Record<string, boolean>>({});
	tierSaved = $state<Record<string, boolean>>({});
	loading = $state(true);
	saving = $state(false);
	orderedTiers = $state<Tier[]>([]);
	index = $derived(this.strategy && strategyIndex(this.strategy));

	readonly #entrySaves = new DebouncedSaver(ENTRY_SAVE_DEBOUNCE_MS, (id) => this.#persistEntry(id));
	readonly #tierSaves = new DebouncedSaver(TIER_SAVE_DEBOUNCE_MS, (id) => this.#persistTier(id));
	readonly #getStrategyId: () => string | undefined;

	constructor(getStrategyId: () => string | undefined) {
		this.#getStrategyId = getStrategyId;
	}

	async load(): Promise<void> {
		this.loading = true;
		try {
			const strategyId = this.#getStrategyId();
			if (!strategyId) throw new Error('Strategia non trovata.');
			const [strategy, players] = await Promise.all([
				getStrategy(strategyId),
				getPlayers({ includeInactive: true })
			]);
			this.players = players;
			this.#applyStrategy(strategy);
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			this.loading = false;
		}
	}

	tierOfPlayer(playerId: string): Tier | undefined {
		return this.index?.tierById.get(this.entryDrafts[playerId]?.tierId);
	}

	entriesForTier(tierId: string, role: Role) {
		return this.players
			.filter((player) => player.role === role && this.entryDrafts[player.id]?.tierId === tierId)
			.map((player) => ({ player, draft: this.entryDrafts[player.id] }))
			.sort(byMaxPercentageDesc((entry) => entry.draft.maximumPricePercentage));
	}

	async rename(): Promise<void> {
		const name = this.strategyName.trim();
		const strategy = this.strategy;
		if (!strategy || !name) return;
		await this.#runMutation(async () => {
			await renameStrategy(strategy.id, name);
			strategy.name = name;
		});
	}

	/** Adds a tier to rename in place. Returns its id, or undefined if the addition failed. */
	async addTier(): Promise<string | undefined> {
		const strategyId = this.strategy?.id;
		if (!strategyId) return;
		let tierId: string | undefined;
		await this.#runMutation(async () => {
			await this.flushAll();
			const color = tierColors[this.orderedTiers.length % tierColors.length];
			tierId = (await addTier(strategyId, this.#newTierName(), color)).id;
			this.#applyStrategy(await getStrategy(strategyId));
		});
		return tierId;
	}

	async deleteTier(tier: Tier): Promise<void> {
		const strategyId = this.strategy?.id;
		if (!strategyId) return;
		const confirmed = await confirmDialog({
			title: 'Elimina fascia',
			message: `Eliminare la fascia “${tier.name}”?`,
			confirmLabel: 'Elimina',
			danger: true
		});
		if (!confirmed) return;
		await this.#runMutation(async () => {
			await this.flushAll();
			await removeTier(strategyId, tier.id);
			this.#applyStrategy(await getStrategy(strategyId));
		});
	}

	/** Called once by the drag/keyboard reorder gesture, with the final tier order. */
	async commitTierOrder(nextIds: string[]): Promise<void> {
		const strategyId = this.strategy?.id;
		if (!strategyId || !this.index) return;
		const { tierById } = this.index;
		this.orderedTiers = nextIds.map((id) => tierById.get(id)).filter((tier) => tier !== undefined);
		await this.#runMutation(() => reorderTiers(strategyId, nextIds));
	}

	/** For free text: one request when the typing settles, not one per keystroke. */
	scheduleEntrySave(playerId: string): void {
		this.#entrySaves.schedule(playerId);
	}

	/** For a discrete, deliberate choice like a tier pick. */
	saveEntryNow(playerId: string): Promise<void> {
		return this.#entrySaves.saveNow(playerId);
	}

	flushEntrySave(playerId: string): Promise<void> {
		return this.#entrySaves.flush(playerId);
	}

	scheduleTierSave(tierId: string): void {
		this.#tierSaves.schedule(tierId);
	}

	flushTierSave(tierId: string): Promise<void> {
		return this.#tierSaves.flush(tierId);
	}

	/** Persists the waiting autosaves, e.g. before a full re-fetch overwrites the local state. */
	async flushAll(): Promise<void> {
		await Promise.all([this.#entrySaves.flushAll(), this.#tierSaves.flushAll()]);
	}

	/** The backend wants the tier names of a strategy to be unique. */
	#newTierName(): string {
		const taken = this.orderedTiers.map((tier) => tier.name.trim().toLowerCase());
		const base = 'Nuova fascia';
		let name = base;
		for (let number = 2; taken.includes(name.toLowerCase()); number++) name = `${base} ${number}`;
		return name;
	}

	async #persistEntry(playerId: string): Promise<void> {
		const draft = this.entryDrafts[playerId];
		if (!this.strategy || !draft) return;
		try {
			await updateStrategyEntry(
				this.strategy.id,
				playerId,
				draft.tierId || null,
				draft.note,
				draft.maximumPricePercentage ?? null
			);
			this.#flashSaved(this.entrySaved, playerId);
		} catch (caught) {
			pushErrorToast(caught);
		}
	}

	async #persistTier(tierId: string): Promise<void> {
		const tier = this.index?.tierById.get(tierId);
		const name = tier?.name.trim();
		if (!this.strategy || !tier || !name) return;
		try {
			await updateTier(this.strategy.id, tierId, name, tier.color);
			this.#flashSaved(this.tierSaved, tierId);
		} catch (caught) {
			pushErrorToast(caught);
		}
	}

	#flashSaved(flags: Record<string, boolean>, id: string): void {
		flags[id] = true;
		setTimeout(() => {
			flags[id] = false;
		}, 1200);
	}

	#applyStrategy(strategy: Strategy): void {
		this.strategy = strategy;
		this.strategyName = strategy.name;
		const index = this.index;
		this.entryDrafts = Object.fromEntries(
			this.players.map((player) => {
				const entry = index?.entryByPlayerId.get(player.id);
				return [
					player.id,
					{
						tierId: entry?.tier_id ?? '',
						note: entry?.note ?? '',
						maximumPricePercentage: entry?.maximum_price_percentage ?? undefined
					}
				];
			})
		);
		this.orderedTiers = index?.sortedTiers ?? [];
	}

	async #runMutation(mutation: () => Promise<void>): Promise<void> {
		this.saving = true;
		try {
			await mutation();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			this.saving = false;
		}
	}
}
