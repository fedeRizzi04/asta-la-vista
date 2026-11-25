<script lang="ts">
	import { tick } from 'svelte';
	import { dragReorder } from '$lib/actions/dragReorder';
	import TierBoard from '$lib/components/TierBoard.svelte';
	import TierPlayerCard from '$lib/components/TierPlayerCard.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { t } from '$lib/i18n';
	import type { Role } from '$lib/players';
	import { percentageToCredits } from '$lib/strategies';
	import type { PlayerDrag } from './playerDrag.svelte';
	import PlayerList from './PlayerList.svelte';
	import { referenceBudget } from './referenceBudget.svelte';
	import { tierTitle } from './SelectionBar.svelte';
	import type { StrategyEditor } from './strategyEditor.svelte';

	/** The tiers of the edited strategy, with the players of one role. */
	let { editor, drag, role }: { editor: StrategyEditor; drag: PlayerDrag; role: Role } = $props();

	let addButton = $state<HTMLButtonElement>();

	let columns = $derived(
		editor.orderedTiers.map((tier, index) => ({
			key: tier.id,
			tier,
			title: tierTitle(tier, index),
			dropTarget: drag.target === tier.id,
			players: editor.playersInTier(tier.id, role, (id) => drag.landsIn(tier.id, id))
		}))
	);

	const nameId = (tierId: string) => `tier-name-${tierId}`;

	function focusSetup(button: HTMLElement): void {
		if (document.activeElement === document.body) button.focus({ preventScroll: true });
	}

	async function addTier(): Promise<void> {
		const tierId = await editor.addTier();
		if (!tierId) return;
		await tick();
		const nameInput = document.getElementById(nameId(tierId)) as HTMLInputElement | null;
		nameInput?.focus({ preventScroll: true });
		nameInput?.select();
		// Shows the whole new column, and the button to add the next one.
		addButton?.scrollIntoView({ block: 'nearest', inline: 'end' });
	}
</script>

<div
	class="strategy-tiers"
	use:dragReorder={{
		ids: () => editor.orderedTiers.map((tier) => tier.id),
		onCommit: (ids) => editor.commitTierOrder(ids),
		disabled: () => editor.saving
	}}
>
	{#if columns.length === 0}
		<EmptyState>
			<h2>{t.strategies.addFirstTiers}</h2>
			<div class="setup-actions">
				<Button
					size="sm"
					disabled={editor.saving}
					onclick={() => editor.addDefaultTiers()}
					{@attach focusSetup}
				>
					{t.strategies.useDefaultTiers}
				</Button>
				<Button variant="secondary" size="sm" onclick={addTier} disabled={editor.saving}>
					{t.strategies.createTiersManually}
				</Button>
			</div>
		</EmptyState>
	{:else}
		<TierBoard {columns} label={t.strategies.strategyTiers}>
			{#snippet header({ tier, title, players })}
				<div class="header">
					<button
						type="button"
						class="handle"
						data-drag-handle
						aria-label={t.strategies.reorderTier(tier.name)}
					>
						⠿
					</button>
					<Input
						type="color"
						class="color"
						value={tier.color ?? '#d8ded9'}
						oninput={(event) => {
							tier.color = event.currentTarget.value;
							editor.scheduleTierSave(tier.id);
						}}
						onchange={() => editor.flushTierSave(tier.id)}
						aria-label={t.strategies.tierColor(tier.name)}
					/>
					<Input
						id={nameId(tier.id)}
						class="inline-name"
						bind:value={
							() => editor.tierNameDrafts[tier.id] ?? tier.name,
							(name) => (editor.tierNameDrafts[tier.id] = name)
						}
						{title}
						oninput={() => editor.scheduleTierSave(tier.id)}
						onblur={() => {
							void editor.flushTierSave(tier.id);
							if (!editor.tierNameDrafts[tier.id]?.trim()) delete editor.tierNameDrafts[tier.id];
						}}
						onkeydown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
						autocomplete="off"
						aria-label={t.strategies.tierName}
					/>
					<span class="saved" role="status">
						{#if editor.tierSaved[tier.id]}
							<span role="img" aria-label={t.strategies.saved} title={t.strategies.saved}>✓</span>
						{/if}
					</span>
					<span class="count" title={t.strategies.players}>{players.length}</span>
					<Button
						variant="text"
						size="sm"
						class="delete"
						title={t.strategies.deleteTier}
						aria-label={t.strategies.deleteTierLabel(tier.name)}
						onclick={() => editor.deleteTier(tier)}
						disabled={editor.saving}
					>
						✕
					</Button>
				</div>
			{/snippet}
			{#snippet players({ tier, players })}
				<PlayerList {editor} {drag} {players} tierId={tier.id} label={tier.name}>
					{#snippet row(player)}
						{@const draft = editor.entryDrafts[player.id]}
						{@const pct = draft.maximumPricePercentage}
						<TierPlayerCard
							name={player.name}
							team={player.active ? player.team : t.strategies.inactiveClub(player.team)}
							mantraRoles={player.mantra_roles}
							maximumPricePercentage={pct ?? null}
							maximumPriceCredits={pct === undefined
								? null
								: percentageToCredits(pct, referenceBudget.value)}
							note={draft.note}
							inactive={!player.active}
						/>
					{/snippet}
				</PlayerList>
			{/snippet}
			{#snippet trailing()}
				<button
					type="button"
					class="add"
					bind:this={addButton}
					onclick={addTier}
					disabled={editor.saving}
				>
					+ {t.strategies.newTier}
				</button>
			{/snippet}
		</TierBoard>
	{/if}
</div>

<style>
	.strategy-tiers {
		min-width: 0;
		min-height: 0;
	}

	.strategy-tiers :global(.empty-state) {
		margin-top: 0;
	}

	h2 {
		margin: 0 0 0.65rem;
		color: var(--text);
		font-size: 1rem;
	}

	.setup-actions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.header {
		display: grid;
		grid-template-columns: auto auto minmax(0, 1fr) 0.8rem auto auto;
		align-items: center;
		gap: 0.3rem;
		padding: 0.3rem 0.3rem 0.3rem 0.2rem;
	}

	.handle {
		min-width: 1.5rem;
		padding: 0.3rem 0.25rem;
		border: 0;
		border-radius: var(--radius-xs);
		background: none;
		color: var(--muted);
		line-height: 1;
		cursor: grab;
		touch-action: none;
	}

	.handle:hover {
		background: var(--hover);
		color: var(--text);
	}

	.handle:active {
		cursor: grabbing;
	}

	.header :global(.color) {
		width: 1.5rem;
		min-height: 1.5rem;
		height: 1.5rem;
		padding: 0.05rem;
		border-width: 1px;
		border-radius: var(--radius-xs);
		cursor: pointer;
	}

	.header :global(.inline-name) {
		min-height: 1.75rem;
		font: 800 0.95rem var(--font-display);
	}

	.header :global(.delete) {
		min-height: 1.5rem;
		padding: 0 0.35rem;
	}

	.saved {
		color: var(--success-text);
		font-weight: 700;
	}

	.count {
		color: var(--muted);
		font: 800 0.8rem var(--font-display);
		font-variant-numeric: tabular-nums;
	}

	.add {
		flex: 0 0 10rem;
		align-self: start;
		min-height: 7rem;
		border: var(--bw) dashed var(--line);
		border-radius: var(--radius-sm);
		background: transparent;
		color: var(--muted);
		font-weight: 700;
		cursor: pointer;
	}

	.add:hover {
		background: var(--hover);
		color: var(--text);
	}
</style>
