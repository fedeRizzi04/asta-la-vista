<script lang="ts">
	import type { Snippet } from 'svelte';

	/** A dashed placeholder for "nothing here yet" and loading messages. */
	let { compact = false, children }: { compact?: boolean; children: Snippet } = $props();
</script>

<div class="empty-state" class:compact>{@render children()}</div>

<style>
	.empty-state {
		margin-top: 1.5rem;
		padding: 1.25rem;
		border: var(--bw) dashed var(--border-strong);
		border-radius: var(--radius);
		background: var(--surface);
		color: var(--muted);
	}

	.compact {
		margin-top: 1rem;
		padding: 1rem;
		border-width: 1px;
		border-radius: var(--radius-sm);
		background: transparent;
		font-size: 0.85rem;
	}
</style>
