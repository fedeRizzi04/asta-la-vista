<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Dialog from '$lib/components/ui/Dialog.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import { confirmDialog } from '$lib/dialog.svelte';
	import { pushErrorToast } from '$lib/toast.svelte';
	import { createAuction, deleteAuction, getAuctions, type AuctionSummary } from '$lib/auctions';
	import AuctionCard from '$lib/features/auction/AuctionCard.svelte';
	import { getStrategies, type StrategySummary } from '$lib/strategies';

	let auctions = $state<AuctionSummary[]>();
	let strategies = $state<StrategySummary[]>([]);
	let createOpen = $state(false);
	let name = $state('');
	let initialCredits = $state(500);
	let goalkeeperSlots = $state(3);
	let defenderSlots = $state(8);
	let midfielderSlots = $state(8);
	let forwardSlots = $state(6);
	let participantNames = $state('');
	let strategyId = $state('');
	let loading = $state(true);
	let saving = $state(false);

	const orderedAuctions = $derived(
		auctions && [
			...auctions.filter((auction) => auction.status === 'live'),
			...auctions.filter((auction) => auction.status !== 'live')
		]
	);

	onMount(loadPage);

	async function loadPage(): Promise<void> {
		loading = true;
		try {
			[auctions, strategies] = await Promise.all([getAuctions(), getStrategies()]);
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			loading = false;
		}
	}

	async function submitAuction(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		const participants = participantNames
			.split('\n')
			.map((participant) => participant.trim())
			.filter(Boolean);
		if (saving || !name.trim() || participants.length === 0) return;
		saving = true;
		try {
			const result = await createAuction({
				name: name.trim(),
				initial_credits: initialCredits,
				goalkeeper_slots: goalkeeperSlots,
				defender_slots: defenderSlots,
				midfielder_slots: midfielderSlots,
				forward_slots: forwardSlots,
				participant_names: participants,
				strategy_id: strategyId || null
			});
			createOpen = false;
			await goto(resolve('/auctions/[auctionId]', { auctionId: result.id }));
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			saving = false;
		}
	}

	async function removeAuction(auction: AuctionSummary): Promise<void> {
		const confirmed = await confirmDialog({
			title: 'Elimina asta',
			message: `Eliminare l'asta “${auction.name}”? Questa azione non può essere annullata.`,
			confirmLabel: 'Elimina',
			danger: true
		});
		if (!confirmed) return;
		saving = true;
		try {
			await deleteAuction(auction.id);
			await loadPage();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Aste | Asta la Vista</title>
</svelte:head>

<PageHeader title="Aste" compact>
	{#snippet actions()}
		<Button size="sm" aria-haspopup="dialog" onclick={() => (createOpen = true)} disabled={saving}>
			Nuova asta
		</Button>
	{/snippet}
</PageHeader>

<Dialog bind:open={createOpen} title="Nuova asta" width="34rem" closeLabel="Chiudi">
	<form class="auction-form" onsubmit={submitAuction}>
		<Field label="Nome asta" class="wide">
			<Input bind:value={name} placeholder="Ad esempio: Lega amici" required data-autofocus />
		</Field>
		<Field label="Crediti">
			<Input bind:value={initialCredits} type="number" min="1" required />
		</Field>
		<Field label="Portieri">
			<Input bind:value={goalkeeperSlots} type="number" min="0" required />
		</Field>
		<Field label="Difensori">
			<Input bind:value={defenderSlots} type="number" min="0" required />
		</Field>
		<Field label="Centrocampisti">
			<Input bind:value={midfielderSlots} type="number" min="0" required />
		</Field>
		<Field label="Attaccanti">
			<Input bind:value={forwardSlots} type="number" min="0" required />
		</Field>
		<Field label="Strategia predefinita" class="wide">
			<Select bind:value={strategyId}>
				<option value="">Nessuna strategia</option>
				{#each strategies as strategy (strategy.id)}
					<option value={strategy.id}>{strategy.name}</option>
				{/each}
			</Select>
		</Field>
		<Field label="Partecipanti, uno per riga" class="wide">
			<textarea
				class="control"
				bind:value={participantNames}
				rows="5"
				placeholder="Alice&#10;Bob&#10;Carlo"
				required></textarea>
		</Field>
		<Button
			class="wide"
			type="submit"
			loading={saving}
			disabled={!name.trim() || !participantNames.trim()}
		>
			Crea asta
		</Button>
	</form>
</Dialog>

<div aria-busy={loading}>
	{#if loading}
		<p class="count-label">Caricamento…</p>
	{:else if !orderedAuctions}
		<EmptyState>Impossibile caricare le aste.</EmptyState>
	{:else if orderedAuctions.length === 0}
		<EmptyState>Nessuna asta salvata. Per iniziare, scegli «Nuova asta».</EmptyState>
	{:else}
		<div class="auction-list">
			{#each orderedAuctions as auction (auction.id)}
				<AuctionCard {auction} highlighted={auction.status === 'live'}>
					{#snippet actions()}
						<Button
							variant="danger"
							size="sm"
							aria-label={`Elimina ${auction.name}`}
							onclick={() => removeAuction(auction)}
							disabled={saving}
						>
							Elimina
						</Button>
					{/snippet}
				</AuctionCard>
			{/each}
		</div>
	{/if}
</div>

<style>
	.auction-form {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.85rem;
	}

	.auction-form :global(.wide) {
		grid-column: 1 / -1;
	}

	.auction-list {
		display: grid;
		gap: 0.65rem;
	}

	@media (max-width: 520px) {
		.auction-form {
			grid-template-columns: 1fr;
		}
	}
</style>
