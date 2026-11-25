<script lang="ts">
	import { nameFit } from '$lib/names';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import { t } from '$lib/i18n';

	/** A player's row in a tier. A taken player shows who bought them and the price paid. */
	let {
		name,
		team,
		mantraRoles = [],
		maximumPricePercentage = null,
		maximumPriceCredits = null,
		note = '',
		inactive = false,
		taken
	}: {
		name: string;
		team: string;
		mantraRoles?: string[];
		maximumPricePercentage?: number | null;
		maximumPriceCredits?: number | null;
		note?: string;
		inactive?: boolean;
		taken?: { buyer: string; price: number };
	} = $props();
</script>

<span class="tier-player" class:inactive class:taken>
	<span class="identity">
		<strong class={['name-line', nameFit(name)]} title={name}>{name}</strong>
		{#if !taken}
			<small>{team}</small>
			<MantraRoleBadges roles={mantraRoles} compact />
		{/if}
	</span>
	{#if taken}
		<span class="price"
			><small class={['name-line', nameFit(taken.buyer)]} title={taken.buyer}>{taken.buyer}</small>
			<span>{taken.price}</span></span
		>
	{:else if maximumPricePercentage !== null}
		<span class="price" title={t.common.maximumPrice}>
			<b>{maximumPricePercentage}%</b>
			{#if maximumPriceCredits !== null}<small>{maximumPriceCredits}</small>{/if}
		</span>
	{/if}
	{#if note && !taken}<em title={note}>{note}</em>{/if}
</span>

<style>
	.tier-player {
		display: grid;
		grid-template-columns: minmax(var(--name-min), 1fr) auto;
		align-items: baseline;
		gap: 0 0.5rem;
		padding: 0.25rem 0.45rem;
		font-size: 0.875rem;
	}

	.identity {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0 0.35rem;
		min-width: 0;
	}

	em {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	small,
	em {
		color: var(--muted);
		font-size: 0.75rem;
	}

	em {
		grid-column: 1 / -1;
	}

	.price {
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}

	.price b {
		font: 800 0.9rem/1 var(--font-display);
	}

	.taken,
	.inactive,
	.taken small,
	.inactive small,
	.inactive em {
		color: var(--taken-text);
	}

	.taken strong {
		text-decoration: line-through;
	}

	/* The player keeps the room he needs; the buyer's name gives way first. */
	.taken {
		grid-template-columns: minmax(var(--name-min), max-content) minmax(9ch, 1fr);
	}

	.taken .price {
		display: flex;
		justify-content: flex-end;
		gap: 0.25rem;
		min-width: 0;
		font-size: 0.75rem;
		font-weight: 700;
	}
</style>
