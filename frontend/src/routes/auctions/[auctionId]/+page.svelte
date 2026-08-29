<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import SectionHeading from '$lib/components/SectionHeading.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import TierPlayerCard from '$lib/components/TierPlayerCard.svelte';
	import { confirmDialog } from '$lib/dialog.svelte';
	import { press } from '$lib/actions/press';
	import { pushErrorToast } from '$lib/toast.svelte';
	import {
		amendPurchase,
		cancelPurchase,
		completeAuction,
		getAuction,
		recordPurchase,
		reopenAuction,
		setAuctionStrategy,
		startAuction,
		type Auction,
		type Participant,
		type Purchase
	} from '$lib/auctions';
	import { mantraRoleLabel, sortMantraRoles } from '$lib/mantraRoles';
	import { getPlayers, type Player, type Role } from '$lib/players';
	import {
		getStrategies,
		getStrategy,
		percentageToCredits,
		type Strategy,
		type StrategySummary
	} from '$lib/strategies';

	const roleLabels: Record<Role, string> = {
		P: 'Portieri',
		D: 'Difensori',
		C: 'Centrocampisti',
		A: 'Attaccanti'
	};
	const roles = Object.keys(roleLabels) as Role[];
	type CatalogSort = 'tier' | 'quotation';

	let auction = $state<Auction>();
	let players = $state<Player[]>([]);
	let strategies = $state<StrategySummary[]>([]);
	let strategy = $state<Strategy>();
	let viewingStrategyId = $state('');
	let playerSearch = $state('');
	let selectedPlayerId = $state('');
	let selectedParticipantId = $state('');
	let price = $state(1);
	let editingPurchaseId = $state('');
	let editedParticipantId = $state('');
	let editedPrice = $state(1);
	let catalogRole = $state<Role>('P');
	let catalogMantraRoles = $state<string[]>([]);
	let catalogSort = $state<CatalogSort>('tier');
	let loading = $state(true);
	let saving = $state(false);

	let purchasedIds = $derived(new Set(auction?.purchased_player_ids ?? []));
	let matchingPlayers = $derived.by(() => {
		const query = playerSearch.trim().toLowerCase();
		return players
			.filter(
				(player) =>
					player.active &&
					!purchasedIds.has(player.id) &&
					(!query ||
						player.name.toLowerCase().includes(query) ||
						player.team.toLowerCase().includes(query))
			)
			.sort((first, second) => matchRank(first, query) - matchRank(second, query))
			.slice(0, 20);
	});
	let selectedPlayer = $derived(players.find((player) => player.id === selectedPlayerId));
	let selectedStrategyEntry = $derived(
		strategy?.entries.find((entry) => entry.player_id === selectedPlayerId)
	);
	let selectedMaximumPriceCredits = $derived(
		selectedStrategyEntry?.maximum_price_percentage != null && auction
			? percentageToCredits(selectedStrategyEntry.maximum_price_percentage, auction.initial_credits)
			: null
	);
	let selectedTier = $derived(
		strategy?.tiers.find((tier) => tier.id === selectedStrategyEntry?.tier_id)
	);
	let catalogRolePlayers = $derived(
		players.filter(
			(player) => player.role === catalogRole && (player.active || purchasedIds.has(player.id))
		)
	);
	let catalogMantraCodes = $derived(
		sortMantraRoles([...new Set(catalogRolePlayers.flatMap((player) => player.mantra_roles))])
	);
	let catalogPlayers = $derived.by(() => {
		return catalogRolePlayers
			.filter(
				(player) =>
					catalogMantraRoles.length === 0 ||
					catalogMantraRoles.some((role) => player.mantra_roles.includes(role))
			)
			.sort((first, second) => {
				if (catalogSort === 'tier' && strategy) {
					const firstPosition = tierPosition(first.id);
					const secondPosition = tierPosition(second.id);
					if (firstPosition < secondPosition) return -1;
					if (firstPosition > secondPosition) return 1;
				}
				const quotationDifference = (second.quotation ?? -1) - (first.quotation ?? -1);
				return quotationDifference || first.name.localeCompare(second.name, 'it');
			});
	});

	onMount(loadAuction);

	async function loadAuction(): Promise<void> {
		loading = true;
		try {
			[auction, players, strategies] = await Promise.all([
				getAuction(currentAuctionId()),
				getPlayers({ includeInactive: true }),
				getStrategies()
			]);
			selectedParticipantId ||= auction.participants[0]?.id ?? '';
			viewingStrategyId = auction.strategy_id ?? '';
			await loadViewedStrategy();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			loading = false;
		}
	}

	async function loadViewedStrategy(): Promise<void> {
		strategy = viewingStrategyId ? await getStrategy(viewingStrategyId) : undefined;
		if (!strategy) catalogSort = 'quotation';
	}

	async function viewSelectedStrategy(): Promise<void> {
		try {
			await loadViewedStrategy();
		} catch (caught) {
			pushErrorToast(caught);
		}
	}

	async function fixViewedStrategy(): Promise<void> {
		await runMutation(async () => {
			await setAuctionStrategy(currentAuctionId(), viewingStrategyId || null);
			await refreshAuction();
		});
	}

	async function changeStatus(action: 'start' | 'complete' | 'reopen'): Promise<void> {
		if (
			action === 'complete' &&
			!(await confirmDialog({
				title: 'Termina asta',
				message: 'Terminare questa asta? Potrai riaprirla in seguito.',
				confirmLabel: 'Termina asta'
			}))
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

	/** Ranks how closely a player matches the search query: name prefix first, then name/team substring. */
	function matchRank(player: Player, query: string): number {
		if (!query) return 0;
		const name = player.name.toLowerCase();
		if (name.startsWith(query)) return 0;
		if (name.includes(query)) return 1;
		return 2;
	}

	function selectTopMatch(): void {
		const [topMatch] = matchingPlayers;
		if (topMatch) selectPlayer(topMatch);
	}

	function handleSearchKeydown(event: KeyboardEvent): void {
		if (event.key !== 'Enter' || selectedPlayerId) return;
		event.preventDefault();
		selectTopMatch();
	}

	function callPlayerFromCatalog(player: Player): void {
		if (auction?.status !== 'live' || purchasedIds.has(player.id)) return;
		selectPlayer(player);
		document.querySelector('.call-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	function tierForPlayer(playerId: string) {
		const tierId = strategy?.entries.find((entry) => entry.player_id === playerId)?.tier_id;
		return strategy?.tiers.find((tier) => tier.id === tierId);
	}

	function tierPosition(playerId: string): number {
		return tierForPlayer(playerId)?.position ?? Number.POSITIVE_INFINITY;
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
		const confirmed = await confirmDialog({
			title: 'Annulla acquisto',
			message: `Annullare l'acquisto di ${purchase.player_name}?`,
			confirmLabel: 'Annulla acquisto',
			danger: true
		});
		if (!confirmed) return;
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
		try {
			await mutation();
		} catch (caught) {
			pushErrorToast(caught);
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
			<SectionHeading eyebrow="Calciatore chiamato" title="Registra l'acquisto">
				{#snippet trailing()}
					{#if selectedPlayer}<span class="selected-player"
							><strong>{selectedPlayer.name}</strong> · {selectedPlayer.team} · {selectedPlayer.role}
							<MantraRoleBadges
								roles={selectedPlayer.mantra_roles}
								compact
							/>{typeof selectedPlayer.quotation === 'number'
								? ` · Q. ${selectedPlayer.quotation}`
								: ''}</span
						>{/if}
				{/snippet}
			</SectionHeading>
			<form onsubmit={submitPurchase}>
				<label class="player-search"
					><span>Calciatore</span><input
						bind:value={playerSearch}
						type="search"
						placeholder="Cerca per nome o squadra"
						oninput={() => (selectedPlayerId = '')}
						onkeydown={handleSearchKeydown}
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
						{#if selectedTier}
							<TierBadge name={selectedTier.name} color={selectedTier.color} />
						{:else}
							<span class="no-tier-note">Senza fascia</span>
						{/if}
					</div>
					<div>
						<span class="strategy-label">Prezzo massimo</span>
						<strong
							>{selectedMaximumPriceCredits !== null
								? `${selectedMaximumPriceCredits} (${selectedStrategyEntry?.maximum_price_percentage}%)`
								: 'Non indicato'}</strong
						>
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
							><strong>{player.name}</strong><span
								>{player.team} · {player.role}{typeof player.quotation === 'number'
									? ` · Q. ${player.quotation}`
									: ''}
								<MantraRoleBadges roles={player.mantra_roles} compact /></span
							></button
						>{/each}
				</div>
			{/if}
		</section>
	{/if}

	<section class="teams-section">
		<SectionHeading eyebrow="Situazione squadre" title="Crediti, slot e rose" />
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
						{#each roles as role (role)}
							{@const rolePurchases = participant.purchases
								.filter((purchase) => purchase.role === role)
								.sort((first, second) => (first.created_at < second.created_at ? -1 : 1))}
							{#if rolePurchases.length > 0}
								<div class="purchase-group" data-role={role} aria-label={roleLabels[role]}>
									{#each rolePurchases as purchase (purchase.id)}
										{@const strategyEntry = strategy?.entries.find(
											(entry) => entry.player_id === purchase.player_id
										)}
										{@const purchaseTier = strategy?.tiers.find(
											(tier) => tier.id === strategyEntry?.tier_id
										)}
										<div class="purchase-row" class:editing={editingPurchaseId === purchase.id}>
											{#if editingPurchaseId === purchase.id}
												<select bind:value={editedParticipantId} aria-label="Vincitore"
													>{#each auction.participants as option (option.id)}<option
															value={option.id}>{option.name}</option
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
													><strong>{purchase.player_name}</strong><small
														>{purchase.team}
														<MantraRoleBadges roles={purchase.mantra_roles} compact /></small
													></span
												><strong class="purchase-price">{purchase.price}</strong>
												{#if purchaseTier}
													<span class="purchase-tier">
														<TierBadge
															name={purchaseTier.name}
															color={purchaseTier.color}
															compact
														/>
													</span>
												{:else}
													<span class="purchase-tier-spacer" aria-hidden="true"></span>
												{/if}
												{#if auction.status === 'live'}<button
														class="text-button"
														onclick={() => beginEdit(purchase, participant)}>Modifica</button
													><button
														class="text-button danger"
														onclick={() => deletePurchase(purchase)}>Elimina</button
													>{/if}
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						{/each}
					</div>
				</article>
			{/each}
		</div>
	</section>

	{#if strategies.length > 0}
		<section class="strategy-section">
			<SectionHeading eyebrow="Strategia" title={strategy?.name ?? 'Nessuna strategia selezionata'}>
				{#snippet trailing()}
					<div class="strategy-picker">
						<label>
							<span>Visualizza</span>
							<select bind:value={viewingStrategyId} onchange={viewSelectedStrategy}>
								<option value="">Nessuna strategia</option>
								{#each strategies as candidate (candidate.id)}
									<option value={candidate.id}>{candidate.name}</option>
								{/each}
							</select>
						</label>
						{#if viewingStrategyId !== (auction?.strategy_id ?? '')}
							<button type="button" use:press disabled={saving} onclick={fixViewedStrategy}>
								Fissa per l'asta
							</button>
						{/if}
					</div>
				{/snippet}
			</SectionHeading>
			{#if strategy}
				<div class="strategy-roles">
					{#each roles as role (role)}
						<div class="strategy-role">
							<h3>{roleLabels[role]}</h3>
							{#each [...strategy.tiers].sort((a, b) => a.position - b.position) as tier (tier.id)}
								{@const tierEntries = strategy.entries.filter(
									(entry) => entry.role === role && entry.tier_id === tier.id
								)}
								{@const availableCount = tierEntries.filter(
									(entry) => !purchasedIds.has(entry.player_id)
								).length}
								<div class="tier">
									<div class="tier-heading">
										<TierBadge name={tier.name} color={tier.color} compact />
										<span class="tier-availability">{availableCount}/{tierEntries.length}</span>
									</div>
									{#if tierEntries.length > 0}
										<div class="tier-players">
											{#each tierEntries as entry (entry.player_id)}
												<TierPlayerCard
													name={entry.name}
													team={entry.team}
													mantraRoles={entry.mantra_roles}
													maximumPricePercentage={entry.maximum_price_percentage}
													maximumPriceCredits={entry.maximum_price_percentage != null
														? percentageToCredits(
																entry.maximum_price_percentage,
																auction.initial_credits
															)
														: null}
													note={entry.note}
													purchased={purchasedIds.has(entry.player_id)}
													compact
												/>
											{/each}
										</div>
									{/if}
								</div>
							{/each}
						</div>
					{/each}
				</div>
			{/if}
		</section>
	{/if}

	{#if auction.status !== 'draft'}
		<section class="catalog-section">
			<details open>
				<summary>
					<span>
						<span class="eyebrow">Supporto alla chiamata</span>
						<strong>Calciatori</strong>
					</span>
					<small>{catalogPlayers.length} nel ruolo</small>
				</summary>
				<div class="catalog-content">
					<div class="catalog-toolbar">
						<div class="catalog-tabs-group">
							<div class="catalog-role-tabs" aria-label="Ruolo calciatori">
								{#each roles as role (role)}
									<button
										type="button"
										class:active={catalogRole === role}
										onclick={() => {
											catalogRole = role;
											catalogMantraRoles = [];
										}}
									>
										{roleLabels[role]}
									</button>
								{/each}
							</div>
							{#if catalogMantraCodes.length > 0}
								<div class="catalog-mantra-chips" aria-label="Sotto-ruolo mantra">
									<button
										type="button"
										class:active={catalogMantraRoles.length === 0}
										onclick={() => (catalogMantraRoles = [])}
									>
										Tutti
									</button>
									{#each catalogMantraCodes as code (code)}
										<button
											type="button"
											class:active={catalogMantraRoles.includes(code)}
											onclick={() => {
												catalogMantraRoles = catalogMantraRoles.includes(code)
													? catalogMantraRoles.filter((role) => role !== code)
													: [...catalogMantraRoles, code];
											}}
										>
											{mantraRoleLabel(code)}
										</button>
									{/each}
								</div>
							{/if}
						</div>
						<label>
							<span>Ordina per</span>
							<select bind:value={catalogSort}>
								{#if strategy}<option value="tier">Fascia</option>{/if}
								<option value="quotation">Quotazione</option>
							</select>
						</label>
					</div>

					<div class="catalog-grid">
						{#each catalogPlayers as player (player.id)}
							{@const playerTier = tierForPlayer(player.id)}
							<button
								type="button"
								class="catalog-player"
								class:purchased={purchasedIds.has(player.id)}
								disabled={auction.status !== 'live' || purchasedIds.has(player.id)}
								onclick={() => callPlayerFromCatalog(player)}
							>
								<span class="catalog-player-heading">
									<strong>{player.name}</strong>
									<span class="catalog-quotation">Q. {player.quotation ?? '—'}</span>
								</span>
								<span class="catalog-player-details">
									<span>{player.team}</span>
									<MantraRoleBadges roles={player.mantra_roles} compact />
									{#if playerTier}
										<TierBadge name={playerTier.name} color={playerTier.color} compact />
									{/if}
								</span>
								{#if purchasedIds.has(player.id)}<span class="purchased-label">Acquistato</span
									>{/if}
							</button>
						{/each}
					</div>
				</div>
			</details>
		</section>
	{/if}
{/if}

<style>
	.back-link {
		display: inline-block;
		margin-bottom: 1.5rem;
		color: var(--muted);
		font-size: 0.84rem;
		font-weight: 650;
	}
	.auction-heading,
	.status-actions,
	.team-card header,
	.slots,
	.slot-summary {
		display: flex;
		align-items: center;
	}
	.auction-heading,
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
		background: var(--live-bg);
		color: var(--live-text);
		font-size: 0.72rem;
		font-weight: 750;
	}
	.status-actions > span[data-status='completed'] {
		background: var(--completed-bg);
		color: var(--completed-text);
	}
	.team-card {
		container-type: inline-size;
		container-name: team-card;
		border: 1px solid var(--border);
		border-radius: 0.7rem;
		background: var(--surface);
	}
	.panel {
		margin-top: 2rem;
	}
	button {
		min-height: 2.5rem;
		padding: 0 0.9rem;
		border: 1px solid var(--primary);
		border-radius: 0.42rem;
		background: var(--primary);
		color: var(--on-primary);
		font: inherit;
		font-size: 0.82rem;
		font-weight: 700;
		cursor: pointer;
	}
	button.secondary {
		border-color: var(--border-strong);
		background: var(--input-bg);
		color: var(--text);
	}
	button:disabled {
		cursor: not-allowed;
		opacity: 0.45;
	}
	.draft-summary h2 {
		margin: 0;
	}
	.draft-summary p {
		color: var(--subdued);
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
		background: var(--muted-bg);
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
		border: 1px solid var(--border-strong);
		border-radius: 0.4rem;
		background: var(--input-bg);
		color: inherit;
		font: inherit;
	}
	.selected-player {
		padding: 0.5rem 0.7rem;
		border-radius: 0.4rem;
		background: var(--primary-soft);
		color: var(--primary-soft-text);
		font-size: 0.82rem;
	}
	.called-player-strategy {
		display: grid;
		grid-template-columns: minmax(140px, 0.6fr) minmax(140px, 0.5fr) minmax(220px, 1.5fr);
		gap: 0.7rem;
		margin-top: 0.8rem;
		padding: 0.8rem;
		border: 1px solid var(--border);
		border-radius: 0.45rem;
		background: var(--input-bg);
	}
	.called-player-strategy > div {
		display: grid;
		align-content: start;
		gap: 0.25rem;
	}
	.strategy-label {
		color: var(--subdued);
		font-size: 0.68rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.called-player-strategy strong {
		font-size: 0.82rem;
	}
	.no-tier-note {
		color: var(--subdued);
		font-size: 0.82rem;
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
		border-color: var(--border);
		background: var(--input-bg);
		color: var(--text);
		text-align: left;
	}
	.search-results span {
		color: var(--subdued);
		font-size: 0.72rem;
	}
	.teams-section,
	.strategy-section {
		margin-top: 3rem;
	}
	.strategy-picker {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	.strategy-picker label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		font-weight: 700;
		white-space: nowrap;
	}
	.strategy-picker select {
		width: auto;
		min-width: 9rem;
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
		color: var(--subdued);
		font-size: 0.7rem;
	}
	.maximum-bid {
		margin: 0.7rem 0;
		padding: 0.6rem;
		border-radius: 0.4rem;
		background: var(--primary-soft);
		color: var(--primary-soft-text);
		font-size: 0.78rem;
	}
	.slots span.full {
		background: var(--muted-bg);
		color: var(--disabled-text);
	}
	.roster {
		display: grid;
		gap: 0.9rem;
		margin-top: 0.8rem;
	}
	.roster > p {
		color: var(--subdued);
		font-size: 0.8rem;
	}
	.purchase-group {
		padding: 0.25rem 0.45rem;
		border: 1px solid var(--border-strong);
		border-radius: 0.55rem;
	}
	.purchase-group[data-role='P'] {
		background: var(--goalkeeper-bg);
	}
	.purchase-group[data-role='D'] {
		background: var(--defender-bg);
	}
	.purchase-group[data-role='C'] {
		background: var(--midfielder-bg);
	}
	.purchase-group[data-role='A'] {
		background: var(--forward-bg);
	}
	.purchase-row {
		display: grid;
		grid-template-columns: 1.5rem minmax(60px, 1fr) 2.5rem minmax(4.5rem, 8rem) auto auto;
		align-items: center;
		gap: 0.45rem;
		min-height: 2.25rem;
		border-top: 1px solid var(--border);
		font-size: 0.78rem;
	}
	.purchase-group .purchase-row:first-child {
		border-top: 0;
	}
	.purchase-row.editing {
		grid-template-columns: minmax(100px, 1fr) 4rem auto auto;
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
		background: var(--muted-bg);
		font-weight: 800;
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
	/* A team card can end up narrower than the tier badge needs, regardless of viewport size
	   (e.g. many participants forcing extra grid columns) — reflow the badge onto its own row
	   whenever the card itself is tight, not just when the whole page is. */
	@container team-card (max-width: 380px) {
		.purchase-row {
			grid-template-columns: 1.5rem minmax(60px, 1fr) 2.5rem auto auto;
		}
		.purchase-tier {
			grid-row: 2;
			grid-column: 2 / 4;
			justify-self: start;
		}
		.purchase-tier-spacer {
			display: none;
		}
	}
	.text-button {
		min-height: auto;
		padding: 0.2rem;
		border: 0;
		background: transparent;
		color: var(--primary-text);
		font-size: 0.7rem;
	}
	.text-button.danger {
		color: var(--error-text);
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
		margin-bottom: 0.4rem;
		border: 1px solid var(--border);
		border-radius: 0.45rem;
		background: var(--surface);
	}
	.tier-heading {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.4rem;
		padding: 0.35rem 0.45rem;
	}
	.tier-availability {
		flex: 0 0 auto;
		color: var(--subdued);
		font-size: 0.68rem;
		font-variant-numeric: tabular-nums;
	}
	.tier-players {
		display: grid;
		gap: 0.35rem;
		padding: 0 0.45rem 0.45rem;
	}
	.catalog-section {
		margin-top: 3rem;
	}
	.catalog-section details {
		border: 1px solid var(--border);
		border-radius: 0.7rem;
		background: var(--surface);
	}
	.catalog-section summary {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 1rem 1.2rem;
		cursor: pointer;
	}
	.catalog-section summary > span {
		display: grid;
		gap: 0.2rem;
	}
	.catalog-section summary .eyebrow {
		margin: 0;
		font-size: 0.65rem;
	}
	.catalog-section summary strong {
		font-size: 1.1rem;
	}
	.catalog-section summary small {
		color: var(--subdued);
	}
	.catalog-content {
		padding: 1rem 1.2rem 1.2rem;
		border-top: 1px solid var(--border);
	}
	.catalog-toolbar,
	.catalog-role-tabs,
	.catalog-mantra-chips {
		display: flex;
		align-items: center;
	}
	.catalog-toolbar {
		justify-content: space-between;
		gap: 1rem;
	}
	.catalog-tabs-group {
		display: grid;
		gap: 0.5rem;
	}
	.catalog-role-tabs,
	.catalog-mantra-chips {
		flex-wrap: wrap;
		gap: 0.35rem;
	}
	.catalog-role-tabs button,
	.catalog-mantra-chips button {
		min-height: 2.2rem;
		border-color: var(--border-strong);
		background: var(--input-bg);
		color: var(--text);
	}
	.catalog-role-tabs button.active,
	.catalog-mantra-chips button.active {
		border-color: var(--primary);
		background: var(--primary);
		color: var(--on-primary);
	}
	.catalog-mantra-chips button {
		min-height: 1.85rem;
		padding: 0 0.6rem;
		font-size: 0.72rem;
	}
	.catalog-toolbar label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		font-weight: 700;
		white-space: nowrap;
	}
	.catalog-toolbar label span {
		margin: 0;
	}
	.catalog-toolbar select {
		width: auto;
		min-width: 9rem;
	}
	.catalog-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
		gap: 0.5rem;
		margin-top: 1rem;
	}
	.catalog-player {
		display: grid;
		gap: 0.35rem;
		min-width: 0;
		height: auto;
		padding: 0.7rem;
		border-color: var(--border);
		background: var(--input-bg);
		color: var(--text);
		text-align: left;
	}
	.catalog-player:disabled {
		cursor: default;
		opacity: 1;
	}
	.catalog-player:not(:disabled):hover {
		border-color: var(--primary-text);
	}
	.catalog-player-heading,
	.catalog-player-details {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.6rem;
		min-width: 0;
	}
	.catalog-player-heading > strong {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.catalog-quotation {
		flex: 0 0 auto;
		font-variant-numeric: tabular-nums;
	}
	.catalog-player-details {
		color: var(--subdued);
		font-size: 0.68rem;
	}
	.catalog-player.purchased {
		background: var(--muted-bg);
		color: var(--disabled-text);
	}
	.catalog-player.purchased :global(.tier-badge-accent) {
		filter: grayscale(1);
		opacity: 0.5;
	}
	.purchased-label {
		justify-self: end;
		padding: 0.1rem 0.25rem;
		border-radius: 0.2rem;
		background: var(--muted-bg);
		font-size: 0.58rem;
		text-transform: uppercase;
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
		.auction-heading {
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
		.catalog-toolbar {
			align-items: stretch;
			flex-direction: column;
		}
		.catalog-toolbar label {
			justify-content: space-between;
		}
		.catalog-toolbar select {
			flex: 1;
		}
	}
</style>
