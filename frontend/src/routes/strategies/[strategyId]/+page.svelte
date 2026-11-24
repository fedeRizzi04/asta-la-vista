<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onDestroy, onMount } from 'svelte';
	import { dragReorder } from '$lib/actions/dragReorder';
	import CollapsibleSection from '$lib/components/CollapsibleSection.svelte';
	import HorizontalScroller from '$lib/components/HorizontalScroller.svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import SectionHeading from '$lib/components/SectionHeading.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import TierPlayerCard from '$lib/components/TierPlayerCard.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import Tabs from '$lib/components/ui/Tabs.svelte';
	import { StrategyEditor } from '$lib/features/strategy/strategyEditor.svelte';
	import { roleLabels, roles, type Role } from '$lib/players';
	import { matchesSearch } from '$lib/search';

	const editor = new StrategyEditor(() => page.params.strategyId);
	const strategy = $derived(editor.strategy);
	const roleTabs = roles.map((role) => ({ value: role, label: roleLabels[role] }));

	let selectedRole = $state<Role>('P');
	let playerSearch = $state('');
	let newTierName = $state('');
	let newTierColor = $state('#d8ded9');

	const visiblePlayers = $derived(
		editor.players.filter(
			(player) =>
				player.role === selectedRole && matchesSearch(playerSearch, player.name, player.team)
		)
	);

	function submitName(event: SubmitEvent): void {
		event.preventDefault();
		void editor.rename();
	}

	async function submitTier(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (await editor.addTier(newTierName, newTierColor)) newTierName = '';
	}

	onMount(() => editor.load());
	onDestroy(() => void editor.flushAll());
</script>

<!-- A reload or a closed window does not destroy the component. -->
<svelte:window onpagehide={() => void editor.flushAll()} />

<svelte:head>
	<title>{strategy?.name ?? 'Strategia'} | Asta la Vista</title>
</svelte:head>

<PageHeader
	title={strategy?.name ?? 'Strategia'}
	back={{ href: resolve('/strategies'), label: 'Strategie' }}
