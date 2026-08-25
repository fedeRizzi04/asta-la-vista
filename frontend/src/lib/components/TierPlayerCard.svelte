<script lang="ts">
	let {
		name,
		team,
		maximumPricePercentage = null,
		maximumPriceCredits = null,
		note = '',
		inactive = false,
		purchased = false,
		compact = false
	}: {
		name: string;
		team: string;
		maximumPricePercentage?: number | null;
		maximumPriceCredits?: number | null;
		note?: string;
		inactive?: boolean;
		purchased?: boolean;
		compact?: boolean;
	} = $props();

	let maximumPriceLabel = $derived.by(() => {
		if (maximumPricePercentage === null) return '';
		const percentageText = `${maximumPricePercentage}%`;
		return maximumPriceCredits === null
			? ` · max ${percentageText}`
			: ` · max ${maximumPriceCredits} cr (${percentageText})`;
	});
</script>

<article class:inactive class:purchased class:compact>
	<strong>{name}</strong>
	<small>{team}{maximumPriceLabel}{note ? ` · ${note}` : ''}</small>
</article>

<style>
	article {
		display: grid;
		gap: 0.12rem;
		padding: 0.5rem;
		border-radius: 0.32rem;
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
		color: var(--disabled-text);
		background: var(--muted-bg);
		opacity: 0.7;
	}

	article.purchased strong {
		text-decoration: line-through;
		text-decoration-color: var(--disabled-text);
	}

	small {
		color: var(--subdued);
	}
</style>
