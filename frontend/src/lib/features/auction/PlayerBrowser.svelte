<script lang="ts">
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import ToggleChip from '$lib/components/ui/ToggleChip.svelte';
	import { mantraRoleLabel, sortMantraRoles } from '$lib/mantraRoles';
	import type { Role } from '$lib/players';
	import { matchesSearch } from '$lib/search';
	import type { AuctionState } from './auctionState.svelte';

	type Sort = 'quotation' | 'tier' | 'name';

	let { auctionState, role }: { auctionState: AuctionState; role: Role } = $props();

	let selectedMantraRoles = $state<string[]>([]);
	let search = $state('');
	let sort = $state<Sort>('quotation');
	let showTaken = $state(false);

	let effectiveSort = $derived(
		sort === 'tier' && !auctionState.viewedStrategy ? 'quotation' : sort
	);
	let rolePlayers = $derived(
		auctionState.players.filter(
			(player) =>
				player.role === role && (player.active || auctionState.purchasedIds.has(player.id))
		)
	);
	let mantraCodes = $derived(
		sortMantraRoles([...new Set(rolePlayers.flatMap((player) => player.mantra_roles))])
	);
	let effectiveMantraRoles = $derived(
		selectedMantraRoles.filter((code) => mantraCodes.includes(code))
	);
	let playerRows = $derived(
		rolePlayers
			.filter(
				(player) =>
					(showTaken || !auctionState.purchasedIds.has(player.id)) &&
					(effectiveMantraRoles.length === 0 ||
						effectiveMantraRoles.some((code) => player.mantra_roles.includes(code))) &&
					matchesSearch(search, player.name, player.team)
			)
			.map((player) => {
				const tier = auctionState.tierForPlayer(player.id);
				return { player, tier, tierPosition: tier?.position ?? Infinity };
			})
			.sort((first, second) => {
				if (effectiveSort === 'tier' && first.tierPosition !== second.tierPosition) {
					return first.tierPosition - second.tierPosition;
				}
				if (effectiveSort !== 'name') {
					const difference = (second.player.quotation ?? -1) - (first.player.quotation ?? -1);
					if (difference) return difference;
				}
				return first.player.name.localeCompare(second.player.name, 'it');
			})
	);

	function toggleMantraRole(code: string): void {
		selectedMantraRoles = selectedMantraRoles.includes(code)
			? selectedMantraRoles.filter((selected) => selected !== code)
			: [...selectedMantraRoles, code];
	}
</script>

<div class="filters">
	{#if mantraCodes.length > 0}
		<div class="filter-row" role="group" aria-label="Sotto-ruoli Mantra">
			<ToggleChip
				pressed={effectiveMantraRoles.length === 0}
				onclick={() => (selectedMantraRoles = [])}
			>
				Tutti
			</ToggleChip>
			{#each mantraCodes as code (code)}
				<ToggleChip
					pressed={effectiveMantraRoles.includes(code)}
					onclick={() => toggleMantraRole(code)}
				>
					{mantraRoleLabel(code)}
				</ToggleChip>
			{/each}
		</div>
	{/if}
	<div class="filter-row">
		<Input
			bind:value={search}
			type="search"
			placeholder="Cerca calciatore o squadra"
			aria-label="Cerca calciatore o squadra"
		/>
		<Select
			bind:value={() => effectiveSort, (value: Sort) => (sort = value)}
			aria-label="Ordina per"
		>
			<option value="quotation">Quotazione</option>
			{#if auctionState.viewedStrategy}<option value="tier">Fascia</option>{/if}
			<option value="name">Nome</option>
		</Select>
		<ToggleChip pressed={showTaken} onclick={() => (showTaken = !showTaken)}>
			Mostra presi
		</ToggleChip>
	</div>
</div>

<p class="count" aria-live="polite">
	{playerRows.length}
	{playerRows.length === 1 ? 'calciatore' : 'calciatori'}
</p>
{#if playerRows.length === 0}
	<EmptyState compact>Nessun calciatore</EmptyState>
{:else}
	<div class="player-grid">
		{#each playerRows as { player, tier } (player.id)}
			{@const taken = auctionState.purchasedIds.has(player.id)}
			<button
				type="button"
				class="player"
				class:taken
				disabled={taken || auctionState.auction?.status !== 'live'}
				onclick={() => auctionState.callPlayer(player.id)}
			>
				<span class="player-heading">
					<span class="role-badge" data-role={player.role}>{player.role}</span>
					<strong class="player-name">{player.name}</strong>
					<span class="quotation">{player.quotation === null ? '—' : `Q. ${player.quotation}`}</span
					>
				</span>
				<span class="player-details">
					<span>{player.team}</span>
					<MantraRoleBadges roles={player.mantra_roles} compact />
					{#if tier}<TierBadge name={tier.name} color={tier.color} compact />{/if}
				</span>
			</button>
		{/each}
	</div>
{/if}

<style>
	.filters,
	.player-grid,
	.player {
		display: grid;
		gap: 0.5rem;
	}
	.filter-row,
	.player-heading,
	.player-details {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.filter-row,
	.player-details {
		flex-wrap: wrap;
	}
	.filter-row :global(input) {
		flex: 1 1 16rem;
	}
	.filter-row :global(select) {
		width: auto;
	}
	.count {
		margin: 0.75rem 0 0.5rem;
		color: var(--muted);
		font-size: 0.8rem;
	}
	.player-grid {
		grid-template-columns: repeat(auto-fill, minmax(min(100%, 12rem), 1fr));
	}
	.player {
		align-content: start;
		min-width: 0;
		padding: 0.65rem;
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		background: var(--surface);
		font-size: 0.875rem;
		text-align: left;
	}
	.player:enabled {
		cursor: pointer;
	}
	.player:enabled:hover {
		border-color: var(--primary-text);
	}
	.player-heading .role-badge,
	.quotation {
		flex: none;
	}
	.player-name {
		flex: 1;
		overflow-wrap: anywhere;
	}
	.quotation {
		font-variant-numeric: tabular-nums;
	}
	.player-details {
		color: var(--muted);
		font-size: 0.75rem;
	}
	.player.taken {
		background: var(--muted-bg);
		color: var(--taken-text);
	}
	.taken .player-details {
		color: inherit;
	}
	.taken .player-name {
		text-decoration: line-through;
	}
	.taken .role-badge,
	.taken :global(.tier-badge) {
		filter: grayscale(1);
	}
</style>
