<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import SectionHeading from '$lib/components/SectionHeading.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import { confirmDialog } from '$lib/dialog.svelte';
	import { pushErrorToast } from '$lib/toast.svelte';
	import {
		createAuction,
		deleteAuction,
		getAuctions,
		type AuctionStatus,
		type AuctionSummary
	} from '$lib/auctions';
	import { getStrategies, type StrategySummary } from '$lib/strategies';

	const statusLabels: Record<AuctionStatus, string> = {
		draft: 'Da iniziare',
		live: 'In corso',
		completed: 'Terminata'
	};

	let auctions = $state<AuctionSummary[]>([]);
	let strategies = $state<StrategySummary[]>([]);
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
		if (!name.trim() || participants.length === 0) return;
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

<PageHeader title="Aste" />

<div class="page-grid">
	<section class="panel">
		<SectionHeading
			title="Nuova asta"
			subtitle="Tutti i partecipanti avranno gli stessi crediti e slot."
		/>

		<form class="auction-form" onsubmit={submitAuction}>
			<Field label="Nome asta" class="wide">
				<Input bind:value={name} placeholder="Ad esempio: Lega amici" required />
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
					rows="7"
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
	</section>

	<section class="auction-section">
		<SectionHeading title="Aste salvate">
			{#snippet trailing()}
				<span class="count-label">{loading ? 'Caricamento…' : `${auctions.length} aste`}</span>
			{/snippet}
		</SectionHeading>

		{#if !loading && auctions.length === 0}
			<EmptyState>Non ci sono ancora aste salvate.</EmptyState>
		{:else}
			<div class="auction-list">
				{#each auctions as auction (auction.id)}
					<article>
						<div>
							<div class="auction-title">
								<h3>{auction.name}</h3>
								<span class="status-badge" data-status={auction.status}
									>{statusLabels[auction.status]}</span
								>
							</div>
							<p>{auction.participant_count} partecipanti · {auction.purchase_count} acquisti</p>
							<strong>{auction.initial_credits} crediti iniziali</strong>
						</div>
						<div class="actions">
							<Button variant="danger" onclick={() => removeAuction(auction)} disabled={saving}>
								Elimina
							</Button>
							<Button href={resolve('/auctions/[auctionId]', { auctionId: auction.id })}
								>Apri</Button
							>
						</div>
					</article>
				{/each}
			</div>
		{/if}
	</section>
</div>

<style>
	.page-grid {
		display: grid;
		grid-template-columns: minmax(360px, 0.8fr) minmax(420px, 1.2fr);
		align-items: start;
		gap: 2rem;
		margin-top: 1.5rem;
	}

	.auction-form {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.85rem;
		margin-top: 1.25rem;
	}

	.auction-form :global(.wide) {
		grid-column: 1 / -1;
	}

	.auction-title {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.auction-list {
		display: grid;
		gap: 0.7rem;
	}

	.auction-list article {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1.5rem;
		padding: 1.15rem;
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		background: var(--surface);
		transition: border-color 140ms ease;
	}

	.auction-list article:hover {
		border-color: var(--border-hover);
	}

	.actions {
		display: flex;
		flex-shrink: 0;
		gap: 0.65rem;
	}

	.auction-title h3 {
		margin: 0;
		font-size: 1rem;
	}

	.auction-list p {
		margin: 0.8rem 0 0.35rem;
		color: var(--subdued);
		font-size: 0.82rem;
	}

	.auction-list strong {
		font-size: 0.78rem;
	}

	@media (max-width: 900px) {
		.page-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 520px) {
		.auction-form {
			grid-template-columns: 1fr;
		}

		.auction-form :global(.wide) {
			grid-column: auto;
		}

		.auction-list article {
			align-items: stretch;
			flex-direction: column;
		}

		.actions > :global(*) {
			flex: 1;
		}
	}
</style>
