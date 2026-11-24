<script lang="ts">
	import { tick } from 'svelte';
	import { dragReorder } from '$lib/actions/dragReorder';
	import TierBoard from '$lib/components/TierBoard.svelte';
	import TierPlayerCard from '$lib/components/TierPlayerCard.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import type { Role } from '$lib/players';
	import type { StrategyEditor } from './strategyEditor.svelte';

	/** The tiers of the edited strategy, with the players of one role. */
	let { editor, role }: { editor: StrategyEditor; role: Role } = $props();

	let addButton = $state<HTMLButtonElement>();

	let columns = $derived(
		editor.orderedTiers.map((tier) => ({
			key: tier.id,
			tier,
			entries: editor.entriesForTier(tier.id, role)
		}))
	);

	const nameId = (tierId: string) => `tier-name-${tierId}`;

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
	<TierBoard {columns} label="Fasce della strategia">
		{#snippet header({ tier, entries })}
			<div class="header">
				<button
					type="button"
					class="handle"
					data-drag-handle
					aria-label="Trascina per riordinare “{tier.name}”, o usa le frecce sinistra/destra"
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
					aria-label="Colore di “{tier.name}”"
				/>
				<Input
					id={nameId(tier.id)}
					class="name"
					bind:value={tier.name}
					title={tier.name}
					oninput={() => editor.scheduleTierSave(tier.id)}
					onblur={() => editor.flushTierSave(tier.id)}
					onkeydown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
					autocomplete="off"
					aria-label="Nome fascia"
				/>
				<span class="saved" role="status">
					{#if editor.tierSaved[tier.id]}
						<span role="img" aria-label="Salvato" title="Salvato">✓</span>
					{/if}
				</span>
				<span class="count" title="Calciatori">{entries.length}</span>
				<Button
					variant="text"
					size="sm"
					class="delete"
					title="Elimina fascia"
					aria-label="Elimina “{tier.name}”"
					onclick={() => editor.deleteTier(tier)}
					disabled={editor.saving}
				>
					✕
				</Button>
			</div>
		{/snippet}
		{#snippet players({ entries })}
			{#each entries as { player, draft } (player.id)}
				<TierPlayerCard
					name={player.name}
					team={player.active ? player.team : `${player.team} · inattivo`}
					mantraRoles={player.mantra_roles}
					maximumPricePercentage={draft.maximumPricePercentage ?? null}
					note={draft.note}
					inactive={!player.active}
				/>
			{:else}
				<p class="empty">Nessun calciatore</p>
			{/each}
		{/snippet}
		{#snippet trailing()}
			<button
				type="button"
				class="add"
				bind:this={addButton}
				onclick={addTier}
				disabled={editor.saving}
			>
				+ Nuova fascia
			</button>
		{/snippet}
	</TierBoard>
</div>

<style>
	.strategy-tiers {
		min-width: 0;
		min-height: 0;
	}

	.header {
		display: grid;
		grid-template-columns: auto auto minmax(0, 1fr) 0.8rem auto auto;
		align-items: center;
		gap: 0.3rem;
		padding: 0.3rem 0.3rem 0.3rem 0.2rem;
	}

	.handle {
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
		width: 1.35rem;
		min-height: 1.5rem;
		height: 1.5rem;
		padding: 0.05rem;
		border-width: 1px;
		border-radius: var(--radius-xs);
		cursor: pointer;
	}

	.header :global(.name) {
		min-height: 1.75rem;
		padding: 0 0.3rem;
		border-color: transparent;
		border-radius: var(--radius-xs);
		background: transparent;
		font: 800 0.95rem var(--font-display);
		text-overflow: ellipsis;
	}

	.header :global(.name:hover) {
		border-color: var(--line-soft);
	}

	.header :global(.name:focus) {
		border-color: var(--line);
		background: var(--input-bg);
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

	.empty {
		margin: 0;
		padding: 0.45rem;
		color: var(--muted);
		font-size: 0.8rem;
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
