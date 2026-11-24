<script lang="ts">
	import type { Auction } from '$lib/auctions';
	import { roleLabels, roles } from '$lib/players';

	let { auction, purchaseCount }: { auction: Auction; purchaseCount: number } = $props();
</script>

<section class="panel summary" aria-labelledby="auction-summary-title">
	{#if auction.status === 'draft'}
		<h2 id="auction-summary-title">Configurazione</h2>
		<span
			>{auction.participants.length} partecipanti · {auction.initial_credits} crediti a testa</span
		>
		<div class="slots">
			<span>Slot</span>
			{#each roles as role (role)}
				<span><strong title={roleLabels[role]}>{role}</strong> {auction.slot_totals[role]}</span>
			{/each}
		</div>
	{:else}
		<h2 id="auction-summary-title">Asta terminata</h2>
		<span
			>{purchaseCount} {purchaseCount === 1 ? 'acquisto registrato' : 'acquisti registrati'}</span
		>
		<span class="hint">Sola lettura: per correggere qualcosa usa «Riapri asta».</span>
	{/if}
</section>

<style>
	.summary,
	.slots {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.35rem 0.8rem;
	}

	.summary {
		margin-top: 1rem;
		padding: 0.65rem 0.8rem;
		font-size: 0.9rem;
	}

	h2 {
		margin: 0;
		font-size: 1.05rem;
	}

	.slots,
	.hint {
		color: var(--muted);
	}
</style>
