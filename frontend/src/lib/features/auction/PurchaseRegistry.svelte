<script lang="ts">
	import type { Participant, Purchase } from '$lib/auctions';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Drawer from '$lib/components/ui/Drawer.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import { t } from '$lib/i18n';
	import { matchesSearch } from '$lib/search';
	import { tick } from 'svelte';
	import type { AuctionState } from './auctionState.svelte';

	let { auctionState, open = $bindable(false) }: { auctionState: AuctionState; open?: boolean } =
		$props();

	const focusId = $props.id();
	let search = $state('');
	let editing = $state<{ purchaseId: string; participantId: string; price: number | undefined }>();
	const canEdit = $derived(auctionState.auction?.status === 'live');
	const filteredPurchases = $derived(
		auctionState.allPurchases
			.map((record, index, purchases) => ({ ...record, number: purchases.length - index }))
			.filter(({ purchase }) => matchesSearch(search, purchase.player_name))
	);

	// Not the Drawer's `onclose`, which skips the closes the parent asks for (the shortcut).
	$effect(() => {
		if (open) return;
		search = '';
		editing = undefined;
	});

	async function beginEdit(purchase: Purchase, participant: Participant): Promise<void> {
		editing = { purchaseId: purchase.id, participantId: participant.id, price: purchase.price };
		await tick();
		document.getElementById(`${focusId}-winner`)?.focus();
	}

	async function endEdit(): Promise<void> {
		const purchaseId = editing?.purchaseId;
		editing = undefined;
		await tick();
		document.getElementById(`${focusId}-edit-${purchaseId}`)?.focus();
	}

	async function saveEdit(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		const draft = editing;
		if (draft?.price === undefined) return;
		const saved = await auctionState.savePurchase(
			draft.purchaseId,
			draft.participantId,
			draft.price
		);
		if (saved && editing === draft) await endEdit();
	}
</script>

<Drawer bind:open title={t.auction.purchaseRegistry} width="640px">
	<Input
		bind:value={search}
		type="search"
		placeholder={t.auction.searchPlayer}
		aria-label={t.auction.searchPlayer}
		data-autofocus
	/>
	{#if filteredPurchases.length === 0}
		<p class="empty">
			{auctionState.allPurchases.length === 0
				? t.auction.noPurchasesRecorded
				: t.auction.noPlayersMatchSearch}
		</p>
	{:else}
		<ol>
			{#each filteredPurchases as { purchase, participant, number } (purchase.id)}
				{@const tier = auctionState.tierForPlayer(purchase.player_id)}
				{@const draft = canEdit && editing?.purchaseId === purchase.id ? editing : undefined}
				<li class:editing={!!draft}>
					<span class="index">#{number}</span>
					<span class="role-badge" data-role={purchase.role}>{purchase.role}</span>
					<span class="player">
						<strong>{purchase.player_name}</strong>
						<small>{purchase.team} <MantraRoleBadges roles={purchase.mantra_roles} compact /></small
						>
					</span>
					{#if tier}
						<span class="tier"><TierBadge name={tier.name} color={tier.color} compact /></span>
					{/if}
					<span class="winner">{participant.name}</span>
					<strong class="price">{purchase.price}</strong>
					{#if draft}
						<form onsubmit={saveEdit}>
							<Select
								id={`${focusId}-winner`}
								bind:value={draft.participantId}
								aria-label={t.auction.winner}
								disabled={auctionState.saving}
							>
								{#each auctionState.auction?.participants ?? [] as option (option.id)}
									<option value={option.id}>{option.name}</option>
								{/each}
							</Select>
							<Input
								bind:value={draft.price}
								type="number"
								min="1"
								required
								aria-label={t.auction.price}
								disabled={auctionState.saving}
							/>
							<div class="edit-actions">
								<Button type="submit" size="sm" disabled={auctionState.saving}
									>{t.auction.save}</Button
								>
								<Button variant="text" size="sm" onclick={endEdit} disabled={auctionState.saving}>
									{t.common.cancel}
								</Button>
							</div>
						</form>
					{:else if canEdit}
						<div class="actions">
							<Button
								id={`${focusId}-edit-${purchase.id}`}
								variant="text"
								size="sm"
								aria-label={t.auction.editPurchaseLabel(purchase.player_name)}
								title={t.auction.editWinnerAndPrice}
								disabled={auctionState.saving}
								onclick={() => beginEdit(purchase, participant)}>✎</Button
							>
							<Button
								variant="text"
								class="delete"
								size="sm"
								aria-label={t.auction.deletePurchaseLabel(purchase.player_name)}
								title={t.auction.deletePurchase}
								disabled={auctionState.saving}
								onclick={() => auctionState.deletePurchase(purchase)}>×</Button
							>
						</div>
					{/if}
				</li>
			{/each}
		</ol>
	{/if}
</Drawer>

<style>
	.empty,
	.index,
	small {
		color: var(--muted);
	}

	.empty,
	ol {
		margin: 0;
	}

	ol {
		padding: 0;
		list-style: none;
	}

	li {
		display: grid;
		grid-template:
			'index role player tier winner price actions' auto /
			2.25rem 1.5rem minmax(0, 1.5fr) minmax(0, 0.9fr) minmax(0, 1fr) auto auto;
		align-items: center;
		gap: 0.4rem;
		padding: 0.3rem;
		border-bottom: 1px solid var(--border);
		font-size: 0.85rem;
		overflow-wrap: anywhere;
	}

	li.editing {
		border-radius: var(--radius-sm);
		background: var(--selected-bg);
	}

	.index {
		grid-area: index;
		font-size: 0.75rem;
	}

	.role-badge {
		grid-area: role;
	}

	.player {
		grid-area: player;
	}

	.tier {
		grid-area: tier;
	}

	.winner {
		grid-area: winner;
	}

	.price {
		grid-area: price;
		text-align: right;
	}

	.index,
	.price {
		font-variant-numeric: tabular-nums;
	}

	.actions,
	.edit-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.15rem;
	}

	.actions {
		grid-area: actions;
	}

	.actions :global(.delete) {
		color: var(--danger);
	}

	form {
		display: grid;
		grid-column: 3 / -1;
		grid-template-columns: minmax(0, 1fr) 5rem auto;
		align-items: center;
		gap: 0.4rem;
	}

	@media (max-width: 36rem) {
		li {
			grid-template:
				'index role player price actions' auto
				'. tier tier winner winner' auto /
				2rem 1.5rem minmax(0, 1fr) auto auto;
		}

		.winner {
			text-align: right;
		}

		form {
			grid-column: 1 / -1;
			grid-template-columns: minmax(0, 1fr) 5rem;
		}

		.edit-actions {
			grid-column: 1 / -1;
		}
	}
</style>
