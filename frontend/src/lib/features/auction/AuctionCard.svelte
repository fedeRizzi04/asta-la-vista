<script lang="ts">
	import { resolve } from '$app/paths';
	import type { Snippet } from 'svelte';
	import { auctionStatusLabels, type AuctionSummary } from '$lib/auctions';
	import Button from '$lib/components/ui/Button.svelte';
	import { t } from '$lib/i18n';

	let {
		auction,
		highlighted = false,
		heading = 'h2',
		actions
	}: {
		auction: AuctionSummary;
		highlighted?: boolean;
		heading?: 'h2' | 'h3';
		actions?: Snippet;
	} = $props();

	const openLabel = $derived(highlighted ? t.auctions.resume : t.strategies.open);
</script>

<article class:highlighted>
	<div class="details">
		<div class="title">
			<svelte:element this={heading}>{auction.name}</svelte:element>
			<span class="status-badge" data-status={auction.status}>
				{auctionStatusLabels[auction.status]}
			</span>
		</div>
		<p>
			{t.auctions.cardSummary(
				auction.participant_count,
				auction.purchase_count,
				auction.initial_credits
			)}
		</p>
	</div>
	<div class="actions">
		{@render actions?.()}
		<Button
			href={resolve('/auctions/[auctionId]', { auctionId: auction.id })}
			variant={highlighted ? 'primary' : 'secondary'}
			size="sm"
			aria-label={`${openLabel} ${auction.name}`}
		>
			{openLabel}
		</Button>
	</div>
</article>

<style>
	article {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 0.6rem 1rem;
		padding: 0.75rem;
		border: var(--bw) solid var(--line);
		border-radius: var(--radius-sm);
		background: var(--surface);
	}

	.highlighted {
		background: var(--primary-soft);
	}

	.details {
		min-width: 0;
		overflow-wrap: anywhere;
	}

	.title,
	.actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.4rem;
	}

	h2,
	h3 {
		margin: 0;
		font-size: 1rem;
		font-weight: 800;
	}

	p {
		margin: 0.3rem 0 0;
		color: var(--muted);
		font-size: 0.85rem;
	}
</style>
