<script lang="ts">
	import { nameFit } from '$lib/names';
	import type { PlayerDrag } from './playerDrag.svelte';

	/** What follows the pointer while players are dragged. */
	let { drag }: { drag: PlayerDrag } = $props();

	let grabbed = $derived(drag.players.at(0));
</script>

{#if grabbed}
	<div
		class="preview"
		bind:this={drag.preview}
		style:transform="translate({drag.x - 16}px, {drag.y - 16}px)"
		aria-hidden="true"
	>
		<div class="card" class:stacked={drag.players.length > 1}>
			<strong class={['name-line', nameFit(grabbed.name)]}>{grabbed.name}</strong>
			<small class={['name-line', nameFit(grabbed.team)]}>{grabbed.team}</small>
			{#if drag.players.length > 1}<span class="count">{drag.players.length}</span>{/if}
		</div>
	</div>
{/if}

<style>
	.preview {
		position: fixed;
		top: 0;
		left: 0;
		/* Above the app header. */
		z-index: 950;
		pointer-events: none;
	}

	.card {
		display: flex;
		align-items: baseline;
		gap: 0.4rem;
		max-width: 18rem;
		padding: 0.3rem 0.6rem;
		border: var(--bw) solid var(--line);
		border-radius: var(--radius-xs);
		background: var(--selected-bg);
		box-shadow: var(--shadow-sm);
		font-size: 0.875rem;
		rotate: -2deg;
	}

	/* Two more cards under the first one. */
	.stacked {
		box-shadow:
			4px 4px 0 -2px var(--surface),
			4px 4px 0 0 var(--line),
			8px 8px 0 -2px var(--surface),
			8px 8px 0 0 var(--line);
	}

	/* The team gives way before the player. */
	small {
		flex-shrink: 4;
		color: var(--muted);
		font-size: 0.75rem;
	}

	.count {
		position: absolute;
		top: -0.7rem;
		right: -0.7rem;
		min-width: 1.4rem;
		padding: 0.2rem 0.35rem;
		border: var(--bw) solid var(--line);
		border-radius: 999px;
		background: var(--primary);
		color: var(--on-primary);
		font: 800 0.8rem/1 var(--font-display);
		text-align: center;
	}
</style>
