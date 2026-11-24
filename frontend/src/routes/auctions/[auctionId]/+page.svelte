<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import CollapsibleSection from '$lib/components/CollapsibleSection.svelte';
	import HorizontalScroller from '$lib/components/HorizontalScroller.svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import SectionHeading from '$lib/components/SectionHeading.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import TierPlayerCard from '$lib/components/TierPlayerCard.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Dialog from '$lib/components/ui/Dialog.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import Tabs from '$lib/components/ui/Tabs.svelte';
	import ToggleChip from '$lib/components/ui/ToggleChip.svelte';
	import { purchasesForRole } from '$lib/auctions';
	import { AuctionState } from '$lib/features/auction/auctionState.svelte';
	import { mantraRoleLabel } from '$lib/mantraRoles';
	import { roleLabels, roles } from '$lib/players';

	const roleTabs = roles.map((role) => ({ value: role, label: roleLabels[role] }));
	const auctionState = new AuctionState(() => page.params.auctionId);
	const auction = $derived(auctionState.auction);
	let callPanel = $state<HTMLElement>();

	onMount(() => auctionState.load());

	function submitPurchase(event: SubmitEvent): void {
		event.preventDefault();
		void auctionState.registerPurchase();
	}

	function handleSearchKeydown(event: KeyboardEvent): void {
		if (event.key !== 'Enter' || auctionState.selectedPlayerId) return;
		event.preventDefault();
		auctionState.selectTopMatch();
	}

	function callPlayer(playerId: string): void {
		if (auctionState.callPlayer(playerId)) {
			callPanel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	}
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
		<section class="call-panel panel" bind:this={callPanel}>
			<SectionHeading eyebrow="Calciatore chiamato" title="Registra l'acquisto">
				{#snippet trailing()}
					{@const selectedPlayer = auctionState.selectedPlayer}
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
				<Field label="Calciatore">
					<Input
						bind:value={auctionState.playerSearch}
						type="search"
						placeholder="Cerca per nome o squadra"
						oninput={() => (auctionState.selectedPlayerId = '')}
						onkeydown={handleSearchKeydown}
					/>
				</Field>
				<Field label="Vincitore">
					<Select bind:value={auctionState.selectedParticipantId}>
						{#each auction.participants as participant (participant.id)}
							<option value={participant.id}
								>{participant.name} · max {participant.maximum_bid}</option
							>
						{/each}
					</Select>
				</Field>
				<Field label="Prezzo">
					<Input bind:value={auctionState.price} type="number" min="1" required />
				</Field>
				<Button
					type="submit"
					disabled={!auctionState.selectedPlayerId ||
						!auctionState.selectedParticipantId ||
						auctionState.saving}
				>
					Registra
				</Button>
			</form>
			{#if auctionState.selectedPlayer && auctionState.viewedStrategy}
				{@const selectedTier = auctionState.selectedTier}
				{@const selectedStrategyEntry = auctionState.selectedStrategyEntry}
				{@const selectedMaximumPriceCredits = auctionState.selectedMaximumPriceCredits}
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
			{#if auctionState.playerSearch && !auctionState.selectedPlayerId}
				<div class="search-results">
					{#each auctionState.matchingPlayers as player (player.id)}<button
							type="button"
							onclick={() => auctionState.selectPlayer(player)}
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
		<CollapsibleSection
			storageKey={`auction:${auction.id}:teams`}
			eyebrow="Situazione squadre"
			title="Crediti, slot e rose"
		>
			<HorizontalScroller ariaLabel="Rose dei partecipanti">
				<div class="team-grid">
					{#each auction.participants as participant (participant.id)}
						<article class="team-card">
							<header>
								<h3>{participant.name}</h3>
								<div><strong>{participant.credits_remaining}</strong><span>crediti</span></div>
							</header>
							<div class="maximum-bid">
								Puntata massima <strong>{participant.maximum_bid}</strong>
							</div>
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
									{@const rolePurchases = purchasesForRole(participant, role)}
									{#if rolePurchases.length > 0}
										<div class="purchase-group" data-role={role} aria-label={roleLabels[role]}>
											{#each rolePurchases as purchase (purchase.id)}
												{@const purchaseTier = auctionState.tierForPlayer(purchase.player_id)}
												<div class="purchase-row">
													<span class="role-badge" data-role={purchase.role}>{purchase.role}</span
													><span class="purchase-name"
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
												</div>
											{/each}
										</div>
									{/if}
								{/each}
							</div>
						</article>
					{/each}
				</div>
			</HorizontalScroller>
		</CollapsibleSection>
	</section>

	{#if auctionState.strategies.length > 0}
		<section class="strategy-section">
			<CollapsibleSection
				storageKey={`auction:${auction.id}:strategy`}
				eyebrow="Strategia"
				title={auctionState.viewedStrategy?.name ?? 'Nessuna strategia selezionata'}
			>
				{#snippet trailing()}
					<div class="strategy-picker">
						<Field label="Visualizza" inline>
							<Select
								bind:value={auctionState.viewingStrategyId}
								onchange={() => auctionState.viewSelectedStrategy()}
							>
								<option value="">Nessuna strategia</option>
								{#each auctionState.strategies as candidate (candidate.id)}
									<option value={candidate.id}>{candidate.name}</option>
								{/each}
							</Select>
						</Field>
						{#if auctionState.viewingStrategyId !== (auction?.strategy_id ?? '')}
							<Button
								disabled={auctionState.saving}
								onclick={() => auctionState.fixViewedStrategy()}>Fissa per l'asta</Button
							>
						{/if}
					</div>
				{/snippet}
				{#if auctionState.viewedStrategy}
					<Tabs
						items={roleTabs}
						bind:value={auctionState.strategyRole}
						label="Ruolo strategia"
						id="strategy-role"
						panelId="strategy-role-panel"
					/>
					<div
						id="strategy-role-panel"
						role="tabpanel"
						tabindex="0"
						aria-labelledby="strategy-role-{auctionState.strategyRole}"
					>
						<HorizontalScroller
							ariaLabel={`Fasce della strategia per ${roleLabels[auctionState.strategyRole]}`}
						>
							<div class="strategy-roles">
								{#each auctionState.strategyRoleTiers as { tier, entries, availableCount } (tier.id)}
									<div class="tier">
										<div class="tier-heading">
											<TierBadge name={tier.name} color={tier.color} compact />
											<span class="tier-availability">{availableCount}/{entries.length}</span>
										</div>
										{#if entries.length > 0}
											<div class="tier-players">
												{#each entries as entry (entry.player_id)}
													<button
														type="button"
														class="tier-player-button"
														disabled={auction.status !== 'live' ||
															auctionState.purchasedIds.has(entry.player_id)}
														onclick={() => callPlayer(entry.player_id)}
													>
														<TierPlayerCard
															name={entry.name}
															team={entry.team}
															mantraRoles={entry.mantra_roles}
															maximumPricePercentage={entry.maximum_price_percentage}
															maximumPriceCredits={auctionState.maximumPriceCredits(
																entry.maximum_price_percentage
															)}
															note={entry.note}
															purchased={auctionState.purchasedIds.has(entry.player_id)}
															compact
														/>
													</button>
												{/each}
											</div>
										{/if}
									</div>
								{/each}
							</div>
						</HorizontalScroller>
					</div>
				{/if}
			</CollapsibleSection>
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
					<small>{auctionState.catalogPlayers.length} nel ruolo</small>
				</summary>
				<div class="catalog-content">
					<div class="catalog-toolbar">
						<div class="catalog-tabs-group">
							<Tabs
								items={roleTabs}
								bind:value={auctionState.catalogRole}
								label="Ruolo calciatori"
								id="catalog-role"
								panelId="catalog-role-panel"
								onchange={() => (auctionState.catalogMantraRoles = [])}
							/>
							{#if auctionState.catalogMantraCodes.length > 0}
								<div class="catalog-mantra-chips" role="group" aria-label="Sotto-ruolo mantra">
									<ToggleChip
										pressed={auctionState.catalogMantraRoles.length === 0}
										onclick={() => (auctionState.catalogMantraRoles = [])}
									>
										Tutti
									</ToggleChip>
									{#each auctionState.catalogMantraCodes as code (code)}
										<ToggleChip
											pressed={auctionState.catalogMantraRoles.includes(code)}
											onclick={() => auctionState.toggleCatalogMantraRole(code)}
										>
											{mantraRoleLabel(code)}
										</ToggleChip>
									{/each}
								</div>
							{/if}
						</div>
						<Field label="Ordina per" inline>
							<Select bind:value={auctionState.catalogSort}>
								{#if auctionState.viewedStrategy}<option value="tier">Fascia</option>{/if}
								<option value="quotation">Quotazione</option>
							</Select>
						</Field>
					</div>

					<div
						class="catalog-grid"
						id="catalog-role-panel"
						role="tabpanel"
						tabindex="0"
						aria-labelledby="catalog-role-{auctionState.catalogRole}"
					>
						{#each auctionState.catalogPlayers as player (player.id)}
							{@const playerTier = auctionState.tierForPlayer(player.id)}
							<button
								type="button"
								class="catalog-player"
								class:purchased={auctionState.purchasedIds.has(player.id)}
								disabled={auction.status !== 'live' || auctionState.purchasedIds.has(player.id)}
								onclick={() => callPlayer(player.id)}
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
								{#if auctionState.purchasedIds.has(player.id)}<span class="purchased-label"
										>Acquistato</span
									>{/if}
							</button>
						{/each}
					</div>
				</div>
			</details>
		</section>
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
	.team-card header,
	.slots,
	.slot-summary {
		display: flex;
		align-items: center;
	}
	.team-card header {
		justify-content: space-between;
	}
	.team-card {
		container-type: inline-size;
		container-name: team-card;
		border: var(--bw) solid var(--line);
		border-radius: var(--radius);
		background: var(--surface);
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
	.slot-summary,
	.slots {
		flex-wrap: wrap;
		gap: 0.45rem;
	}
	.slot-summary span,
	.slots span {
		padding: 0.35rem 0.55rem;
		border-radius: var(--radius-xs);
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

	.selected-player {
		padding: 0.5rem 0.7rem;
		border-radius: var(--radius-sm);
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
		border-radius: var(--radius-sm);
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
		padding: 0.6rem;
		border: var(--bw) solid var(--border);
		border-radius: var(--radius-sm);
		background: var(--input-bg);
		color: var(--text);
		font-size: 0.875rem;
		font-weight: 700;
		text-align: left;
		cursor: pointer;
	}
	.search-results button:hover {
		border-color: var(--border-hover);
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
	.strategy-picker :global(select) {
		width: auto;
		min-width: 9rem;
	}
	.team-grid {
		display: flex;
		align-items: stretch;
		gap: 0.8rem;
		width: max-content;
		min-width: 100%;
		margin-top: 1rem;
	}
	.team-card {
		flex: 0 0 min(22.5rem, calc(100vw - 4rem));
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
		border-radius: var(--radius-sm);
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
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		background: var(--input-bg);
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
	.purchase-group .purchase-row:first-child {
		border-top: 0;
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
	/* A team card can end up narrower than the tier badge needs, regardless of viewport size
	   (e.g. many participants forcing extra grid columns) — reflow the badge onto its own row
	   whenever the card itself is tight, not just when the whole page is. */
	@container team-card (max-width: 380px) {
		.purchase-row:not(.registry-row) {
			grid-template-columns: 1.5rem minmax(60px, 1fr) 2.5rem;
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

	.strategy-roles {
		display: flex;
		align-items: stretch;
		gap: 0.7rem;
		width: max-content;
		min-width: 100%;
		margin-top: 1rem;
	}
	.tier {
		display: flex;
		flex-direction: column;
		flex: 0 0 min(17.5rem, calc(100vw - 4rem));
		border: var(--bw) solid var(--line);
		border-radius: var(--radius-sm);
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
		align-content: start;
		gap: 0.35rem;
		padding: 0 0.45rem 0.45rem;
		flex: 1;
	}
	.tier-player-button {
		display: block;
		width: 100%;
		padding: 0;
		border: 0;
		border-radius: var(--radius-xs);
		background: none;
		font: inherit;
		color: inherit;
		text-align: left;
		cursor: pointer;
	}
	.tier-player-button:disabled {
		cursor: default;
		opacity: 1;
	}
	.tier-player-button:not(:disabled):hover:not(:focus-visible) {
		outline: 1px solid var(--border-hover);
	}
	.catalog-section {
		margin-top: 3rem;
	}
	.catalog-section details {
		border: var(--bw) solid var(--line);
		border-radius: var(--radius);
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
	.catalog-section summary strong {
		font: 800 1.1rem/1.15 var(--font-display);
	}
	.catalog-section summary small {
		color: var(--subdued);
	}
	.catalog-content {
		padding: 1rem 1.2rem 1.2rem;
		border-top: 1px solid var(--border);
	}
	.catalog-toolbar,
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
	.catalog-mantra-chips {
		flex-wrap: wrap;
		gap: 0.35rem;
	}
	.catalog-toolbar :global(select) {
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
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		background: var(--input-bg);
		font-size: 0.875rem;
		font-weight: 700;
		text-align: left;
		cursor: pointer;
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
		color: var(--taken-text);
	}
	.catalog-player.purchased .catalog-player-heading > strong {
		text-decoration: line-through;
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
	@media (max-width: 950px) {
		.call-panel form {
			grid-template-columns: 1fr 1fr;
		}
		.search-results {
			grid-template-columns: repeat(2, 1fr);
		}
	}
	@media (max-width: 620px) {
		.call-panel form,
		.called-player-strategy,
		.search-results {
			grid-template-columns: 1fr;
		}
		.catalog-toolbar {
			align-items: stretch;
			flex-direction: column;
		}
		.catalog-toolbar :global(.field) {
			justify-content: space-between;
		}
		.catalog-toolbar :global(select) {
			flex: 1;
		}
	}
</style>
