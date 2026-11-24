<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Dialog from '$lib/components/ui/Dialog.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import Tabs from '$lib/components/ui/Tabs.svelte';
	import ToggleChip from '$lib/components/ui/ToggleChip.svelte';
	import AuctionTiers from '$lib/features/auction/AuctionTiers.svelte';
	import CallBar from '$lib/features/auction/CallBar.svelte';
	import PlayerBrowser from '$lib/features/auction/PlayerBrowser.svelte';
	import TeamsStrip from '$lib/features/auction/TeamsStrip.svelte';
	import { AuctionState } from '$lib/features/auction/auctionState.svelte';
	import { roleLabels, roles, type Role } from '$lib/players';
	import { getUrlParams, setUrlParams } from '$lib/urlState';

	type AuctionView = 'tiers' | 'free';

	const auctionState = new AuctionState(() => page.params.auctionId);
	const auction = $derived(auctionState.auction);
	const view = $derived<AuctionView>(getUrlParams().get('view') === 'free' ? 'free' : 'tiers');

	/** The role filter of both views: no role selected means all of them. */
	const selectedRoles = $derived.by(() => {
		const selected = getUrlParams().getAll('roles');
		return roles.filter((role) => selected.includes(role));
	});
	const shownRoles = $derived(selectedRoles.length > 0 ? selectedRoles : roles);

	function toggleRole(toggled: Role): void {
		const next = roles.filter((role) => selectedRoles.includes(role) !== (role === toggled));
		void setUrlParams({ roles: next });
	}

	function setView(next: AuctionView): void {
		void setUrlParams({ view: next === 'free' ? next : null });
	}

	onMount(() => auctionState.load());
</script>

<svelte:head><title>{auction?.name ?? 'Asta'} | Asta la Vista</title></svelte:head>