>
	{#snippet actions()}
		<form class="name-form" onsubmit={submitName}>
			<Field label="Nome" inline>
				<Input bind:value={editor.strategyName} />
			</Field>
			<Button type="submit" disabled={!editor.strategyName.trim() || editor.saving}>Salva</Button>
		</form>
	{/snippet}
</PageHeader>

{#if editor.loading}
	<EmptyState>Caricamento della strategia…</EmptyState>
{:else if strategy}
	<section class="panel">
		<CollapsibleSection
			storageKey={`strategy:${strategy.id}:global-tiers`}
			title="Fasce globali"
			subtitle="La stessa sequenza viene utilizzata per tutti i ruoli."
		>
			{#snippet trailing()}
				<form class="tier-form" onsubmit={submitTier}>
					<Input
						class="tier-name"
						bind:value={newTierName}
						placeholder="Nome fascia"
						aria-label="Nome nuova fascia"
					/>
					<Input bind:value={newTierColor} type="color" aria-label="Colore nuova fascia" />
					<Button type="submit" disabled={!newTierName.trim() || editor.saving}>Aggiungi</Button>
				</form>
			{/snippet}

			{#if editor.orderedTiers.length === 0}
				<EmptyState compact>Non hai ancora creato nessuna fascia.</EmptyState>
			{:else}
				<div
					class="tier-list"
					use:dragReorder={{
						ids: () => editor.orderedTiers.map((tier) => tier.id),
						onCommit: (ids) => editor.commitTierOrder(ids),
						disabled: () => editor.saving
					}}
				>
					{#each editor.orderedTiers as tier (tier.id)}
						<div
							class="tier-row"
							data-drag-id={tier.id}
							style:--tier-color={tier.color ?? 'var(--tier-default)'}
						>
							<Button
								variant="secondary"
								class="drag-handle"
								data-drag-handle
								aria-label={`Trascina per riordinare “${tier.name}”, o usa le frecce su/giù`}
							>
								⠿
							</Button>
							<span class="color-marker"></span>
							<Input
								bind:value={tier.name}
								oninput={() => editor.scheduleTierSave(tier.id)}
								onblur={() => editor.flushTierSave(tier.id)}
								aria-label="Nome fascia"
							/>
							<Input
								type="color"
								value={tier.color ?? '#d8ded9'}
								oninput={(event) => {
									tier.color = event.currentTarget.value;
									editor.scheduleTierSave(tier.id);
								}}
								onchange={() => editor.flushTierSave(tier.id)}
								aria-label="Colore fascia"
							/>
							<div class="tier-actions">
								<span class="save-status" class:visible={editor.tierSaved[tier.id]} role="status"
									>{editor.tierSaved[tier.id] ? 'Salvato' : ''}</span
								>
								<Button
									variant="danger"
									onclick={() => editor.deleteTier(tier)}
									disabled={editor.saving}
								>
									Elimina
								</Button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</CollapsibleSection>
	</section>

	<div class="role-tabs">
		<Tabs
			items={roleTabs}
			bind:value={selectedRole}
			label="Ruoli"
			id="strategy-role"
			panelId="strategy-role-panel"
			onchange={() => (playerSearch = '')}
		/>
	</div>

	<div
		id="strategy-role-panel"
		role="tabpanel"
		tabindex="0"
		aria-labelledby="strategy-role-{selectedRole}"
	>
		<section class="panel role-tier-panel">
			<CollapsibleSection
				storageKey={`strategy:${strategy.id}:role-tiers`}
				title={`Fasce per ${roleLabels[selectedRole].toLowerCase()}`}
				subtitle="Vista raggruppata dei calciatori già assegnati."
			>
				{#if editor.orderedTiers.length === 0}
					<EmptyState compact>Crea almeno una fascia per organizzare i calciatori.</EmptyState>
				{:else}
					<HorizontalScroller ariaLabel={`Fasce per ${roleLabels[selectedRole].toLowerCase()}`}>
						<div class="tier-board">
							{#each editor.orderedTiers as tier (tier.id)}
								<div class="tier-column" style:--tier-color={tier.color ?? 'var(--tier-default)'}>
									<h3><TierBadge name={tier.name} color={tier.color} /></h3>
									<div>
										{#each editor.entriesForTier(tier.id, selectedRole) as entry (entry.player.id)}
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
					<Input
						class="search"
						bind:value={playerSearch}
						type="search"
						placeholder="Cerca nome o squadra"
						aria-label="Cerca calciatori"
					/>
				{/snippet}
			</SectionHeading>

			{#if visiblePlayers.length === 0}
				<EmptyState compact>Nessun calciatore disponibile per questo ruolo.</EmptyState>
			{:else}
				<div class="player-list">
					{#each visiblePlayers as player (player.id)}
						{@const selectedPlayerTier = editor.index?.tierById.get(
							editor.entryDrafts[player.id].tierId
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
								<Select
									bind:value={editor.entryDrafts[player.id].tierId}
									style="--tier-color: {selectedPlayerTier?.color ?? 'var(--tier-default)'}"
									class={selectedPlayerTier ? 'has-tier' : ''}
									aria-label={`Fascia di ${player.name}`}
									onchange={() => editor.saveEntryNow(player.id)}
								>
									<option value="">Senza fascia</option>
									{#each editor.orderedTiers as tier (tier.id)}
										<option value={tier.id}>{tier.name}</option>
									{/each}
								</Select>
							</div>
							<Input
								bind:value={editor.entryDrafts[player.id].note}
								placeholder="Nota"
								aria-label={`Nota per ${player.name}`}
								oninput={() => editor.scheduleEntrySave(player.id)}
								onblur={() => editor.flushEntrySave(player.id)}
							/>
							<div class="percentage-field">
								<Input
									bind:value={editor.entryDrafts[player.id].maximumPricePercentage}
									type="number"
									min="0.1"
									max="100"
									step="0.1"
									placeholder="% max"
									aria-label={`Percentuale massima per ${player.name}`}
									oninput={() => editor.scheduleEntrySave(player.id)}
									onblur={() => editor.flushEntrySave(player.id)}
								/>
								<span class="percentage-suffix">%</span>
							</div>
							<span class="save-status" class:visible={editor.entrySaved[player.id]} role="status"
								>{editor.entrySaved[player.id] ? 'Salvato' : ''}</span
							>
						</div>
					{/each}
				</div>
			{/if}
		</section>
	</div>
{/if}

<style>
	.name-form,
	.tier-form,
	.tier-actions {
		display: flex;
		align-items: center;
		gap: 0.55rem;
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
		top: var(--header-height);
		z-index: 80;
		margin-top: 1.5rem;
		padding: 0.5rem 0 0.4rem;
		background: var(--page-bg);
		border-bottom: 1px solid var(--border);
	}

	.panel {
		margin-top: 1.5rem;
	}

	.tier-form :global(.tier-name) {
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
		border-radius: var(--radius-sm);
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
		box-shadow: var(--shadow-sm);
		cursor: grabbing;
	}

	.tier-row :global(.drag-handle) {
		display: grid;
		place-items: center;
		width: 2.1rem;
		min-height: 2.1rem;
		padding: 0;
		border-color: var(--border-strong);
		border-radius: var(--radius-sm);
		background: var(--input-bg);
		color: var(--subdued);
		font-size: 1rem;
		letter-spacing: 0;
		line-height: 1;
		cursor: grab;
		touch-action: none;
	}

	.tier-row :global(.drag-handle:active) {
		cursor: grabbing;
	}

	.color-marker {
		align-self: stretch;
		border: 1px solid rgb(0 0 0 / 14%);
		border-radius: 0.24rem;
		background: var(--tier-color);
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
		border: var(--bw) solid var(--line);
		border-top: 0.35rem solid var(--tier-color);
		border-radius: var(--radius-sm);
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

	.players-panel :global(.search) {
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

	.percentage-field {
		position: relative;
		min-width: 0;
	}

	.percentage-field :global(input) {
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

	.tier-selector :global(select.has-tier) {
		border-left: 4px solid var(--tier-color);
	}

	@media (max-width: 900px) {
		.player-row {
			grid-template-columns: 0.35rem 1fr auto;
		}

		.tier-row {
			grid-template-columns: auto 0.35rem 1fr auto;
		}

		.tier-actions {
			grid-column: 3 / -1;
		}

		.player-row > :global(input),
		.player-row > .tier-selector,
		.player-row > .percentage-field,
		.player-row > .save-status {
			grid-column: 2 / -1;
		}
	}

	@media (max-width: 560px) {
		.tier-form,
		.tier-actions {
			flex-wrap: wrap;
		}

		.tier-form :global(.tier-name) {
			width: 100%;
		}
	}
</style>
