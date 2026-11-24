<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { ResolvedPathname } from '$app/types';

	/** One compact row on top of each page, so the laptop screen's height goes to the data. */
	let {
		title,
		back,
		meta,
		actions,
		compact = false
	}: {
		title: string | Snippet;
		back?: { href: ResolvedPathname; label: string };
		meta?: Snippet;
		actions?: Snippet;
		compact?: boolean;
	} = $props();
</script>

<header class="page-header" class:compact>
	{#if back}<a class="back" href={back.href}>← {back.label}</a>{/if}
	<h1 class:custom-title={typeof title !== 'string'}>
		{#if typeof title === 'string'}{title}{:else}{@render title()}{/if}
	</h1>
	{#if meta}{@render meta()}{/if}
	{#if actions}<div class="actions">{@render actions()}</div>{/if}
</header>

<style>
	.page-header {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem 1rem;
		min-height: 3rem;
		margin-bottom: 1.25rem;
	}

	.back {
		color: var(--muted);
		font-size: 0.9rem;
		font-weight: 700;
		text-decoration: none;
	}

	.back:hover {
		color: var(--text);
	}

	h1 {
		font-size: 1.45rem;
	}

	.actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.6rem;
		margin-left: auto;
	}

	.compact {
		gap: 0.5rem 0.7rem;
		min-height: 2.25rem;
		margin-bottom: 0.65rem;
	}

	.compact .back {
		white-space: nowrap;
	}

	.compact h1 {
		min-width: 0;
	}

	.compact h1:not(.custom-title) {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	@media (min-width: 72rem) {
		.compact,
		.compact .actions {
			flex-wrap: nowrap;
		}
	}
</style>