<PageHeader title={auction?.name ?? 'Asta'} back={{ href: resolve('/auctions'), label: 'Aste' }}>
	{#snippet meta()}
		{#if auction}
			<span class="status-badge" data-status={auction.status}
				>{auction.status === 'draft'
					? 'Da iniziare'
					: auction.status === 'live'
						? 'In corso'
						: 'Terminata'}</span
			>
		{/if}
	{/snippet}
	{#snippet actions()}
		{#if auction?.status === 'draft'}
			<Button onclick={() => auctionState.changeStatus('start')} disabled={auctionState.saving}
				>Inizia asta</Button
			>
		{:else if auction?.status === 'live'}
			<Button
				variant="secondary"
				onclick={() => auctionState.changeStatus('complete')}
				disabled={auctionState.saving}
			>
				Termina asta
			</Button>
		{:else if auction?.status === 'completed'}
			<Button onclick={() => auctionState.changeStatus('reopen')} disabled={auctionState.saving}
				>Riapri asta</Button
			>
			<Button variant="secondary" onclick={() => auctionState.downloadReport()}
				>Scarica report</Button
			>
		{/if}
	{/snippet}
</PageHeader>

{#if auctionState.loading}<EmptyState>Caricamento dell'asta…</EmptyState>{/if}

{#if auction && !auctionState.loading}
	{#if auction.status === 'draft'}
		<section class="draft-summary panel">
			<h2>Configurazione</h2>
			<p>{auction.participants.length} partecipanti · {auction.initial_credits} crediti a testa</p>
			<div class="slot-summary">
				{#each roles as role (role)}<span
						><strong>{role}</strong> {auction.slot_totals[role]} slot</span
					>{/each}
			</div>
			<ul>
				{#each auction.participants as participant (participant.id)}<li>
						{participant.name}
					</li>{/each}
			</ul>
		</section>
	{:else if auction.status === 'live'}
		<div class="registry-trigger-row">
			<Button onclick={() => (auctionState.registryOpen = true)}>
				Apri registro acquisti{auctionState.allPurchases.length > 0
					? ` (${auctionState.allPurchases.length})`
					: ''}
			</Button>
		</div>
	{/if}

	<TeamsStrip {auctionState} />

	{#if auction.status === 'live'}<CallBar {auctionState} />{/if}

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
		<div class="role-filter" role="group" aria-label="Ruoli">
			<ToggleChip
				pressed={selectedRoles.length === 0}
				onclick={() => void setUrlParams({ roles: null })}
			>
				Tutti
			</ToggleChip>
			{#each roles as role (role)}
				<ToggleChip pressed={selectedRoles.includes(role)} onclick={() => toggleRole(role)}>
					{roleLabels[role]}
				</ToggleChip>
			{/each}
		</div>
	</div>
	{#if auction.status === 'draft'}
		<AuctionTiers {auctionState} roles={shownRoles} />
	{:else}
		<div id="auction-view-panel" role="tabpanel" tabindex="0" aria-labelledby="auction-view-{view}">
			{#if view === 'free'}
				<PlayerBrowser {auctionState} roles={shownRoles} />
			{:else}
				<AuctionTiers {auctionState} roles={shownRoles} />
			{/if}
		</div>
	{/if}

	<Dialog
		bind:open={auctionState.registryOpen}
		title="Registro acquisti"
		width="760px"
		closeLabel="Chiudi"
		onclose={() => auctionState.resetRegistry()}
	>
		<Field label="Cerca calciatore">
			<Input
				bind:value={auctionState.registrySearch}
				type="search"
				placeholder="Nome del calciatore"
				data-autofocus
			/>
		</Field>
		{#if auctionState.allPurchases.length === 0}
			<p class="registry-empty">Nessun acquisto registrato.</p>
		{:else if auctionState.filteredRegistryPurchases.length === 0}
			<p class="registry-empty">Nessun calciatore corrisponde alla ricerca.</p>
		{:else}
			<div class="registry-list">
				{#each auctionState.filteredRegistryPurchases as { purchase, participant } (purchase.id)}
					{@const purchaseTier = auctionState.tierForPlayer(purchase.player_id)}
					<div
						class="purchase-row registry-row"
						class:editing={auctionState.editingPurchaseId === purchase.id}
					>
						{#if auctionState.editingPurchaseId === purchase.id}
							<Select bind:value={auctionState.editedParticipantId} aria-label="Vincitore">
								{#each auction.participants as option (option.id)}
									<option value={option.id}>{option.name}</option>
								{/each}
							</Select>
							<Input
								bind:value={auctionState.editedPrice}
								type="number"
								min="1"
								aria-label="Prezzo"
							/>
							<Button
								variant="text"
								size="sm"
								onclick={() => auctionState.savePurchase(purchase.id)}
								disabled={auctionState.saving}>Salva</Button
							>
							<Button
								variant="text"
								size="sm"
								onclick={() => (auctionState.editingPurchaseId = '')}
							>
								Annulla
							</Button>
						{:else}
							<span class="role-badge" data-role={purchase.role}>{purchase.role}</span><span
								class="purchase-name"
								><strong>{purchase.player_name}</strong><small
									>{purchase.team}
									<MantraRoleBadges roles={purchase.mantra_roles} compact /></small
								></span
							><strong class="purchase-price">{purchase.price}</strong>
							{#if purchaseTier}
								<span class="purchase-tier">
									<TierBadge name={purchaseTier.name} color={purchaseTier.color} compact />
								</span>
							{:else}
								<span class="purchase-tier-spacer" aria-hidden="true"></span>
							{/if}
							<span class="registry-participant">{participant.name}</span>
							<Button
								variant="text"
								size="sm"
								onclick={() => auctionState.beginEdit(purchase, participant)}
							>
								Modifica
							</Button>
							<Button
								variant="danger"
								size="sm"
								onclick={() => auctionState.deletePurchase(purchase)}
							>
								Elimina
							</Button>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</Dialog>
{/if}

<style>
	.slot-summary {
		display: flex;
		align-items: center;
	}
	.panel {
		margin-top: 2rem;
	}
	.draft-summary h2 {
		margin: 0;
	}
	.draft-summary p {
		color: var(--subdued);
	}
	.slot-summary {
		flex-wrap: wrap;
		gap: 0.45rem;
	}
	.slot-summary span {
		padding: 0.35rem 0.55rem;
		border-radius: var(--radius-xs);
		background: var(--muted-bg);
		font-size: 0.76rem;
	}
	.purchase-row {
		display: grid;
		grid-template-columns: 1.5rem minmax(60px, 1fr) 2.5rem minmax(4.5rem, 8rem);
		align-items: center;
		gap: 0.45rem;
		min-height: 2.25rem;
		border-top: 1px solid var(--border);
		font-size: 0.78rem;
	}
	.purchase-row.editing {
		grid-template-columns: minmax(100px, 1fr) 4rem auto auto;
	}
	.purchase-row.registry-row:not(.editing) {
		grid-template-columns:
			1.5rem minmax(60px, 1fr) 2.5rem minmax(4.5rem, 7rem) minmax(70px, 8rem) auto
			auto;
	}
	.registry-participant {
		overflow: hidden;
		font-weight: 700;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.purchase-row :global(input),
	.purchase-row :global(select) {
		min-height: 2rem;
	}
	.purchase-name {
		display: grid;
		flex: 1;
	}
	.purchase-name small {
		color: var(--subdued);
	}
	.purchase-price {
		justify-self: end;
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	.purchase-tier {
		min-width: 0;
	}
	.purchase-tier :global(.tier-badge) {
		max-width: 100%;
	}
	.controls,
	.role-filter {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
	}
	.controls {
		gap: 0.75rem;
		margin: 0.5rem 0 0.6rem;
	}
	.registry-trigger-row {
		margin-bottom: 0.6rem;
	}

	.registry-empty {
		margin: 0;
		color: var(--subdued);
		font-size: 0.85rem;
	}
	.registry-list {
		display: grid;
		align-content: start;
		gap: 0;
		min-height: 0;
		overflow-y: auto;
		overflow-x: auto;
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
	}
	.registry-row {
		min-width: 34rem;
		padding: 0 0.6rem;
	}
	.registry-list .registry-row:first-child {
		border-top: 0;
	}
</style>
