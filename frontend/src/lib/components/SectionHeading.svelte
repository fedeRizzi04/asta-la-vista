<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		eyebrow,
		title,
		subtitle,
		trailing
	}: {
		eyebrow?: string;
		title: string;
		subtitle?: string;
		trailing?: Snippet;
	} = $props();
</script>

<div class="section-heading">
	<div>
		{#if eyebrow}<p class="eyebrow">{eyebrow}</p>{/if}
		<h2>{title}</h2>
		{#if subtitle}<p class="subtitle">{subtitle}</p>{/if}
	</div>
	{#if trailing}{@render trailing()}{/if}
</div>

<style>
	.section-heading {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1.5rem;
		margin-bottom: 0.8rem;
	}

	.section-heading .eyebrow {
		margin-bottom: 0.5rem;
	}

	.section-heading h2 {
		margin: 0;
		font-size: 1.15rem;
	}

	.section-heading .subtitle {
		margin: 0.3rem 0 0;
		color: var(--subdued);
		font-size: 0.8rem;
	}

	@media (max-width: 720px) {
		.section-heading {
			align-items: stretch;
			flex-direction: column;
		}
	}
</style>
