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
import { PlayerSelection } from './playerSelection.svelte';

type EntryDraft = {
	tierId: string;
	note: string;
	maximumPricePercentage: number | undefined;
};

// Every field saves itself shortly after the user stops changing it.
const ENTRY_SAVE_DEBOUNCE_MS = 500;
const TIER_SAVE_DEBOUNCE_MS = 400;

/**
 * Delays the save of each id until its changes settle, and saves an id again only after its
 * running save, or the older request could land last. `persist` must handle its own errors.
 */
class DebouncedSaver {
	readonly #timers = new Map<string, ReturnType<typeof setTimeout>>();
	readonly #running = new Map<string, Promise<void>>();
	/** The ids to save again after their running save. */
	readonly #changed = new Set<string>();
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

	saveNow(id: string): Promise<void> {
		clearTimeout(this.#timers.get(id));
		this.#timers.delete(id);
		const running = this.#running.get(id);
		if (running) {
			this.#changed.add(id);
			return running;
		}
		const save = this.#save(id);
		this.#running.set(id, save);
		return save;
	}

	async flushAll(): Promise<void> {
		for (const id of [...this.#timers.keys()]) void this.saveNow(id);
		await Promise.all(this.#running.values());
	}

	/** Starts every save synchronously: an unloading page cannot wait for the running ones. */
	flushOnUnload(): void {
		const ids = new Set([...this.#timers.keys(), ...this.#changed]);
		for (const timer of this.#timers.values()) clearTimeout(timer);
		this.#timers.clear();
		this.#changed.clear();
		for (const id of ids) void this.#persist(id);
	}

	async #save(id: string): Promise<void> {
		do {
			this.#changed.delete(id);
			await this.#persist(id);
		} while (this.#changed.has(id));
		this.#running.delete(id);
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
	/** The last move of players, for screen readers. */
	lastMove = $state('');
	index = $derived(this.strategy && strategyIndex(this.strategy));

	readonly selection = new PlayerSelection();
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

	/** The players of a role in a tier, and the ones that `isLanding` there, in order. */
	playersInTier(tierId: string, role: Role, isLanding: (playerId: string) => boolean): Player[] {
		return this.players
			.filter(
				(player) =>
					player.role === role &&
					(this.entryDrafts[player.id]?.tierId === tierId || isLanding(player.id))
			)
			.sort(byMaxPercentageDesc(({ id }) => this.entryDrafts[id].maximumPricePercentage));
	}

	/** Moves players to a tier, or out of theirs with an empty `tierId`. */
	movePlayers(playerIds: Iterable<string>, tierId: string): void {
		const movedIds = [...playerIds].filter((id) => this.entryDrafts[id].tierId !== tierId);
		if (movedIds.length === 0) return;
		for (const id of movedIds) {
			this.entryDrafts[id].tierId = tierId;
			void this.saveEntryNow(id);
		}
		this.selection.clear();
		const moved =
			movedIds.length === 1
				? this.players.find((player) => player.id === movedIds[0])?.name
				: `${movedIds.length} calciatori`;
		this.lastMove = `${moved}: ${this.index?.tierById.get(tierId)?.name ?? 'senza fascia'}`;
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

	/** As `flushAll`, for a page that is reloading or closing. */
	flushOnUnload(): void {
		this.#entrySaves.flushOnUnload();
		this.#tierSaves.flushOnUnload();
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
