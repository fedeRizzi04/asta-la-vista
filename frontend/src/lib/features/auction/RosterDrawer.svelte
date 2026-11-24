<script lang="ts">
	import { purchasesForRole, type Participant } from '$lib/auctions';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import Drawer from '$lib/components/ui/Drawer.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import { roleLabels, roles } from '$lib/players';
	import type { AuctionState } from './auctionState.svelte';

	let {
		auctionState,
		participant,
		onclose
	}: { auctionState: AuctionState; participant: Participant; onclose: () => void } = $props();
</script>

<Drawer open title={participant.name} {onclose}>
	<p class="budget">
		<span><strong>{participant.credits_remaining}</strong> crediti residui</span>
		<span>max <strong>{participant.maximum_bid}</strong></span>
	</p>
	{#if participant.purchases.length === 0}
		<EmptyState compact>Nessun acquisto.</EmptyState>
	{:else}
		{#each roles as role (role)}
			{@const purchases = purchasesForRole(participant, role)}
			{#if purchases.length > 0}
				<section>
					<h3>{roleLabels[role]}</h3>
					<ul>
						{#each purchases as purchase (purchase.id)}
							{@const tier = auctionState.tierForPlayer(purchase.player_id)}
							<li>
								<span class="role-badge" data-role={role}>{role}</span>
								<span class="player">
									<strong>{purchase.player_name}</strong>
									<small
										>{purchase.team}
										<MantraRoleBadges roles={purchase.mantra_roles} compact /></small
									>
								</span>
								<span class="purchase">
									<strong>{purchase.price} cr</strong>
									{#if tier}<TierBadge name={tier.name} color={tier.color} compact />{/if}
								</span>
							</li>
						{/each}
					</ul>
				</section>
			{/if}
		{/each}
	{/if}
</Drawer>

<style>
	.budget {
		display: flex;
		flex-wrap: wrap;
		column-gap: 1rem;
		margin: 0;
		color: var(--muted);
		font-size: 0.875rem;
		font-variant-numeric: tabular-nums;
	}
	.budget strong {
		color: var(--text);
	}
	h3 {
		margin: 0 0 0.2rem;
		font-size: 0.9rem;
	}
	ul {
		margin: 0;
		padding: 0;
		list-style: none;
	}
	li {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) fit-content(35%);
		align-items: center;
		gap: 0.45rem;
		padding: 0.35rem 0;
		border-top: 1px solid var(--border);
		font-size: 0.85rem;
		overflow-wrap: anywhere;
	}
	.player,
	.purchase {
		display: grid;
		min-width: 0;
	}
	.player small {
		color: var(--subdued);
	}
	.purchase {
		justify-items: end;
		font-variant-numeric: tabular-nums;
	}
</style>
