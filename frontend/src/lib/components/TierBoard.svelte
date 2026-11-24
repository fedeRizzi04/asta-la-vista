<script lang="ts" module>
	import type { PanelVisibility } from '$lib/panelVisibility.svelte';
	import type { Tier } from '$lib/strategies';

	/** The players of one tier. */
	export type TierColumn = { key: string; tier: Tier; panel: PanelVisibility };
</script>

<script lang="ts" generics="Column extends TierColumn">
	import type { Snippet } from 'svelte';
	import HorizontalScroller from './HorizontalScroller.svelte';

	/**
	 * The tiers of a strategy as columns in one scrollable row. A closed column shrinks to a
	 * vertical strip. The board only lays the columns out: the caller renders what goes in them
	 * (`players`) and next to the tier name (`summary`).
	 */
	let {
		columns,
		label,
		summary,
		players
	}: {
		columns: Column[];
		label: string;
		summary: Snippet<[Column]>;
		players: Snippet<[Column]>;
	} = $props();
</script>

<HorizontalScroller ariaLabel={label}>
	<div class="tier-board">
		{#each columns as column (column.key)}
			{@const { tier, panel } = column}
			<section class="tier" class:closed={!panel.visible}>
				<h3>
					<button
						type="button"
						class="tier-header"
						aria-expanded={panel.visible}
						title={tier.name}
						onclick={() => panel.toggle()}
					>
						<span class="chevron" aria-hidden="true">▾</span>
						<span
							class="tier-color"
							style:background={tier.color ?? 'var(--tier-default)'}
							aria-hidden="true"
						></span>
						<span class="tier-name">{tier.name}</span>
						<span class="tier-summary">{@render summary(column)}</span>
					</button>
				</h3>
				{#if panel.visible}
					<div class="tier-players">{@render players(column)}</div>
				{/if}
			</section>
		{/each}
	</div>
</HorizontalScroller>

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
