<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import {
		amendPurchase,
		cancelPurchase,
		completeAuction,
		getAuction,
		recordPurchase,
		reopenAuction,
		startAuction,
		type Auction,
		type Participant,
		type Purchase
	} from '$lib/auctions';
	import { getPlayers, type Player, type Role } from '$lib/players';
	import { getStrategy, type Strategy } from '$lib/strategies';

	const roleLabels: Record<Role, string> = {
		P: 'Portieri',
		D: 'Difensori',
		C: 'Centrocampisti',
		A: 'Attaccanti'
	};
	const roles = Object.keys(roleLabels) as Role[];

	let auction = $state<Auction>();
	let players = $state<Player[]>([]);
	let strategy = $state<Strategy>();
	let playerSearch = $state('');
	let selectedPlayerId = $state('');
	let selectedParticipantId = $state('');
	let price = $state(1);
	let editingPurchaseId = $state('');
	let editedParticipantId = $state('');
	let editedPrice = $state(1);
	let loading = $state(true);
	let saving = $state(false);
	let error = $state('');

	let purchasedIds = $derived(new Set(auction?.purchased_player_ids ?? []));
	let matchingPlayers = $derived(
		players
			.filter((player) => {
				const query = playerSearch.trim().toLowerCase();
				return (
					player.active &&
					!purchasedIds.has(player.id) &&
					(!query ||
						player.name.toLowerCase().includes(query) ||
						player.team.toLowerCase().includes(query))
				);
			})
			.slice(0, 20)
	);
	let selectedPlayer = $derived(players.find((player) => player.id === selectedPlayerId));
	let selectedStrategyEntry = $derived(
		strategy?.entries.find((entry) => entry.player_id === selectedPlayerId)
	);
	let selectedTier = $derived(
		strategy?.tiers.find((tier) => tier.id === selectedStrategyEntry?.tier_id)
	);

	onMount(loadAuction);

	async function loadAuction(): Promise<void> {
		loading = true;
		error = '';
		try {
			[auction, players] = await Promise.all([getAuction(currentAuctionId()), getPlayers()]);
			selectedParticipantId ||= auction.participants[0]?.id ?? '';
			strategy = auction.strategy_id ? await getStrategy(auction.strategy_id) : undefined;
		} catch (caught) {
			error = errorMessage(caught);
		} finally {
			loading = false;
		}
	}

	async function changeStatus(action: 'start' | 'complete' | 'reopen'): Promise<void> {
		if (
			action === 'complete' &&
			!window.confirm('Terminare questa asta? Potrai riaprirla in seguito.')
		)
			return;
		await runMutation(async () => {
			if (action === 'start') await startAuction(currentAuctionId());
			if (action === 'complete') await completeAuction(currentAuctionId());
			if (action === 'reopen') await reopenAuction(currentAuctionId());
			await refreshAuction();
		});
	}

	async function submitPurchase(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!selectedPlayerId || !selectedParticipantId) return;
		await runMutation(async () => {
			await recordPurchase(currentAuctionId(), selectedPlayerId, selectedParticipantId, price);
			selectedPlayerId = '';
			playerSearch = '';
			price = 1;
			await refreshAuction();
		});
	}

	function selectPlayer(player: Player): void {
		selectedPlayerId = player.id;
		playerSearch = player.name;
	}

	function beginEdit(purchase: Purchase, participant: Participant): void {
		editingPurchaseId = purchase.id;
		editedParticipantId = participant.id;
		editedPrice = purchase.price;
	}

	async function savePurchase(purchaseId: string): Promise<void> {
		await runMutation(async () => {
			await amendPurchase(currentAuctionId(), purchaseId, editedParticipantId, editedPrice);
			editingPurchaseId = '';
			await refreshAuction();
		});
	}

	async function deletePurchase(purchase: Purchase): Promise<void> {
		if (!window.confirm(`Annullare l'acquisto di ${purchase.player_name}?`)) return;
		await runMutation(async () => {
			await cancelPurchase(currentAuctionId(), purchase.id);
			await refreshAuction();
		});
	}

	async function refreshAuction(): Promise<void> {
		auction = await getAuction(currentAuctionId());
	}

	async function runMutation(mutation: () => Promise<void>): Promise<void> {
		saving = true;
		error = '';
		try {
			await mutation();
		} catch (caught) {
			error = errorMessage(caught);
		} finally {
			saving = false;
		}
	}

	function currentAuctionId(): string {
		const auctionId = page.params.auctionId;
		if (!auctionId) throw new Error('Asta non trovata.');
		return auctionId;
	}

	function downloadReport(): void {
		window.location.assign(`/api/auctions/${currentAuctionId()}/report`);
	}

	function errorMessage(caught: unknown): string {
		return caught instanceof Error ? caught.message : 'Si è verificato un errore inatteso.';
	}
