<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { getPlayers, type Player, type Role } from '$lib/players';
	import {
		addTier,
		getStrategy,
		removeTier,
		renameStrategy,
		reorderTiers,
		updateStrategyEntry,
		updateTier,
		type Strategy,
		type Tier
	} from '$lib/strategies';

	type EntryDraft = { tierId: string; note: string };

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
	let error = $state('');

	let roleTiers = $derived(
		(strategy?.tiers ?? [])
			.filter((tier) => tier.role === selectedRole)
			.sort((first, second) => first.position - second.position)
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

	onMount(loadData);

	async function loadData(): Promise<void> {
		loading = true;
		error = '';
		try {
			[strategy, players] = await Promise.all([
				getStrategy(currentStrategyId()),
				getPlayers({ includeInactive: true })
			]);
			strategyName = strategy.name;
			buildEntryDrafts();
		} catch (caught) {
			error = errorMessage(caught);
		} finally {
			loading = false;
		}
	}

	function buildEntryDrafts(): void {
		const entries = new Map(strategy?.entries.map((entry) => [entry.player_id, entry]));
		entryDrafts = Object.fromEntries(
			players.map((player) => {
				const entry = entries.get(player.id);
				return [player.id, { tierId: entry?.tier_id ?? '', note: entry?.note ?? '' }];
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
			await addTier(strategy!.id, selectedRole, name, newTierColor);
			newTierName = '';
			await refreshStrategy();
		});
	}

	async function saveTier(tier: Tier): Promise<void> {
		if (!strategy || !tier.name.trim()) return;
		await runMutation(() => updateTier(strategy!.id, tier.id, tier.name.trim(), tier.color));
	}

	async function deleteTier(tier: Tier): Promise<void> {
		if (!strategy || !window.confirm(`Eliminare la fascia “${tier.name}”?`)) return;
		await runMutation(async () => {
			await removeTier(strategy!.id, tier.id);
			await refreshStrategy();
		});
	}

	async function moveTier(tier: Tier, offset: number): Promise<void> {
		if (!strategy) return;
		const tierIds = roleTiers.map((item) => item.id);
		const currentIndex = tierIds.indexOf(tier.id);
		const targetIndex = currentIndex + offset;
		if (targetIndex < 0 || targetIndex >= tierIds.length) return;
		[tierIds[currentIndex], tierIds[targetIndex]] = [tierIds[targetIndex], tierIds[currentIndex]];
		await runMutation(async () => {
			await reorderTiers(strategy!.id, selectedRole, tierIds);
			await refreshStrategy();
		});
	}

	async function saveEntry(player: Player): Promise<void> {
		if (!strategy) return;
		const draft = entryDrafts[player.id];
		savedPlayerId = '';
		await runMutation(async () => {
			await updateStrategyEntry(strategy!.id, player.id, draft.tierId || null, draft.note);
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
		error = '';
		try {
			await mutation();
		} catch (caught) {
			error = errorMessage(caught);
		} finally {
			saving = false;
		}
	}

	function errorMessage(caught: unknown): string {
		return caught instanceof Error ? caught.message : 'Si è verificato un errore inatteso.';
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

{#if error}
	<div class="message" role="alert">{error}</div>
{/if}

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
		<div class="section-heading">
			<div>
				<h2>Fasce</h2>
				<p>Ordinale dalla priorità più alta a quella più bassa.</p>
			</div>
			<form class="tier-form" onsubmit={submitTier}>
				<input bind:value={newTierName} placeholder="Nome fascia" aria-label="Nome nuova fascia" />
				<input bind:value={newTierColor} type="color" aria-label="Colore nuova fascia" />
				<button type="submit" disabled={!newTierName.trim() || saving}>Aggiungi</button>
			</form>
		</div>

		{#if roleTiers.length === 0}
			<div class="compact-empty">Nessuna fascia per questo ruolo.</div>
		{:else}
			<div class="tier-list">
				{#each roleTiers as tier, index (tier.id)}
					<div class="tier-row" style:--tier-color={tier.color ?? '#d8ded9'}>
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
								disabled={index === roleTiers.length - 1 || saving}
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

	<section class="panel players-panel">
		<div class="section-heading">
			<div>
				<h2>Calciatori</h2>
				<p>Assegna una fascia e aggiungi una nota facoltativa.</p>
			</div>
			<input
				class="search"
				bind:value={playerSearch}
				type="search"
				placeholder="Cerca nome o squadra"
				aria-label="Cerca calciatori"
			/>
		</div>

		{#if visiblePlayers.length === 0}
			<div class="compact-empty">Nessun calciatore disponibile per questo ruolo.</div>
		{:else}
			<div class="player-list">
				{#each visiblePlayers as player (player.id)}
					<div class:inactive={!player.active} class="player-row">
						<div class="player-info">
							<strong>{player.name}</strong>
							<span>{player.team}{player.active ? '' : ' · inattivo'}</span>
						</div>
						<select
							bind:value={entryDrafts[player.id].tierId}
							aria-label={`Fascia di ${player.name}`}
						>
							<option value="">Senza fascia</option>
							{#each roleTiers as tier (tier.id)}
								<option value={tier.id}>{tier.name}</option>
							{/each}
						</select>
						<input
							bind:value={entryDrafts[player.id].note}
							placeholder="Nota"
							aria-label={`Nota per ${player.name}`}
						/>
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
		color: #526057;
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

	label,
	.section-heading p {
		font-size: 0.78rem;
	}

	label {
		display: block;
		margin-bottom: 0.4rem;
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
		border: 1px solid #bdc5bf;
		border-radius: 0.4rem;
		background: #fff;
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
		border: 1px solid #bdc5bf;
		border-radius: 0.4rem;
		background: #fff;
	}

	button {
		min-height: 2.5rem;
		padding: 0 0.9rem;
		border: 1px solid #204c39;
		border-radius: 0.42rem;
		background: #204c39;
		color: #fff;
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
		border-color: #bdc5bf;
		background: #fff;
		color: #344039;
	}

	button.danger {
		border-color: transparent;
		background: transparent;
		color: #8b3434;
	}

	button.icon {
		width: 2.5rem;
		padding: 0;
	}

	.message {
		margin-top: 1.5rem;
		padding: 0.85rem 1rem;
		border: 1px solid #d4a7a7;
		border-radius: 0.5rem;
		background: #fff7f7;
		color: #7a2727;
		font-size: 0.9rem;
	}

	.role-tabs {
		display: flex;
		gap: 0.4rem;
		margin-top: 3rem;
		border-bottom: 1px solid #d9ddd7;
	}

	.role-tabs button {
		border: 0;
		border-bottom: 2px solid transparent;
		border-radius: 0;
		background: transparent;
		color: #667069;
	}

	.role-tabs button.active {
		border-bottom-color: #204c39;
		color: #204c39;
	}

	.panel {
		margin-top: 1.5rem;
		padding: 1.25rem;
		border: 1px solid #d9ddd7;
		border-radius: 0.7rem;
		background: #fafbf8;
	}

	.section-heading {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 2rem;
	}

	.section-heading h2,
	.section-heading p {
		margin: 0;
	}

	.section-heading h2 {
		font-size: 1.1rem;
	}

	.section-heading p {
		margin-top: 0.3rem;
		color: #667069;
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
		grid-template-columns: 0.35rem minmax(180px, 1fr) auto auto;
		align-items: center;
		gap: 0.65rem;
		padding: 0.6rem;
		border: 1px solid #e0e3df;
		border-radius: 0.5rem;
		background: #fff;
	}

	.color-marker {
		align-self: stretch;
		border-radius: 0.2rem;
		background: var(--tier-color);
	}

	.compact-empty {
		margin-top: 1rem;
		padding: 1rem;
		border: 1px dashed #c8cec9;
		border-radius: 0.5rem;
		color: #667069;
		font-size: 0.85rem;
	}

	.players-panel {
		margin-top: 1rem;
	}

	.search {
		width: min(100%, 280px);
	}

	.player-row {
		display: grid;
		grid-template-columns: minmax(180px, 1fr) minmax(150px, 0.7fr) minmax(180px, 1fr) auto;
		align-items: center;
		gap: 0.65rem;
		padding: 0.65rem;
		border-bottom: 1px solid #e0e3df;
	}

	.player-row:last-child {
		border-bottom: 0;
	}

	.player-row.inactive {
		color: #929893;
		background: #f0f1ef;
	}

	.player-info {
		display: grid;
		gap: 0.2rem;
	}

	.player-info span {
		color: #707971;
		font-size: 0.76rem;
	}

	@media (max-width: 900px) {
		.detail-heading,
		.section-heading {
			align-items: stretch;
			flex-direction: column;
		}

		.tier-row,
		.player-row {
			grid-template-columns: 0.35rem 1fr auto;
		}

		.tier-actions,
		.player-row > input,
		.player-row > select,
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
