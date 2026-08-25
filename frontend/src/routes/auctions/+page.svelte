<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import {
		createAuction,
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
	let error = $state('');

	onMount(loadPage);

	async function loadPage(): Promise<void> {
		loading = true;
		error = '';
		try {
			[auctions, strategies] = await Promise.all([getAuctions(), getStrategies()]);
		} catch (caught) {
			error = errorMessage(caught);
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
		error = '';
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
			error = errorMessage(caught);
		} finally {
			saving = false;
		}
	}

	function errorMessage(caught: unknown): string {
		return caught instanceof Error ? caught.message : 'Si è verificato un errore inatteso.';
	}
</script>

<svelte:head>
	<title>Aste | Asta la Vista</title>
</svelte:head>

<section class="page-heading">
	<p class="eyebrow">Gestione aste</p>
	<h1>Aste</h1>
	<p>Crea una nuova asta Classic oppure riprendi rapidamente quella in corso.</p>
</section>

{#if error}
	<div class="message" role="alert">{error}</div>
{/if}

<div class="page-grid">
	<section class="panel">
		<div class="section-heading">
			<h2>Nuova asta</h2>
			<p>Tutti i partecipanti avranno gli stessi crediti e slot.</p>
		</div>

		<form class="auction-form" onsubmit={submitAuction}>
			<label class="wide">
				<span>Nome asta</span>
				<input bind:value={name} placeholder="Ad esempio: Lega amici" required />
			</label>
			<label>
				<span>Crediti</span>
				<input bind:value={initialCredits} type="number" min="1" required />
			</label>
			<label>
				<span>Portieri</span>
				<input bind:value={goalkeeperSlots} type="number" min="0" required />
			</label>
			<label>
				<span>Difensori</span>
				<input bind:value={defenderSlots} type="number" min="0" required />
			</label>
			<label>
				<span>Centrocampisti</span>
				<input bind:value={midfielderSlots} type="number" min="0" required />
			</label>
			<label>
				<span>Attaccanti</span>
				<input bind:value={forwardSlots} type="number" min="0" required />
			</label>
			<label class="wide">
				<span>Strategia</span>
				<select bind:value={strategyId}>
					<option value="">Nessuna strategia</option>
					{#each strategies as strategy (strategy.id)}
						<option value={strategy.id}>{strategy.name}</option>
					{/each}
				</select>
			</label>
			<label class="wide">
				<span>Partecipanti, uno per riga</span>
				<textarea
					bind:value={participantNames}
					rows="7"
					placeholder="Alice&#10;Bob&#10;Carlo"
					required></textarea>
			</label>
			<button
				class="wide"
				type="submit"
				disabled={saving || !name.trim() || !participantNames.trim()}
			>
				{saving ? 'Creazione…' : 'Crea asta'}
			</button>
		</form>
	</section>

	<section class="auction-section">
		<div class="list-heading">
			<h2>Aste salvate</h2>
			<span>{loading ? 'Caricamento…' : `${auctions.length} aste`}</span>
		</div>

		{#if !loading && auctions.length === 0}
			<div class="empty-state">Non ci sono ancora aste salvate.</div>
		{:else}
			<div class="auction-list">
				{#each auctions as auction (auction.id)}
					<a href={resolve('/auctions/[auctionId]', { auctionId: auction.id })}>
						<div class="auction-title">
							<h3>{auction.name}</h3>
							<span data-status={auction.status}>{statusLabels[auction.status]}</span>
						</div>
						<p>{auction.participant_count} partecipanti · {auction.purchase_count} acquisti</p>
						<strong>{auction.initial_credits} crediti iniziali</strong>
					</a>
				{/each}
			</div>
		{/if}
	</section>
</div>

<style>
	.message {
		margin-top: 1.5rem;
		padding: 0.85rem 1rem;
		border: 1px solid #d4a7a7;
		border-radius: 0.5rem;
		background: #fff7f7;
		color: #7a2727;
		font-size: 0.9rem;
	}

	.page-grid {
		display: grid;
		grid-template-columns: minmax(360px, 0.8fr) minmax(420px, 1.2fr);
		align-items: start;
		gap: 2rem;
		margin-top: 3rem;
	}

	.panel {
		padding: 1.25rem;
		border: 1px solid #d9ddd7;
		border-radius: 0.7rem;
		background: #fafbf8;
	}

	.section-heading h2,
	.section-heading p,
	.list-heading h2 {
		margin: 0;
	}

	.section-heading h2,
	.list-heading h2 {
		font-size: 1.15rem;
	}

	.section-heading p {
		margin-top: 0.35rem;
		color: #667069;
		font-size: 0.8rem;
	}

	.auction-form {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.85rem;
		margin-top: 1.25rem;
	}

	.wide {
		grid-column: 1 / -1;
	}

	label span {
		display: block;
		margin-bottom: 0.4rem;
		font-size: 0.76rem;
		font-weight: 700;
	}

	input,
	select,
	textarea {
		width: 100%;
		padding: 0.65rem 0.7rem;
		border: 1px solid #bdc5bf;
		border-radius: 0.4rem;
		background: #fff;
		color: inherit;
		font: inherit;
	}

	input,
	select {
		height: 2.5rem;
	}

	textarea {
		resize: vertical;
		line-height: 1.45;
	}

	button {
		min-height: 2.65rem;
		border: 1px solid #204c39;
		border-radius: 0.45rem;
		background: #204c39;
		color: #fff;
		font: inherit;
		font-size: 0.86rem;
		font-weight: 700;
		cursor: pointer;
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.5;
	}

	.list-heading,
	.auction-title {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.list-heading {
		margin-bottom: 0.8rem;
	}

	.list-heading > span {
		color: #667069;
		font-size: 0.8rem;
	}

	.auction-list {
		display: grid;
		gap: 0.7rem;
	}

	.auction-list > a {
		padding: 1.15rem;
		border: 1px solid #d9ddd7;
		border-radius: 0.65rem;
		background: #fafbf8;
		text-decoration: none;
		transition: border-color 140ms ease;
	}

	.auction-list > a:hover {
		border-color: #94a098;
	}

	.auction-title h3 {
		margin: 0;
		font-size: 1rem;
	}

	.auction-title span {
		padding: 0.25rem 0.5rem;
		border-radius: 999px;
		background: #e5e8e4;
		color: #5e665f;
		font-size: 0.7rem;
		font-weight: 750;
	}

	.auction-title span[data-status='live'] {
		background: #dcebe1;
		color: #24583b;
	}

	.auction-title span[data-status='completed'] {
		background: #e1e3e2;
		color: #555c58;
	}

	.auction-list p {
		margin: 0.8rem 0 0.35rem;
		color: #667069;
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

		.wide {
			grid-column: auto;
		}
	}
</style>
