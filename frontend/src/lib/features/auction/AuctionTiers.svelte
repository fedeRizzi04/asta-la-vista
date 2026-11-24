<script lang="ts">
	import TierBoard from '$lib/components/TierBoard.svelte';
	import TierPlayerCard from '$lib/components/TierPlayerCard.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import ToggleChip from '$lib/components/ui/ToggleChip.svelte';
	import { panelVisibility } from '$lib/panelVisibility.svelte';
	import type { Role } from '$lib/players';
	import { byMaxPercentageDesc } from '$lib/strategies';
	import type { AuctionState } from './auctionState.svelte';

	/** The tiers of one strategy during the auction, with the players left and the taken ones. */
	let { auctionState, role }: { auctionState: AuctionState; role: Role } = $props();

	let auction = $derived(auctionState.auction);
	let strategy = $derived(auctionState.viewedStrategy);
	let takenPlayers = $derived(panelVisibility(`auction:${auction?.id}:tier-taken-players`));

	let columns = $derived.by(() => {
		if (!strategy) return [];
		const { id: strategyId, entries: strategyEntries } = strategy;
		return auctionState.sortedTiers.map((tier) => {
			const key = `${strategyId}:${role}:${tier.id}`;
			const entries = strategyEntries
				.filter((entry) => entry.role === role && entry.tier_id === tier.id)
				.sort(byMaxPercentageDesc((entry) => entry.maximum_price_percentage));
			return {
				key,
				tier,
				entries,
				leftCount: entries.filter(
					(entry) => entry.active && !auctionState.purchasedIds.has(entry.player_id)
				).length,
				// A tier with no players of this role starts closed.
				panel: panelVisibility(`tier:${key}`, entries.length > 0)
			};
		});
	});
	let allClosed = $derived(columns.every((column) => !column.panel.visible));

	function setAllVisible(visible: boolean): void {
		for (const { panel } of columns) {
			if (panel.visible !== visible) panel.toggle();
		}
	}
</script>

<div class="toolbar">
	{#if auctionState.strategies.length > 0}
		<Field label="Strategia" inline>
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
				variant="secondary"
				size="sm"
				disabled={auctionState.saving}
				onclick={() => auctionState.fixViewedStrategy()}
			>
				Fissa per l'asta
			</Button>
		{:else if auctionState.viewingStrategyId}
			<span class="fixed">Fissata</span>
		{/if}
	{/if}
	{#if columns.length > 0}
		<div class="board-actions">
			<ToggleChip pressed={!takenPlayers.visible} onclick={() => takenPlayers.toggle()}>
				Nascondi presi
			</ToggleChip>
			<Button variant="text" size="sm" onclick={() => setAllVisible(allClosed)}>
				{allClosed ? 'Espandi tutte' : 'Comprimi tutte'}
			</Button>
		</div>
	{/if}
</div>

{#if columns.length > 0}
	<TierBoard {columns} label="Fasce della strategia">
		{#snippet summary({ entries, leftCount })}
			rimasti <b>{leftCount}</b>/{entries.length}
		{/snippet}
		{#snippet players({ entries })}
			{@const shownEntries = takenPlayers.visible
				? entries
				: entries.filter((entry) => !auctionState.purchasedIds.has(entry.player_id))}
			{#each shownEntries as entry (entry.player_id)}
				{@const record = auctionState.purchaseOfPlayer(entry.player_id)}
				<button
					type="button"
					class="player"
					disabled={!auctionState.canCall(entry.player_id)}
					aria-current={auctionState.calledPlayer?.id === entry.player_id || undefined}
					onclick={() => auctionState.callPlayer(entry.player_id)}
				>
					<TierPlayerCard
						name={entry.name}
						team={entry.team}
						mantraRoles={entry.mantra_roles}
						maximumPricePercentage={entry.maximum_price_percentage}
						maximumPriceCredits={auctionState.maximumPriceCredits(entry.maximum_price_percentage)}
						note={entry.note}
						inactive={!entry.active}
						taken={record && { buyer: record.participant.name, price: record.purchase.price }}
					/>
				</button>
			{:else}
				<p class="empty">{entries.length > 0 ? 'Tutti presi' : 'Nessun calciatore'}</p>
			{/each}
		{/snippet}
	</TierBoard>
{:else}
	<EmptyState compact>
		{strategy ? 'La strategia non ha fasce' : 'Nessuna strategia selezionata'}
	</EmptyState>
{/if}

<style>
	.toolbar,
	.board-actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
	}

	.toolbar {
		margin-bottom: 0.6rem;
	}

	.toolbar :global(select) {
		width: auto;
		min-width: 9rem;
		max-width: 16rem;
	}

	.board-actions {
		margin-left: auto;
	}

	.fixed {
		padding: 0.1rem 0.5rem;
		border: 1px dashed var(--muted);
		border-radius: 999px;
		color: var(--muted);
		font-size: 0.75rem;
		font-weight: 700;
	}

	b {
		color: var(--text);
		font: 800 0.95rem/1 var(--font-display);
	}

	.player {
		display: block;
		width: 100%;
		padding: 0;
		border: 0;
		border-radius: var(--radius-xs);
		background: none;
		text-align: left;
	}

	.player:enabled {
		cursor: pointer;
	}

	.player:enabled:hover {
		background: var(--hover);
	}

	.player[aria-current] {
		background: var(--selected-bg);
		box-shadow: inset 0 0 0 var(--bw) var(--line);
	}

	.player:focus-visible {
		outline-offset: -2px;
	}

	.empty {
		margin: 0;
		padding: 0.45rem;
		color: var(--muted);
		font-size: 0.8rem;
	}
</style>
