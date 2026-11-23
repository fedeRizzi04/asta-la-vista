<script lang="ts">
	import type { Snippet } from 'svelte';
	import { press } from '$lib/actions/press';

	/** An on/off pill for filters where several can be active together (unlike Tabs). */
	let {
		pressed,
		onclick,
		children
	}: {
		pressed: boolean;
		onclick: () => void;
		children: Snippet;
	} = $props();
</script>

<button type="button" class="toggle-chip" aria-pressed={pressed} use:press {onclick}>
	{@render children()}
</button>

<style>
	.toggle-chip {
		display: inline-flex;
		align-items: center;
		min-height: 1.85rem;
		padding: 0 0.7rem;
		border: var(--bw) solid var(--line-soft);
		border-radius: 999px;
		background: var(--surface);
		color: var(--muted);
		font-size: 0.8rem;
		font-weight: 700;
		cursor: pointer;
		transition:
			background-color 140ms ease,
			border-color 140ms ease;
	}

	.toggle-chip:hover {
		border-color: var(--border-hover);
		color: var(--text);
	}

	.toggle-chip[aria-pressed='true'] {
		border-color: var(--line);
		background: var(--selected-bg);
		color: var(--text);
	}
</style>
