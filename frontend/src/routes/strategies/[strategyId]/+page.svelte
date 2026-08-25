<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import SectionHeading from '$lib/components/SectionHeading.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import TierPlayerCard from '$lib/components/TierPlayerCard.svelte';
	import { confirmDialog } from '$lib/dialog.svelte';
	import { getPlayers, type Player, type Role } from '$lib/players';
	import { pushErrorToast } from '$lib/toast.svelte';
	import {
		addTier,
		getStrategy,
		removeTier,
		renameStrategy,
		reorderTiers,
		updateStrategyEntry,
		updateTier,
		type Strategy,
		type StrategyEntry,
		type Tier
	} from '$lib/strategies';

	type EntryDraft = {
		tierId: string;
		note: string;
		maximumPricePercentage: number | undefined;
	};

	const roleLabels: Record<Role, string> = {
		P: 'Portieri',
		D: 'Difensori',
		C: 'Centrocampisti',
		A: 'Attaccanti'
	};
	const roles = Object.keys(roleLabels) as Role[];

	let strategy = $state<Strategy>();
	let players = $state<Player[]>([]);
	let strategyName = $state('');
	let selectedRole = $state<Role>('P');
	let playerSearch = $state('');
	let newTierName = $state('');
	let newTierColor = $state('#d8ded9');
	let entryDrafts = $state<Record<string, EntryDraft>>({});
	let loading = $state(true);
	let saving = $state(false);
	let savedPlayerId = $state('');

	let orderedTiers = $derived(
		[...(strategy?.tiers ?? [])].sort((first, second) => first.position - second.position)
	);
	let visiblePlayers = $derived(
		players.filter(
			(player) =>
				player.role === selectedRole &&
				(!playerSearch.trim() ||
					player.name.toLowerCase().includes(playerSearch.trim().toLowerCase()) ||
					player.team.toLowerCase().includes(playerSearch.trim().toLowerCase()))
		)
	);

	function entriesForTier(tierId: string): StrategyEntry[] {
		return (strategy?.entries ?? [])
			.filter((entry) => entry.role === selectedRole && entry.tier_id === tierId)
			.sort(
				(first, second) =>
					(second.maximum_price_percentage ?? -1) - (first.maximum_price_percentage ?? -1)
			);
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
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			loading = false;
		}
	}

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
			await addTier(strategy!.id, name, newTierColor);
			newTierName = '';
			await refreshStrategy();
		});
	}

	async function saveTier(tier: Tier): Promise<void> {
		if (!strategy || !tier.name.trim()) return;
		await runMutation(() => updateTier(strategy!.id, tier.id, tier.name.trim(), tier.color));
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
			await removeTier(strategy!.id, tier.id);
			await refreshStrategy();
		});
	}

	async function moveTier(tier: Tier, offset: number): Promise<void> {
		if (!strategy) return;
		const tierIds = orderedTiers.map((item) => item.id);
		const currentIndex = tierIds.indexOf(tier.id);
		const targetIndex = currentIndex + offset;
		if (targetIndex < 0 || targetIndex >= tierIds.length) return;
		[tierIds[currentIndex], tierIds[targetIndex]] = [tierIds[targetIndex], tierIds[currentIndex]];
		await runMutation(async () => {
			await reorderTiers(strategy!.id, tierIds);
			await refreshStrategy();
		});
	}

	async function saveEntry(player: Player): Promise<void> {
		if (!strategy) return;
		const draft = entryDrafts[player.id];
		savedPlayerId = '';
		await runMutation(async () => {
			await updateStrategyEntry(
				strategy!.id,
				player.id,
				draft.tierId || null,
				draft.note,
				draft.tierId ? (draft.maximumPricePercentage ?? null) : null
			);
			await refreshStrategy();
			savedPlayerId = player.id;
		});
	}

	async function refreshStrategy(): Promise<void> {
		strategy = await getStrategy(currentStrategyId());
		strategyName = strategy.name;
		buildEntryDrafts();
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
			<button type="submit" disabled={!strategyName.trim() || saving}>Salva</button>
		</div>
	</form>
</section>

{#if loading}
	<div class="empty-state">Caricamento della strategia…</div>
{:else if strategy}
	<div class="role-tabs" role="tablist" aria-label="Ruoli">
		{#each roles as role (role)}
			<button
				type="button"
				class:active={selectedRole === role}
				onclick={() => {
					selectedRole = role;
					playerSearch = '';
					savedPlayerId = '';
				}}
			>
				{roleLabels[role]}
			</button>
		{/each}
	</div>

	<section class="panel">
		<SectionHeading
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
					<button type="submit" disabled={!newTierName.trim() || saving}>Aggiungi</button>
				</form>
			{/snippet}
		</SectionHeading>

		{#if orderedTiers.length === 0}
			<div class="compact-empty">Non hai ancora creato nessuna fascia.</div>
		{:else}
			<div class="tier-list">
				{#each orderedTiers as tier, index (tier.id)}
					<div class="tier-row" style:--tier-color={tier.color ?? 'var(--tier-default)'}>
						<span class="color-marker"></span>
						<input bind:value={tier.name} aria-label="Nome fascia" />
						<input
							type="color"
							value={tier.color ?? '#d8ded9'}
							oninput={(event) => (tier.color = event.currentTarget.value)}
							aria-label="Colore fascia"
						/>
						<div class="tier-actions">
							<button
								type="button"
								class="icon"
								onclick={() => moveTier(tier, -1)}
								disabled={index === 0 || saving}
								aria-label="Sposta in alto">↑</button
							>
							<button
								type="button"
								class="icon"
								onclick={() => moveTier(tier, 1)}
								disabled={index === orderedTiers.length - 1 || saving}
								aria-label="Sposta in basso">↓</button
							>
							<button
								type="button"
								class="secondary"
								onclick={() => saveTier(tier)}
								disabled={saving}>Salva</button
							>
							<button
								type="button"
								class="danger"
								onclick={() => deleteTier(tier)}
								disabled={saving}>Elimina</button
							>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</section>

	<section class="panel role-tier-panel">
		<SectionHeading
			title={`Fasce per ${roleLabels[selectedRole].toLowerCase()}`}
			subtitle="Vista raggruppata dei calciatori già assegnati."
		/>
		{#if orderedTiers.length === 0}
			<div class="compact-empty">Crea almeno una fascia per organizzare i calciatori.</div>
		{:else}
			<div class="tier-board">
				{#each orderedTiers as tier (tier.id)}
					<div class="tier-column" style:--tier-color={tier.color ?? 'var(--tier-default)'}>
						<h3><TierBadge name={tier.name} color={tier.color} /></h3>
						<div>
							{#each entriesForTier(tier.id) as entry (entry.player_id)}
								<TierPlayerCard
									name={entry.name}
									team={entry.team}
									mantraRoles={entry.mantra_roles}
									maximumPricePercentage={entry.maximum_price_percentage}
									note={entry.note}
									inactive={!entry.active}
								/>
							{:else}
								<p class="empty-tier">Nessun calciatore</p>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		{/if}
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
								onchange={() => {
									if (!entryDrafts[player.id].tierId) {
										entryDrafts[player.id].maximumPricePercentage = undefined;
									}
								}}
								aria-label={`Fascia di ${player.name}`}
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
								disabled={!entryDrafts[player.id].tierId}
							/>
							<span class="percentage-suffix">%</span>
						</div>
						<button
							type="button"
							class="secondary"
							onclick={() => saveEntry(player)}
							disabled={saving}
						>
							{savedPlayerId === player.id ? 'Salvato' : 'Salva'}
						</button>
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

	button.secondary,
	button.icon {
		border-color: var(--border-strong);
		background: var(--input-bg);
		color: var(--text);
	}

	button.danger {
		border-color: transparent;
		background: transparent;
		color: var(--error-text);
	}

	button.icon {
		width: 2.5rem;
		padding: 0;
	}

	.role-tabs {
		display: flex;
		gap: 0.4rem;
		margin-top: 3rem;
		border-bottom: 1px solid var(--border);
	}

	.role-tabs button {
		border: 0;
		border-bottom: 2px solid transparent;
		border-radius: 0;
		background: transparent;
		color: var(--subdued);
	}

	.role-tabs button.active {
		border-bottom-color: var(--primary);
		color: var(--primary);
	}

	.panel {
		margin-top: 1.5rem;
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
		grid-template-columns: 0.5rem minmax(180px, 1fr) auto auto;
		align-items: center;
		gap: 0.65rem;
		padding: 0.6rem;
		border: 1px solid var(--border);
		border-radius: 0.5rem;
		background: var(--input-bg);
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
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.tier-column {
		min-width: 0;
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

		.tier-row,
		.player-row {
			grid-template-columns: 0.35rem 1fr auto;
		}

		.tier-actions,
		.player-row > input,
		.player-row > .tier-selector,
		.player-row > .percentage-field,
		.player-row > button {
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
