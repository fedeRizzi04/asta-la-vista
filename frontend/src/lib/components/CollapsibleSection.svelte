<script lang="ts">
	import type { Snippet } from 'svelte';
	import SectionHeading from './SectionHeading.svelte';
	import { panelVisibility } from '$lib/panelVisibility.svelte';

	/**
	 * A SectionHeading whose body can be skipped past with a Mostra/Nascondi toggle, so a
	 * long screen (a live auction, a strategy) can be scanned quickly. The show/hide choice
	 * is remembered per `storageKey` (see panelVisibility.svelte.ts).
	 */
	let {
		storageKey,
		eyebrow,
		title,
		subtitle,
		defaultVisible = true,
		trailing,
		children
	}: {
		storageKey: string;
		eyebrow?: string;
		title: string;
		subtitle?: string;
		defaultVisible?: boolean;
		trailing?: Snippet;
		children: Snippet;
	} = $props();

	let panel = $derived(panelVisibility(storageKey, defaultVisible));
</script>

{#snippet trailingContent()}
	<div class="collapsible-trailing">
		{#if trailing}{@render trailing()}{/if}
		<button type="button" class="text-button" onclick={() => panel.toggle()}>
			{panel.visible ? 'Nascondi' : 'Mostra'}
		</button>
	</div>
{/snippet}

<SectionHeading {eyebrow} {title} {subtitle} trailing={trailingContent} />
{#if panel.visible}
	{@render children()}
{/if}

<style>
	.collapsible-trailing {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
</style>
