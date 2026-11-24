<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onDestroy, onMount } from 'svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import SectionHeading from '$lib/components/SectionHeading.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import Tabs from '$lib/components/ui/Tabs.svelte';
	import { PlayerDrag } from '$lib/features/strategy/playerDrag.svelte';
	import PlayerDragPreview from '$lib/features/strategy/PlayerDragPreview.svelte';
	import PlayerPool from '$lib/features/strategy/PlayerPool.svelte';
	import SelectionBar from '$lib/features/strategy/SelectionBar.svelte';
	import { StrategyEditor } from '$lib/features/strategy/strategyEditor.svelte';
	import StrategyTiers from '$lib/features/strategy/StrategyTiers.svelte';
	import { roleLabels, roles, type Role } from '$lib/players';
	import { matchesSearch } from '$lib/search';

	const editor = new StrategyEditor(() => page.params.strategyId);
	const drag = new PlayerDrag(editor);
	const strategy = $derived(editor.strategy);
	const roleTabs = roles.map((role) => ({ value: role, label: roleLabels[role] }));

	let selectedRole = $state<Role>('P');
	let playerSearch = $state('');

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

	onMount(() => editor.load());
	onDestroy(() => void editor.flushAll());
</script>

<!-- A reload or a closed window does not destroy the component. -->
<svelte:window onpagehide={() => editor.flushOnUnload()} />

<svelte:head>
	<title>{strategy?.name ?? 'Strategia'} | Asta la Vista</title>
</svelte:head>

<div class="editor">
	<PageHeader
		compact
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
		<div class="toolbar">
			<Tabs
				items={roleTabs}
				bind:value={selectedRole}
				label="Ruoli"
				id="strategy-role"
				panelId="strategy-role-panel"
				onchange={() => {
					playerSearch = '';
					editor.selection.clear();
				}}
			/>
			<SelectionBar {editor} workspaceId="strategy-role-panel" />
		</div>
		<div
			id="strategy-role-panel"
			class="workspace"
			role="tabpanel"
			tabindex="0"
			aria-labelledby="strategy-role-{selectedRole}"
			use:drag.area
		>
			<PlayerPool {editor} {drag} role={selectedRole} />
			<StrategyTiers {editor} {drag} role={selectedRole} />
		</div>
		<PlayerDragPreview {drag} />
	{/if}
</div>

{#if strategy && !editor.loading}
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
					{@const selectedPlayerTier = editor.tierOfPlayer(player.id)}
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
{/if}

<style>
	/* The tiers need the whole width of the window. */
	:global(main):has(.editor) {
		width: calc(100% - 3rem);
	}

	/* Fills the window, down to a gap as big as the padding above, so that only the pool and
	   the board scroll. */
	.editor {
		display: flex;
		flex-direction: column;
		height: calc(100dvh - var(--header-height) - 3rem);
		min-height: 30rem;
	}

	.toolbar {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem 1rem;
		margin-bottom: 0.6rem;
	}

	.workspace {
		display: grid;
		flex: 1;
		grid-template: minmax(0, 1fr) / 19.5rem minmax(0, 1fr);
		gap: 1rem;
		min-height: 0;
	}

	.name-form {
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

	.player-list {
		display: grid;
		gap: 0.55rem;
		margin-top: 1rem;
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
		.editor {
			height: auto;
		}

		.workspace {
			grid-template: 24rem auto / minmax(0, 1fr);
		}

		.player-row {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 720px) {
		:global(main):has(.editor) {
			width: calc(100% - 2rem);
		}
	}
</style>
