<script lang="ts" module>
	import type { PanelVisibility } from '$lib/panelVisibility.svelte';
	import type { Tier } from '$lib/strategies';

	/** The players of one tier. A column without a `panel` is always open. */
	export type TierColumn = {
		key: string;
		tier: Tier;
		panel?: PanelVisibility;
		/** Highlights the column as the place where the dragged players would go. */
		dropTarget?: boolean;
	};
</script>

<script lang="ts" generics="Column extends TierColumn">
	import type { Snippet } from 'svelte';
	import HorizontalScroller from './HorizontalScroller.svelte';

	/**
	 * The tiers of a strategy as columns in one scrollable row. A closed column shrinks to a
	 * vertical strip. The board only lays the columns out: the caller renders what goes in them
	 * (`players`) and next to the tier name (`summary`).
	 *
	 * To edit the tiers, pass a whole `header` for the columns instead. The board then fills its
	 * container and scrolls in it both ways, with the headers always in view; `dragReorder` can
	 * move the columns, `PlayerDrag` can drop players in them, and `trailing` comes after the last
	 * one.
	 */
	let {
		columns,
		label,
		summary,
		header,
		players,
		trailing
	}: {
		columns: Column[];
		label: string;
		summary?: Snippet<[Column]>;
		header?: Snippet<[Column]>;
		players: Snippet<[Column]>;
		trailing?: Snippet;
	} = $props();
</script>

{#snippet board()}
	<div class="tier-board">
		{#each columns as column (column.key)}
			{@const { tier, panel } = column}
			{@const visible = panel?.visible ?? true}
			<section
				class="tier"
				class:closed={!visible}
				class:drop-target={column.dropTarget}
				aria-label={header ? tier.name : undefined}
				data-drag-id={header ? tier.id : undefined}
				data-drop-tier={header ? tier.id : undefined}
			>
				{#if header}
					<div class="edit-header">{@render header(column)}</div>
				{:else}
					<h3>
						<button
							type="button"
							class="tier-header"
							aria-expanded={visible}
							title={tier.name}
							onclick={() => panel?.toggle()}
						>
							<span class="chevron" aria-hidden="true">▾</span>
							<span
								class="tier-color"
								style:background={tier.color ?? 'var(--tier-default)'}
								aria-hidden="true"
							></span>
							<span class="tier-name">{tier.name}</span>
							<span class="tier-summary">{@render summary?.(column)}</span>
						</button>
					</h3>
				{/if}
				{#if visible}
					<div class="tier-players">{@render players(column)}</div>
				{/if}
			</section>
		{/each}
		{@render trailing?.()}
	</div>
{/snippet}

{#if header}
	<div class="edit-viewport" role="region" aria-label={label} data-drag-scroll>
		{@render board()}
	</div>
{:else}
	<HorizontalScroller ariaLabel={label}>{@render board()}</HorizontalScroller>
{/if}

<style>
	.tier-board {
		display: flex;
		align-items: stretch;
		gap: 0.7rem;
		/* A row of closed columns still leaves room for the vertical names. */
		min-height: 14rem;
		/* Room for the hard shadows, clipped by the scroller. */
		padding: 0 2px 2px 0;
	}

	.tier {
		display: flex;
		flex: 0 0 min(17.5rem, calc(100vw - 4rem));
		flex-direction: column;
		min-width: 0;
		border: var(--bw) solid var(--line);
		border-radius: var(--radius-sm);
		background: var(--surface);
		box-shadow: var(--shadow-xs);
		overflow: hidden;
	}

	.tier.closed {
		flex-basis: 2.75rem;
	}

	h3 {
		margin: 0;
		font-size: 0.95rem;
	}

	.tier-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		min-height: 2.4rem;
		padding: 0.35rem 0.6rem;
		border: 0;
		border-bottom: var(--bw) solid var(--line);
		background: var(--head-bg);
		text-align: left;
		cursor: pointer;
	}

	.tier-header:hover {
		background: var(--hover);
	}

	.tier-header:focus-visible {
		outline-offset: -3px;
	}

	.chevron,
	.tier-color,
	.tier-summary {
		flex: none;
	}

	.tier-color {
		width: 0.7rem;
		height: 1.25rem;
		border: 1px solid var(--line);
		border-radius: 3px;
	}

	.tier-name {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		font-weight: 800;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.tier-summary {
		color: var(--muted);
		font: 0.75rem var(--font-text);
		font-variant-numeric: tabular-nums;
	}

	.tier-players {
		display: grid;
		align-content: start;
		padding: 0.25rem;
	}

	.edit-viewport {
		height: 100%;
		overflow: auto;
	}

	.edit-viewport .tier-board {
		width: max-content;
		min-height: 100%;
	}

	.edit-viewport .tier {
		flex-basis: min(15.5rem, calc(100vw - 4rem));
		/* Unlike hidden, it lets the header stick to the viewport. */
		overflow: clip;
	}

	.edit-header {
		position: sticky;
		top: 0;
		z-index: 1;
		border-bottom: var(--bw) solid var(--line);
		background: var(--head-bg);
	}

	.drop-target {
		border-color: var(--focus);
		background: color-mix(in srgb, var(--selected-bg) 45%, var(--surface));
		box-shadow: 0 0 0 2px var(--focus);
	}

	.tier:global(.is-dragging) {
		position: relative;
		z-index: 2;
		box-shadow: var(--shadow);
	}

	.closed h3 {
		flex: 1;
		min-height: 0;
	}

	.closed .tier-header {
		flex-direction: column;
		height: 100%;
		padding: 0.6rem 0;
		border-bottom: 0;
	}

	.closed .chevron {
		transform: rotate(-90deg);
	}

	.closed .tier-name,
	.closed .tier-summary {
		writing-mode: vertical-rl;
	}

	.closed .tier-name {
		flex: 0 1 auto;
		min-width: auto;
		min-height: 0;
		max-width: 100%;
		max-height: 16rem;
	}
</style>
