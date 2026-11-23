<script lang="ts">
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<kbd>{@render children()}</kbd>

<style>
	kbd {
		padding: 0.2rem 0.32rem;
		border: 1px solid var(--line-soft);
		border-radius: var(--radius-xs);
		background: var(--muted-bg);
		color: var(--text);
		font: 700 0.7rem/1 var(--font-text);
		white-space: nowrap;
	}
</style>
