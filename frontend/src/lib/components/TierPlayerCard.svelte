<script lang="ts">
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';

	let {
		name,
		team,
		mantraRoles = [],
		maximumPricePercentage = null,
		maximumPriceCredits = null,
		note = '',
		inactive = false,
		purchased = false,
		compact = false
	}: {
		name: string;
		team: string;
		mantraRoles?: string[];
		maximumPricePercentage?: number | null;
		maximumPriceCredits?: number | null;
		note?: string;
		inactive?: boolean;
		purchased?: boolean;
		compact?: boolean;
	} = $props();

	let maximumPriceText = $derived.by(() => {
		if (maximumPricePercentage === null) return '';
		const percentageText = `${maximumPricePercentage}%`;
		return maximumPriceCredits === null
			? `max ${percentageText}`
			: `max ${maximumPriceCredits} cr (${percentageText})`;
	});
</script>

<article class:inactive class:purchased class:compact>
	<span class="name-row"
		><strong>{name}</strong><MantraRoleBadges roles={mantraRoles} compact /></span
	>
	<small
		>{team}{note ? ` · ${note}` : ''}{#if maximumPriceText}
			· <span class="max-price">{maximumPriceText}</span>{/if}</small
	>
</article>

<style>
	article {
		display: grid;
		gap: 0.12rem;
		padding: 0.5rem;
		border-radius: var(--radius-xs);
		background: var(--input-bg);
		font-size: 0.8rem;
	}

	article.compact {
		padding: 0.45rem 0.55rem;
		font-size: 0.74rem;
	}

	article.inactive {
		color: var(--disabled-text);
		background: var(--muted-bg);
	}

	article.purchased {
		color: var(--taken-text);
		background: var(--muted-bg);
	}

	article.purchased strong {
		text-decoration: line-through;
	}

	article.purchased small,
	article.purchased .max-price {
		color: inherit;
	}

	small {
		color: var(--subdued);
	}

	.name-row {
		display: inline-flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.3rem;
	}

	.name-row strong {
		font-size: 1.15em;
	}

	.max-price {
		color: var(--primary-text);
		font-weight: 700;
		text-decoration: overline;
		text-decoration-color: var(--primary-text);
	}
</style>
