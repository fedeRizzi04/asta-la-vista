<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onMount, untrack } from 'svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Tabs from '$lib/components/ui/Tabs.svelte';
	import AuctionSummary from '$lib/features/auction/AuctionSummary.svelte';
	import AuctionTiers from '$lib/features/auction/AuctionTiers.svelte';
	import CallBar from '$lib/features/auction/CallBar.svelte';
	import PlayerBrowser from '$lib/features/auction/PlayerBrowser.svelte';
	import PurchaseRegistry from '$lib/features/auction/PurchaseRegistry.svelte';
	import TeamsStrip from '$lib/features/auction/TeamsStrip.svelte';
	import { AuctionState } from '$lib/features/auction/auctionState.svelte';
	import { roleLabels, roles, type Role } from '$lib/players';
	import { getUrlParams, setUrlParams } from '$lib/urlState';

	type AuctionView = 'tiers' | 'free';

	const auctionState = new AuctionState(() => page.params.auctionId);
	const auction = $derived(auctionState.auction);
	let registryOpen = $state(false);
	const purchaseCount = $derived(auctionState.allPurchases.length);
	const purchaseCapacity = $derived(
		auction
			? auction.participants.length *
					roles.reduce((total, role) => total + auction.slot_totals[role], 0)
			: 0
	);
	const view = $derived<AuctionView>(getUrlParams().get('view') === 'free' ? 'free' : 'tiers');

	/** The role filter shared by both views: one role at a time, goalkeepers by default. */
	const role = $derived(
		roles.find((candidate) => candidate === getUrlParams().get('role')) ?? roles[0]
	);

	function setRole(next: Role): void {
		void setUrlParams({ role: next === roles[0] ? null : next });
	}

	// Calling a player of another role (from the search) shows that role's tiers.
	$effect(() => {
		const calledRole = auctionState.calledPlayer?.role;
		if (calledRole) untrack(() => setRole(calledRole));
	});

	function setView(next: AuctionView): void {
		void setUrlParams({ view: next === 'free' ? next : null });
	}

	onMount(() => auctionState.load());
</script>

<svelte:head><title>{auction?.name ?? 'Asta'} | Asta la Vista</title></svelte:head>

<PageHeader
	compact
	title={auction?.name ?? 'Asta'}
	back={{ href: resolve('/auctions'), label: 'Aste' }}
>
	{#snippet meta()}
		{#if auction}
			<span class="status-badge" data-status={auction.status}
				>{auction.status === 'draft'
					? 'Da iniziare'
					: auction.status === 'live'
						? 'In corso'
						: 'Terminata'}</span
			>
			<span class="header-summary">
				{auction.participants.length} partecipanti · {auction.initial_credits} crediti · {purchaseCount}/{purchaseCapacity}
				acquisti
			</span>
		{/if}
	{/snippet}
	{#snippet actions()}
		{#if auction && auction.status !== 'draft'}
			<Button
				variant="secondary"
				size="sm"
				aria-haspopup="dialog"
				onclick={() => (registryOpen = true)}
			>
				Registro ({purchaseCount})
			</Button>
		{/if}
		{#if auction?.status === 'draft'}
			<Button
				size="sm"
				onclick={() => auctionState.changeStatus('start')}
				disabled={auctionState.saving}
			>
				Inizia asta
			</Button>
		{:else if auction?.status === 'live'}
			<Button
				variant="secondary"
				size="sm"
				onclick={() => auctionState.undoLastPurchase()}
				disabled={auctionState.saving || purchaseCount === 0}
			>
				<span aria-hidden="true">↶</span> Annulla ultimo
			</Button>
			<Button
				variant="danger"
				size="sm"
				onclick={() => auctionState.changeStatus('complete')}
				disabled={auctionState.saving}
			>
				Termina asta
			</Button>
		{:else if auction?.status === 'completed'}
			<Button variant="secondary" size="sm" onclick={() => auctionState.downloadReport()}>
				Scarica report
			</Button>
			<Button
				size="sm"
				onclick={() => auctionState.changeStatus('reopen')}
				disabled={auctionState.saving}
			>
				Riapri asta
			</Button>
		{/if}
	{/snippet}
</PageHeader>

{#if auctionState.loading}<EmptyState>Caricamento dell'asta…</EmptyState>{/if}

{#if auction && !auctionState.loading}
	<TeamsStrip {auctionState} />

	{#if auction.status === 'live'}
		<CallBar {auctionState} />
	{:else}
		<AuctionSummary {auction} {purchaseCount} />
	{/if}

	<div class="controls">
		{#if auction.status !== 'draft'}
			<Tabs
				items={[
					{ value: 'tiers', label: 'Fasce' },
					{ value: 'free', label: 'Svincolati' }
				]}
				bind:value={() => view, setView}
				label="Vista"
				id="auction-view"
				panelId="auction-view-panel"
			/>
		{/if}
		<Tabs
			items={roles.map((value) => ({ value, label: roleLabels[value] }))}
			bind:value={() => role, setRole}
			label="Ruolo"
			id="auction-role"
			panelId="auction-view-panel"
		/>
	</div>
	<div id="auction-view-panel" role="tabpanel" tabindex="0" aria-labelledby="auction-role-{role}">
		{#if view === 'free' && auction.status !== 'draft'}
			<PlayerBrowser {auctionState} {role} />
		{:else}
			<AuctionTiers {auctionState} {role} />
		{/if}
	</div>

	<PurchaseRegistry {auctionState} bind:open={registryOpen} />
{/if}

<style>
	.header-summary {
		color: var(--muted);
		font-size: 0.875rem;
		white-space: nowrap;
	}

	.controls {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem;
		margin: 0.5rem 0 0.6rem;
	}
</style>