</script>

<svelte:head><title>{auction?.name ?? 'Asta'} | Asta la Vista</title></svelte:head>

<a class="back-link" href={resolve('/auctions')}>Torna alle aste</a>

<header class="auction-heading">
	<div>
		<p class="eyebrow">Asta Classic</p>
		<h1>{auction?.name ?? 'Asta'}</h1>
	</div>
	{#if auction}
		<div class="status-actions">
			<span data-status={auction.status}
				>{auction.status === 'draft'
					? 'Da iniziare'
					: auction.status === 'live'
						? 'In corso'
						: 'Terminata'}</span
			>
			{#if auction.status === 'draft'}<button
					onclick={() => changeStatus('start')}
					disabled={saving}>Inizia asta</button
				>{/if}
			{#if auction.status === 'live'}<button
					class="secondary"
					onclick={() => changeStatus('complete')}
					disabled={saving}>Termina asta</button
				>{/if}
			{#if auction.status === 'completed'}
				<button onclick={() => changeStatus('reopen')} disabled={saving}>Riapri asta</button>
				<button class="secondary" onclick={downloadReport}>Scarica report</button>
			{/if}
		</div>
	{/if}
</header>

{#if error}<div class="message" role="alert">{error}</div>{/if}
{#if loading}<div class="empty-state">Caricamento dell'asta…</div>{/if}

{#if auction && !loading}
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
		<section class="call-panel panel">
			<div class="section-heading">
				<div>
					<p class="eyebrow">Calciatore chiamato</p>
					<h2>Registra l'acquisto</h2>
				</div>
				{#if selectedPlayer}<span class="selected-player"
						><strong>{selectedPlayer.name}</strong> · {selectedPlayer.team} · {selectedPlayer.role}</span
					>{/if}
			</div>
			<form onsubmit={submitPurchase}>
				<label class="player-search"
					><span>Calciatore</span><input
						bind:value={playerSearch}
						type="search"
						placeholder="Cerca per nome o squadra"
						oninput={() => (selectedPlayerId = '')}
					/></label
				>
				<label
					><span>Vincitore</span><select bind:value={selectedParticipantId}
						>{#each auction.participants as participant (participant.id)}<option
								value={participant.id}>{participant.name} · max {participant.maximum_bid}</option
							>{/each}</select
					></label
				>
				<label><span>Prezzo</span><input bind:value={price} type="number" min="1" required /></label
				>
				<button type="submit" disabled={!selectedPlayerId || !selectedParticipantId || saving}
					>Registra</button
				>
			</form>
			{#if selectedPlayer && strategy}
				<div class="called-player-strategy">
					<div>
						<span class="strategy-label">Fascia</span>
						<strong class="called-tier" style:--tier-color={selectedTier?.color ?? '#d8ded9'}
							><span></span>{selectedTier?.name ?? 'Senza fascia'}</strong
						>
					</div>
					<div>
						<span class="strategy-label">Prezzo massimo</span>
						<strong>{selectedStrategyEntry?.maximum_price ?? 'Non indicato'}</strong>
					</div>
					<div class="called-note">
						<span class="strategy-label">Note</span>
						<strong>{selectedStrategyEntry?.note || 'Nessuna nota'}</strong>
					</div>
				</div>
			{/if}
			{#if playerSearch && !selectedPlayerId}
				<div class="search-results">
					{#each matchingPlayers as player (player.id)}<button
							type="button"
							onclick={() => selectPlayer(player)}
							><strong>{player.name}</strong><span>{player.team} · {player.role}</span></button
						>{/each}
				</div>
			{/if}
		</section>
	{/if}

	<section class="teams-section">
		<div class="section-heading">
			<div>
				<p class="eyebrow">Situazione squadre</p>
				<h2>Crediti, slot e rose</h2>
			</div>
		</div>
		<div class="team-grid">
			{#each auction.participants as participant (participant.id)}
				<article class="team-card">
					<header>
						<h3>{participant.name}</h3>
						<div><strong>{participant.credits_remaining}</strong><span>crediti</span></div>
					</header>
					<div class="maximum-bid">Puntata massima <strong>{participant.maximum_bid}</strong></div>
					<div class="slots">
						{#each roles as role (role)}<span
								class:full={participant.slots[role].filled === participant.slots[role].total}
								><strong>{role}</strong>
								{participant.slots[role].filled}/{participant.slots[role].total}</span
							>{/each}
					</div>
					<div class="roster">
						{#if participant.purchases.length === 0}<p>Nessun acquisto.</p>{/if}
						{#each participant.purchases as purchase (purchase.id)}
							<div class="purchase-row">
								{#if editingPurchaseId === purchase.id}
									<select bind:value={editedParticipantId} aria-label="Vincitore"
										>{#each auction.participants as option (option.id)}<option value={option.id}
												>{option.name}</option
											>{/each}</select
									>
									<input bind:value={editedPrice} type="number" min="1" aria-label="Prezzo" />
									<button
										class="text-button"
										onclick={() => savePurchase(purchase.id)}
										disabled={saving}>Salva</button
									><button class="text-button" onclick={() => (editingPurchaseId = '')}
										>Annulla</button
									>
								{:else}
									<span class="role-badge">{purchase.role}</span><span class="purchase-name"
										><strong>{purchase.player_name}</strong><small>{purchase.team}</small></span
									><strong>{purchase.price}</strong>
									{#if auction.status === 'live'}<button
											class="text-button"
											onclick={() => beginEdit(purchase, participant)}>Modifica</button
										><button class="text-button danger" onclick={() => deletePurchase(purchase)}
											>Elimina</button
										>{/if}
								{/if}
							</div>
						{/each}
					</div>
				</article>
			{/each}
		</div>
	</section>

	{#if strategy}
		<section class="strategy-section">
			<div class="section-heading">
				<div>
					<p class="eyebrow">Strategia</p>
					<h2>{strategy.name}</h2>
				</div>
			</div>
			<div class="strategy-roles">
				{#each roles as role (role)}
					<div class="strategy-role">
						<h3>{roleLabels[role]}</h3>
						{#each [...strategy.tiers].sort((a, b) => a.position - b.position) as tier (tier.id)}
							<div class="tier" style:--tier-color={tier.color ?? '#d8ded9'}>
								<h4>{tier.name}</h4>
								<div>
									{#each strategy.entries.filter((entry) => entry.role === role && entry.tier_id === tier.id) as entry (entry.player_id)}<span
											class:purchased={purchasedIds.has(entry.player_id)}
											><strong>{entry.name}</strong><small
												>{entry.team}{entry.maximum_price !== null
													? ` · max ${entry.maximum_price}`
													: ''}{entry.note ? ` · ${entry.note}` : ''}</small
											></span
										>{/each}
								</div>
							</div>
						{/each}
					</div>
				{/each}
			</div>
		</section>
	{/if}
{/if}

<style>
	.back-link {
		display: inline-block;
		margin-bottom: 1.5rem;
		color: #526057;
		font-size: 0.84rem;
		font-weight: 650;
	}
	.auction-heading,
	.status-actions,
	.section-heading,
	.team-card header,
	.slots,
	.slot-summary {
		display: flex;
		align-items: center;
	}
	.auction-heading,
	.section-heading,
	.team-card header {
		justify-content: space-between;
	}
	.auction-heading {
		gap: 2rem;
	}
	.auction-heading h1 {
		margin: 0;
		font-size: clamp(2rem, 4vw, 3.5rem);
		letter-spacing: -0.045em;
	}
	.status-actions {
		gap: 0.7rem;
	}
	.status-actions > span {
		padding: 0.35rem 0.65rem;
		border-radius: 999px;
		background: #dcebe1;
		color: #24583b;
		font-size: 0.72rem;
		font-weight: 750;
	}
	.status-actions > span[data-status='completed'] {
		background: #e1e3e2;
		color: #555c58;
	}
	.panel,
	.team-card {
		border: 1px solid #d9ddd7;
		border-radius: 0.7rem;
		background: #fafbf8;
	}
	.panel {
		margin-top: 2rem;
		padding: 1.25rem;
	}
	.message {
		margin-top: 1.5rem;
		padding: 0.85rem 1rem;
		border: 1px solid #d4a7a7;
		border-radius: 0.5rem;
		background: #fff7f7;
		color: #7a2727;
		font-size: 0.9rem;
	}
	button {
		min-height: 2.5rem;
		padding: 0 0.9rem;
		border: 1px solid #204c39;
		border-radius: 0.42rem;
		background: #204c39;
		color: #fff;
		font: inherit;
		font-size: 0.82rem;
		font-weight: 700;
		cursor: pointer;
	}
	button.secondary {
		border-color: #bdc5bf;
		background: #fff;
		color: #344039;
	}
	button:disabled {
		cursor: not-allowed;
		opacity: 0.45;
	}
	.draft-summary h2,
	.section-heading h2 {
		margin: 0;
	}
	.draft-summary p {
		color: #667069;
	}
	.slot-summary,
	.slots {
		flex-wrap: wrap;
		gap: 0.45rem;
	}
	.slot-summary span,
	.slots span {
		padding: 0.35rem 0.55rem;
		border-radius: 0.35rem;
		background: #edf0ec;
		font-size: 0.76rem;
	}
	.call-panel form {
		display: grid;
		grid-template-columns: minmax(260px, 1.4fr) minmax(210px, 1fr) 110px auto;
		align-items: end;
		gap: 0.75rem;
		margin-top: 1rem;
	}
	label > span {
		display: block;
		margin-bottom: 0.35rem;
		font-size: 0.74rem;
		font-weight: 700;
	}
	input,
	select {
		width: 100%;
		height: 2.5rem;
		padding: 0 0.65rem;
		border: 1px solid #bdc5bf;
		border-radius: 0.4rem;
		background: #fff;
		color: inherit;
		font: inherit;
	}
	.selected-player {
		padding: 0.5rem 0.7rem;
		border-radius: 0.4rem;
		background: #edf3ef;
		color: #315641;
		font-size: 0.82rem;
	}
	.called-player-strategy {
		display: grid;
		grid-template-columns: minmax(140px, 0.6fr) minmax(140px, 0.5fr) minmax(220px, 1.5fr);
		gap: 0.7rem;
		margin-top: 0.8rem;
		padding: 0.8rem;
		border: 1px solid #d9ddd7;
		border-radius: 0.45rem;
		background: #fff;
	}
	.called-player-strategy > div {
		display: grid;
		align-content: start;
		gap: 0.25rem;
	}
	.strategy-label {
		color: #707971;
		font-size: 0.68rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.called-player-strategy strong {
		font-size: 0.82rem;
	}
	.called-tier {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}
	.called-tier span {
		width: 0.7rem;
		height: 0.7rem;
		border: 1px solid rgb(0 0 0 / 12%);
		border-radius: 50%;
		background: var(--tier-color);
	}
	.search-results {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0.45rem;
		margin-top: 0.7rem;
	}
	.search-results button {
		display: grid;
		justify-items: start;
		gap: 0.2rem;
		height: auto;
		padding: 0.6rem;
		border-color: #d9ddd7;
		background: #fff;
		color: #26322b;
		text-align: left;
	}
	.search-results span {
		color: #6a736c;
		font-size: 0.72rem;
	}
	.teams-section,
	.strategy-section {
		margin-top: 3rem;
	}
	.section-heading .eyebrow {
		margin-bottom: 0.5rem;
	}
	.team-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 0.8rem;
		margin-top: 1rem;
	}
	.team-card {
		padding: 1rem;
	}
	.team-card h3 {
		margin: 0;
	}
	.team-card header div {
		display: grid;
		justify-items: end;
	}
	.team-card header div strong {
		font-size: 1.6rem;
	}
	.team-card header div span {
		color: #69736c;
		font-size: 0.7rem;
	}
	.maximum-bid {
		margin: 0.7rem 0;
		padding: 0.6rem;
		border-radius: 0.4rem;
		background: #edf3ef;
		color: #375544;
		font-size: 0.78rem;
	}
	.slots span.full {
		background: #e2e3e1;
		color: #8a908c;
	}
	.roster {
		margin-top: 0.8rem;
	}
	.roster > p {
		color: #777f79;
		font-size: 0.8rem;
	}
	.purchase-row {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		min-height: 2.25rem;
		border-top: 1px solid #e2e5e1;
		font-size: 0.78rem;
	}
	.purchase-row input,
	.purchase-row select {
		height: 2rem;
	}
	.role-badge {
		display: grid;
		place-items: center;
		width: 1.5rem;
		height: 1.5rem;
		border-radius: 0.3rem;
		background: #e4e8e4;
		font-weight: 800;
	}
	.purchase-name {
		display: grid;
		flex: 1;
	}
	.purchase-name small {
		color: #747c76;
	}
	.text-button {
		min-height: auto;
		padding: 0.2rem;
		border: 0;
		background: transparent;
		color: #315e48;
		font-size: 0.7rem;
	}
	.text-button.danger {
		color: #8b3434;
	}
	.strategy-roles {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0.7rem;
		margin-top: 1rem;
	}
	.strategy-role h3 {
		font-size: 0.9rem;
	}
	.tier {
		margin-bottom: 0.6rem;
		border: 1px solid #dde1dd;
		border-left: 4px solid var(--tier-color);
		border-radius: 0.45rem;
		background: #fafbf8;
	}
	.tier h4 {
		margin: 0;
		padding: 0.5rem 0.65rem;
		border-bottom: 1px solid #e3e6e2;
		font-size: 0.78rem;
	}
	.tier > div {
		display: grid;
	}
	.tier span {
		display: grid;
		padding: 0.45rem 0.65rem;
		border-bottom: 1px solid #eceeeb;
		font-size: 0.74rem;
	}
	.tier span:last-child {
		border-bottom: 0;
	}
	.tier span small {
		color: #747c76;
	}
	.tier span.purchased {
		color: #969b97;
		background: #eeefed;
		text-decoration: line-through;
	}
	@media (max-width: 950px) {
		.call-panel form,
		.strategy-roles {
			grid-template-columns: 1fr 1fr;
		}
		.search-results {
			grid-template-columns: repeat(2, 1fr);
		}
	}
	@media (max-width: 620px) {
		.auction-heading,
		.section-heading {
			align-items: stretch;
			flex-direction: column;
		}
		.status-actions {
			flex-wrap: wrap;
		}
		.call-panel form,
		.called-player-strategy,
		.strategy-roles,
		.search-results {
			grid-template-columns: 1fr;
		}
		.team-grid {
			grid-template-columns: 1fr;
		}
		.purchase-row {
			flex-wrap: wrap;
		}
	}
</style>
