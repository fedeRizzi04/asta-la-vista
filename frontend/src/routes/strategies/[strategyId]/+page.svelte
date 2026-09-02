<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onDestroy, onMount } from 'svelte';
	import { SvelteMap } from 'svelte/reactivity';
	import CollapsibleSection from '$lib/components/CollapsibleSection.svelte';
	import HorizontalScroller from '$lib/components/HorizontalScroller.svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import SectionHeading from '$lib/components/SectionHeading.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import TierPlayerCard from '$lib/components/TierPlayerCard.svelte';
	import { confirmDialog } from '$lib/dialog.svelte';
	import { press } from '$lib/actions/press';
	import { dragReorder } from '$lib/actions/dragReorder';
	import { slidingIndicator } from '$lib/actions/slidingIndicator.svelte';
	import { getPlayers, type Player, type Role } from '$lib/players';
	import { matchesSearch } from '$lib/search';
	import { pushErrorToast } from '$lib/toast.svelte';
	import {
		addTier,
		byMaxPercentageDesc,
		getStrategy,
		removeTier,
		renameStrategy,
		reorderTiers,
		updateStrategyEntry,
		updateTier,
		type Strategy,
		type Tier
	} from '$lib/strategies';

	type EntryDraft = {
		tierId: string;
		note: string;
		maximumPricePercentage: number | undefined;
	};

	/** A player row paired with its current (possibly unsaved-for-a-moment) draft, for the tier board. */
	type BoardEntry = { player: Player; draft: EntryDraft };

	const roleLabels: Record<Role, string> = {
		P: 'Portieri',
		D: 'Difensori',
		C: 'Centrocampisti',
		A: 'Attaccanti'
	};
	const roles = Object.keys(roleLabels) as Role[];

	// Every field autosaves shortly after the user stops changing it (see §Response/§Direct
	// manipulation in apple-design): no "Salva" button, no page-wide lock while one field settles.
	const ENTRY_SAVE_DEBOUNCE_MS = 500;
	const TIER_SAVE_DEBOUNCE_MS = 400;

	let strategy = $state<Strategy>();
	let players = $state<Player[]>([]);
	let strategyName = $state('');
	let selectedRole = $state<Role>('P');
	let playerSearch = $state('');
	let newTierName = $state('');
	let newTierColor = $state('#d8ded9');
	let entryDrafts = $state<Record<string, EntryDraft>>({});
	let entrySaved = $state<Record<string, boolean>>({});
	let tierSaved = $state<Record<string, boolean>>({});
	let loading = $state(true);
	let saving = $state(false);
	let orderedTiers = $state<Tier[]>([]);
	let roleTabsEl = $state<HTMLElement>();
	let activeRoleTabEl = $state<HTMLElement>();

	const pendingEntrySaves = new SvelteMap<string, ReturnType<typeof setTimeout>>();
	const pendingTierSaves = new SvelteMap<string, ReturnType<typeof setTimeout>>();

	let visiblePlayers = $derived(
		players.filter(
			(player) =>
				player.role === selectedRole && matchesSearch(playerSearch, player.name, player.team)
		)
	);

	function entriesForTier(tierId: string): BoardEntry[] {
		return players
			.filter((player) => player.role === selectedRole && entryDrafts[player.id]?.tierId === tierId)
			.map((player) => ({ player, draft: entryDrafts[player.id] }))
			.sort(byMaxPercentageDesc((entry) => entry.draft.maximumPricePercentage));
	}

	onMount(loadData);

	async function loadData(): Promise<void> {
		loading = true;
		try {
			[strategy, players] = await Promise.all([
				getStrategy(currentStrategyId()),
				getPlayers({ includeInactive: true })
			]);
			strategyName = strategy.name;
			buildEntryDrafts();
			syncOrderedTiers();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		// Re-measure whenever the selected role changes, so the indicator glides across.
		void selectedRole;
		activeRoleTabEl = roleTabsEl?.querySelector<HTMLElement>('button.active') ?? undefined;
	});

	function buildEntryDrafts(): void {
		const entries = new Map(strategy?.entries.map((entry) => [entry.player_id, entry]));
		entryDrafts = Object.fromEntries(
			players.map((player) => {
				const entry = entries.get(player.id);
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
	}

	async function submitName(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		const name = strategyName.trim();
		const currentStrategy = strategy;
		if (!currentStrategy || !name) return;
		await runMutation(async () => {
			await renameStrategy(currentStrategy.id, name);
			currentStrategy.name = name;
		});
	}

	async function submitTier(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		const name = newTierName.trim();
		if (!strategy || !name) return;
		await runMutation(async () => {
			await flushAllPending();
			await addTier(strategy!.id, name, newTierColor);
			newTierName = '';
			await refreshStrategy();
		});
	}

	async function deleteTier(tier: Tier): Promise<void> {
		if (!strategy) return;
		const confirmed = await confirmDialog({
			title: 'Elimina fascia',
			message: `Eliminare la fascia “${tier.name}”?`,
			confirmLabel: 'Elimina',
			danger: true
		});
		if (!confirmed) return;
		await runMutation(async () => {
			await flushAllPending();
			await removeTier(strategy!.id, tier.id);
			await refreshStrategy();
		});
	}

	/** Called once by the drag/keyboard reorder gesture, with the final tier order. */
	async function commitTierOrder(nextIds: string[]): Promise<void> {
		if (!strategy) return;
		const byId = new Map(orderedTiers.map((tier) => [tier.id, tier]));
		orderedTiers = nextIds.map((id) => byId.get(id)).filter((tier) => tier !== undefined);
		await runMutation(() => reorderTiers(strategy!.id, nextIds));
	}

	/**
	 * Schedules an autosave for a player's tier/note/max-price draft. A tier pick is a discrete,
	 * deliberate choice and saves right away; free-text fields debounce so we don't fire a
	 * request per keystroke.
	 */
	function scheduleEntrySave(playerId: string, options: { immediate?: boolean } = {}): void {
		const pending = pendingEntrySaves.get(playerId);
		if (pending) clearTimeout(pending);
		if (options.immediate) {
			pendingEntrySaves.delete(playerId);
			void persistEntry(playerId);
			return;
		}
		pendingEntrySaves.set(
			playerId,
			setTimeout(() => {
				pendingEntrySaves.delete(playerId);
				void persistEntry(playerId);
			}, ENTRY_SAVE_DEBOUNCE_MS)
		);
	}

	/** Saves immediately if an autosave is pending (e.g. on blur), otherwise a no-op. */
	function flushEntrySave(playerId: string): Promise<void> {
		const pending = pendingEntrySaves.get(playerId);
		if (!pending) return Promise.resolve();
		clearTimeout(pending);
		pendingEntrySaves.delete(playerId);
		return persistEntry(playerId);
	}

	async function persistEntry(playerId: string): Promise<void> {
		const draft = entryDrafts[playerId];
		if (!strategy || !draft) return;
		try {
			await updateStrategyEntry(
				strategy.id,
				playerId,
				draft.tierId || null,
				draft.note,
				draft.maximumPricePercentage ?? null
			);
			flashSaved(entrySaved, playerId);
		} catch (caught) {
			pushErrorToast(caught);
		}
	}

	/** Same autosave shape as entries: debounced text/color, flushed on blur/change. */
	function scheduleTierSave(tierId: string): void {
		const pending = pendingTierSaves.get(tierId);
		if (pending) clearTimeout(pending);
		pendingTierSaves.set(
			tierId,
			setTimeout(() => {
				pendingTierSaves.delete(tierId);
				void persistTier(tierId);
			}, TIER_SAVE_DEBOUNCE_MS)
		);
	}

	function flushTierSave(tierId: string): Promise<void> {
		const pending = pendingTierSaves.get(tierId);
		if (!pending) return Promise.resolve();
		clearTimeout(pending);
		pendingTierSaves.delete(tierId);
		return persistTier(tierId);
	}

	async function persistTier(tierId: string): Promise<void> {
		const tier = orderedTiers.find((candidate) => candidate.id === tierId);
		if (!strategy || !tier || !tier.name.trim()) return;
		try {
			await updateTier(strategy.id, tier.id, tier.name.trim(), tier.color);
			flashSaved(tierSaved, tierId);
		} catch (caught) {
			pushErrorToast(caught);
		}
	}

	function flashSaved(flags: Record<string, boolean>, id: string): void {
		flags[id] = true;
		setTimeout(() => {
			flags[id] = false;
		}, 1200);
	}

	/** Persists any autosave still waiting on its debounce, before a full re-fetch overwrites local state. */
	async function flushAllPending(): Promise<void> {
		await Promise.all([
			...[...pendingEntrySaves.keys()].map(flushEntrySave),
			...[...pendingTierSaves.keys()].map(flushTierSave)
		]);
	}

	onDestroy(() => {
		for (const playerId of pendingEntrySaves.keys()) void flushEntrySave(playerId);
		for (const tierId of pendingTierSaves.keys()) void flushTierSave(tierId);
	});

	async function refreshStrategy(): Promise<void> {
		strategy = await getStrategy(currentStrategyId());
		strategyName = strategy.name;
		buildEntryDrafts();
		syncOrderedTiers();
	}

	function syncOrderedTiers(): void {
		orderedTiers = [...(strategy?.tiers ?? [])].sort(
			(first, second) => first.position - second.position
		);
	}

	function currentStrategyId(): string {
		const strategyId = page.params.strategyId;
		if (!strategyId) throw new Error('Strategia non trovata.');
		return strategyId;
	}

	async function runMutation(mutation: () => Promise<void>): Promise<void> {
		saving = true;
		try {
			await mutation();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>{strategy?.name ?? 'Strategia'} | Asta la Vista</title>
</svelte:head>

<a class="back-link" href={resolve('/strategies')}>Torna alle strategie</a>

<section class="detail-heading">
	<div>
		<p class="eyebrow">Modifica strategia</p>
		<h1>{strategy?.name ?? 'Strategia'}</h1>
	</div>
	<form onsubmit={submitName}>
		<label for="strategy-name">Nome</label>
		<div class="inline-fields">
			<input id="strategy-name" bind:value={strategyName} />
			<button type="submit" use:press disabled={!strategyName.trim() || saving}>Salva</button>
		</div>
	</form>
</section>

{#if loading}
	<div class="empty-state">Caricamento della strategia…</div>
{:else if strategy}
	<section class="panel">
		<CollapsibleSection
			storageKey={`strategy:${strategy.id}:global-tiers`}
			title="Fasce globali"
			subtitle="La stessa sequenza viene utilizzata per tutti i ruoli."
		>
			{#snippet trailing()}
				<form class="tier-form" onsubmit={submitTier}>
					<input
						bind:value={newTierName}
						placeholder="Nome fascia"
						aria-label="Nome nuova fascia"
					/>
					<input bind:value={newTierColor} type="color" aria-label="Colore nuova fascia" />
					<button type="submit" use:press disabled={!newTierName.trim() || saving}>Aggiungi</button>
				</form>
			{/snippet}

			{#if orderedTiers.length === 0}
				<div class="compact-empty">Non hai ancora creato nessuna fascia.</div>
			{:else}
				<div
					class="tier-list"
					use:dragReorder={{
						ids: () => orderedTiers.map((tier) => tier.id),
						onCommit: commitTierOrder,
						disabled: () => saving
					}}
				>
					{#each orderedTiers as tier (tier.id)}
						<div
							class="tier-row"
							data-drag-id={tier.id}
							style:--tier-color={tier.color ?? 'var(--tier-default)'}
						>
							<button
								type="button"
								class="drag-handle"
								data-drag-handle
								use:press
								aria-label={`Trascina per riordinare “${tier.name}”, o usa le frecce su/giù`}
							>
								⠿
							</button>
							<span class="color-marker"></span>
							<input
								bind:value={tier.name}
								oninput={() => scheduleTierSave(tier.id)}
								onblur={() => flushTierSave(tier.id)}
								aria-label="Nome fascia"
							/>
							<input
								type="color"
								value={tier.color ?? '#d8ded9'}
								oninput={(event) => {
									tier.color = event.currentTarget.value;
									scheduleTierSave(tier.id);
								}}
								onchange={() => flushTierSave(tier.id)}
								aria-label="Colore fascia"
							/>
							<div class="tier-actions">
								<span class="save-status" class:visible={tierSaved[tier.id]} role="status"
									>{tierSaved[tier.id] ? 'Salvato' : ''}</span
								>
								<button
									type="button"
									class="danger"
									use:press
									onclick={() => deleteTier(tier)}
									disabled={saving}>Elimina</button
								>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</CollapsibleSection>
	</section>

	<div class="role-tabs" role="tablist" aria-label="Ruoli" bind:this={roleTabsEl}>
		{#each roles as role (role)}
			<button
				type="button"
				class:active={selectedRole === role}
				use:press
				onclick={() => {
					selectedRole = role;
					playerSearch = '';
				}}
			>
				{roleLabels[role]}
			</button>
		{/each}
		<span class="tab-indicator" use:slidingIndicator={activeRoleTabEl} aria-hidden="true"></span>
	</div>

	<section class="panel role-tier-panel">
		<CollapsibleSection
			storageKey={`strategy:${strategy.id}:role-tiers`}
			title={`Fasce per ${roleLabels[selectedRole].toLowerCase()}`}
			subtitle="Vista raggruppata dei calciatori già assegnati."
		>
			{#if orderedTiers.length === 0}
				<div class="compact-empty">Crea almeno una fascia per organizzare i calciatori.</div>
			{:else}
				<HorizontalScroller ariaLabel={`Fasce per ${roleLabels[selectedRole].toLowerCase()}`}>
					<div class="tier-board">
						{#each orderedTiers as tier (tier.id)}
							<div class="tier-column" style:--tier-color={tier.color ?? 'var(--tier-default)'}>
								<h3><TierBadge name={tier.name} color={tier.color} /></h3>
								<div>
									{#each entriesForTier(tier.id) as entry (entry.player.id)}
										<TierPlayerCard
											name={entry.player.name}
											team={entry.player.team}
											mantraRoles={entry.player.mantra_roles}
											maximumPricePercentage={entry.draft.maximumPricePercentage ?? null}
											note={entry.draft.note}
											inactive={!entry.player.active}
										/>
									{:else}
										<p class="empty-tier">Nessun calciatore</p>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				</HorizontalScroller>
			{/if}
		</CollapsibleSection>
	</section>

	<section class="panel players-panel">
		<SectionHeading
			title="Calciatori"
			subtitle="Assegna una fascia, una percentuale massima di spesa e una nota facoltativa."
		>
			{#snippet trailing()}
				<input
					class="search"
					bind:value={playerSearch}
					type="search"
					placeholder="Cerca nome o squadra"
					aria-label="Cerca calciatori"
				/>
			{/snippet}
		</SectionHeading>

		{#if visiblePlayers.length === 0}
			<div class="compact-empty">Nessun calciatore disponibile per questo ruolo.</div>
		{:else}
			<div class="player-list">
				{#each visiblePlayers as player (player.id)}
					{@const selectedPlayerTier = orderedTiers.find(
						(tier) => tier.id === entryDrafts[player.id].tierId
					)}
					<div class:inactive={!player.active} class="player-row">
						<div class="player-info">
							<span class="name-row"
								><strong>{player.name}</strong><MantraRoleBadges
									roles={player.mantra_roles}
									compact
								/></span
							>
							<span>{player.team}{player.active ? '' : ' · inattivo'}</span>
						</div>
						<div class="tier-selector">
							<select
								bind:value={entryDrafts[player.id].tierId}
								style:--tier-color={selectedPlayerTier?.color ?? 'var(--tier-default)'}
								class:has-tier={!!selectedPlayerTier}
								aria-label={`Fascia di ${player.name}`}
								onchange={() => scheduleEntrySave(player.id, { immediate: true })}
							>
								<option value="">Senza fascia</option>
								{#each orderedTiers as tier (tier.id)}
									<option value={tier.id}>{tier.name}</option>
								{/each}
							</select>
						</div>
						<input
							bind:value={entryDrafts[player.id].note}
							placeholder="Nota"
							aria-label={`Nota per ${player.name}`}
							oninput={() => scheduleEntrySave(player.id)}
							onblur={() => flushEntrySave(player.id)}
						/>
						<div class="percentage-field">
							<input
								bind:value={entryDrafts[player.id].maximumPricePercentage}
								type="number"
								min="0.1"
								max="100"
								step="0.1"
								placeholder="% max"
								aria-label={`Percentuale massima per ${player.name}`}
								oninput={() => scheduleEntrySave(player.id)}
								onblur={() => flushEntrySave(player.id)}
							/>
							<span class="percentage-suffix">%</span>
						</div>
						<span class="save-status" class:visible={entrySaved[player.id]} role="status"
							>{entrySaved[player.id] ? 'Salvato' : ''}</span
						>
					</div>
				{/each}
			</div>
		{/if}
	</section>
{/if}

<style>
	.back-link {
		display: inline-block;
		margin-bottom: 1.5rem;
		color: var(--muted);
		font-size: 0.84rem;
		font-weight: 650;
	}

	.detail-heading {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 3rem;
	}

	.detail-heading h1 {
		margin: 0;
		font-size: clamp(2rem, 4vw, 3.5rem);
		letter-spacing: -0.045em;
	}

	.detail-heading form {
		width: min(100%, 390px);
	}

	label {
		display: block;
		margin-bottom: 0.4rem;
		font-size: 0.78rem;
		font-weight: 700;
	}

	.inline-fields,
	.tier-form,
	.tier-actions {
		display: flex;
		gap: 0.55rem;
	}

	input:not([type='color']),
	select {
		min-width: 0;
		height: 2.5rem;
		padding: 0 0.7rem;
		border: 1px solid var(--border-strong);
		border-radius: 0.4rem;
		background: var(--input-bg);
		color: inherit;
		font: inherit;
	}

	.inline-fields input {
		flex: 1;
	}

	input[type='color'] {
		width: 2.75rem;
		height: 2.5rem;
		padding: 0.2rem;
		border: 1px solid var(--border-strong);
		border-radius: 0.4rem;
		background: var(--input-bg);
	}

	button {
		min-height: 2.5rem;
		padding: 0 0.9rem;
		border: 1px solid var(--primary);
		border-radius: 0.42rem;
		background: var(--primary);
		color: var(--on-primary);
		font: inherit;
		font-size: 0.82rem;
		font-weight: 700;
		cursor: pointer;
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.45;
	}

	button.danger {
		border-color: transparent;
		background: transparent;
		color: var(--error-text);
	}

	/* Completion feedback (§Feedback comes in four kinds): every field autosaves on its own,
	   so instead of a "Salva" button we surface a quiet, transient confirmation next to the
	   field that just settled. `role="status"` announces it to assistive tech without a
	   dedicated live region per row; reduced motion already neutralises the pulse globally. */
	.save-status {
		min-width: 4.5rem;
		color: var(--success-text);
		font-size: 0.78rem;
		font-weight: 700;
		text-align: right;
		opacity: 0;
		transition: opacity 220ms ease;
	}

	.save-status.visible {
		opacity: 1;
		animation: save-pulse 320ms cubic-bezier(0.19, 1, 0.22, 1);
	}

	@keyframes save-pulse {
		0% {
			transform: scale(1);
		}
		40% {
			transform: scale(1.06);
		}
		100% {
			transform: scale(1);
		}
	}

	/* Pinned below the app header once the page scrolls past it (plain CSS sticky, no
	   scroll-listener bookkeeping), so the role you're editing stays reachable without
	   scrolling back up — the tier/player panels below all depend on it. */
	.role-tabs {
		position: sticky;
		top: var(--header-height, 4.5rem);
		z-index: 80;
		display: flex;
		gap: 0.4rem;
		margin-top: 1.75rem;
		padding-top: 0.5rem;
		background: var(--page-bg);
		border-bottom: 1px solid var(--border);
	}

	.role-tabs button {
		border: 0;
		border-radius: 0;
		background: transparent;
		color: var(--subdued);
	}

	.role-tabs button.active {
		color: var(--primary);
	}

	.panel {
		margin-top: 1.5rem;
	}

	.detail-heading + .panel {
		margin-top: 3rem;
	}

	.tier-form input:not([type='color']) {
		width: 190px;
	}

	.tier-list,
	.player-list {
		display: grid;
		gap: 0.55rem;
		margin-top: 1rem;
	}

	.tier-row {
		display: grid;
		grid-template-columns: auto 0.5rem minmax(180px, 1fr) auto auto;
		align-items: center;
		gap: 0.65rem;
		padding: 0.6rem;
		border: 1px solid var(--border);
		border-radius: 0.5rem;
		background: var(--input-bg);
		transition:
			box-shadow 180ms ease,
			border-color 180ms ease;
	}

	/* Direct manipulation feedback while held: lift off the list, follow the pointer 1:1.
	   `is-dragging` is toggled imperatively by the dragReorder action, not by Svelte's
	   `class:` directive, so it's marked :global to keep the compiler from tree-shaking it. */
	.tier-row:global(.is-dragging) {
		position: relative;
		z-index: 5;
		border-color: var(--border-hover);
		box-shadow: 0 18px 32px -12px rgb(0 0 0 / 30%);
		cursor: grabbing;
	}

	.drag-handle {
		display: grid;
		place-items: center;
		width: 2.1rem;
		min-height: 2.1rem;
		padding: 0;
		border-color: var(--border-strong);
		border-radius: 0.4rem;
		background: var(--input-bg);
		color: var(--subdued);
		font-size: 1rem;
		letter-spacing: 0;
		line-height: 1;
		cursor: grab;
		touch-action: none;
	}

	.drag-handle:active {
		cursor: grabbing;
	}

	.color-marker {
		align-self: stretch;
		border: 1px solid rgb(0 0 0 / 14%);
		border-radius: 0.24rem;
		background: var(--tier-color);
	}

	.compact-empty {
		margin-top: 1rem;
		padding: 1rem;
		border: 1px dashed var(--border-strong);
		border-radius: 0.5rem;
		color: var(--subdued);
		font-size: 0.85rem;
	}

	.role-tier-panel {
		background: var(--input-bg);
	}

	.tier-board {
		display: flex;
		align-items: stretch;
		gap: 0.75rem;
		width: max-content;
		min-width: 100%;
		margin-top: 1rem;
	}

	.tier-column {
		flex: 0 0 min(17.5rem, calc(100vw - 4rem));
		border: 1px solid var(--border);
		border-top: 0.35rem solid var(--tier-color);
		border-radius: 0.45rem;
		background: var(--surface);
	}

	.tier-column h3 {
		margin: 0;
		padding: 0.65rem 0.75rem;
		border-bottom: 1px solid var(--border);
	}

	.tier-column > div {
		display: grid;
		gap: 0.35rem;
		padding: 0.5rem;
	}

	.tier-column .empty-tier {
		margin: 0;
		padding: 0.45rem;
		color: var(--subdued);
		font-size: 0.72rem;
	}

	.players-panel {
		margin-top: 1rem;
	}

	.search {
		width: min(100%, 280px);
	}

	.player-row {
		display: grid;
		grid-template-columns:
			minmax(180px, 1fr) minmax(150px, 0.7fr) minmax(160px, 0.9fr) minmax(110px, 0.45fr)
			auto;
		align-items: center;
		gap: 0.65rem;
		padding: 0.65rem;
		border-bottom: 1px solid var(--border);
	}

	.player-row:last-child {
		border-bottom: 0;
	}

	.player-row.inactive {
		color: var(--disabled-text);
		background: var(--muted-bg);
	}

	.player-info {
		display: grid;
		gap: 0.2rem;
	}

	.player-info span {
		color: var(--subdued);
		font-size: 0.76rem;
	}

	.player-info .name-row {
		display: inline-flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.3rem;
		color: inherit;
		font-size: inherit;
	}

	.player-info .name-row strong {
		color: var(--text);
		font-size: 0.9rem;
	}

	.tier-selector {
		min-width: 0;
	}

	.tier-selector select {
		width: 100%;
	}

	.percentage-field {
		position: relative;
		min-width: 0;
	}

	.percentage-field input {
		width: 100%;
		padding-right: 1.6rem;
	}

	.percentage-suffix {
		position: absolute;
		top: 50%;
		right: 0.7rem;
		transform: translateY(-50%);
		color: var(--subdued);
		font-size: 0.8rem;
		pointer-events: none;
	}

	.tier-selector select.has-tier {
		border-left: 4px solid var(--tier-color);
	}

	@media (max-width: 900px) {
		.detail-heading {
			align-items: stretch;
			flex-direction: column;
		}

		.player-row {
			grid-template-columns: 0.35rem 1fr auto;
		}

		.tier-row {
			grid-template-columns: auto 0.35rem 1fr auto;
		}

		.tier-actions {
			grid-column: 3 / -1;
		}

		.player-row > input,
		.player-row > .tier-selector,
		.player-row > .percentage-field,
		.player-row > .save-status {
			grid-column: 2 / -1;
		}
	}

	@media (max-width: 560px) {
		.role-tabs {
			overflow-x: auto;
		}

		.tier-form,
		.tier-actions {
			flex-wrap: wrap;
		}

		.tier-form input:not([type='color']) {
			width: 100%;
		}
	}
</style>
