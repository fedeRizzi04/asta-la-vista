<script lang="ts">
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import MantraRoleFilter from '$lib/components/MantraRoleFilter.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import ToggleChip from '$lib/components/ui/ToggleChip.svelte';
	import { mantraRolesOf } from '$lib/mantraRoles';
	import type { Player, Role } from '$lib/players';
	import { matchesSearch } from '$lib/search';
	import type { StrategyEditor } from './strategyEditor.svelte';

	/** The players of a role still without a tier, to assign to one. */
	let { editor, role }: { editor: StrategyEditor; role: Role } = $props();

	type Sort = 'quotation' | 'name' | 'team';

	const byName = (first: Player, second: Player) => first.name.localeCompare(second.name, 'it');
	const byQuotation = (first: Player, second: Player) =>
		(second.quotation ?? -1) - (first.quotation ?? -1) || byName(first, second);
	const comparators: Record<Sort, (first: Player, second: Player) => number> = {
		quotation: byQuotation,
		name: byName,
		team: (first, second) =>
			first.team.localeCompare(second.team, 'it') || byQuotation(first, second)
	};

	let search = $state('');
	let sort = $state<Sort>('quotation');
	let showAssigned = $state(false);
	let selectedMantraRoles = $state<string[]>([]);

	let rolePlayers = $derived(editor.players.filter((player) => player.role === role));
	let mantraCodes = $derived(mantraRolesOf(rolePlayers));
	// A selection that does not apply to the role is ignored, and comes back with its role.
	let mantraRoles = $derived(selectedMantraRoles.filter((code) => mantraCodes.includes(code)));
	let shownPlayers = $derived(
		rolePlayers
			.filter(
				(player) =>
					(showAssigned || !editor.tierOfPlayer(player.id)) &&
					(mantraRoles.length === 0 ||
						mantraRoles.some((code) => player.mantra_roles.includes(code))) &&
					matchesSearch(search, player.name, player.team)
			)
			.sort(comparators[sort])
	);
</script>

<section class="panel pool" aria-labelledby="pool-title">
	<div class="pool-header">
		<div class="row">
			<h2 id="pool-title">{showAssigned ? 'Tutti' : 'Senza fascia'}</h2>
			<span class="count" aria-live="polite">{shownPlayers.length}</span>
			<div class="show-assigned">
				<ToggleChip pressed={showAssigned} onclick={() => (showAssigned = !showAssigned)}>
					Mostra tutti
				</ToggleChip>
			</div>
		</div>
		<div class="row">
			<Input
				bind:value={search}
				type="search"
				placeholder="Cerca"
				aria-label="Cerca calciatore o squadra"
			/>
			<Select bind:value={sort} aria-label="Ordina per">
				<option value="quotation">Quotazione</option>
				<option value="name">Nome</option>
				<option value="team">Squadra</option>
			</Select>
		</div>
		{#if mantraCodes.length > 1}
			<MantraRoleFilter
				codes={mantraCodes}
				bind:selected={() => mantraRoles, (codes) => (selectedMantraRoles = codes)}
			/>
		{/if}
	</div>

	<!-- svelte-ignore a11y_no_noninteractive_tabindex (Allow keyboard scrolling.) -->
	<div class="pool-players" role="region" aria-labelledby="pool-title" tabindex="0">
		{#each shownPlayers as player (player.id)}
			{@const tier = showAssigned && editor.tierOfPlayer(player.id)}
			<div class="player" class:inactive={!player.active}>
				<span class="identity">
					<strong title={player.name}>{player.name}</strong>
					<small>{player.team}{player.active ? '' : ' · inattivo'}</small>
					<MantraRoleBadges roles={player.mantra_roles} compact />
					{#if tier}<TierBadge name={tier.name} color={tier.color} compact />{/if}
				</span>
				<span class="quotation" title="Quotazione">{player.quotation ?? '—'}</span>
			</div>
		{:else}
			<p class="empty">Nessun calciatore</p>
		{/each}
	</div>
</section>

<style>
	.pool {
		display: flex;
		flex-direction: column;
		min-height: 0;
		padding: 0;
		overflow: hidden;
	}

	.pool-header {
		display: grid;
		gap: 0.5rem;
		padding: 0.6rem 0.75rem;
		border-bottom: var(--bw) solid var(--line);
		background: var(--head-bg);
	}

	.row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.row :global(select) {
		flex: none;
		width: auto;
	}

	.pool-header :global(.mantra-filter) {
		gap: 0.3rem;
	}

	h2 {
		margin: 0;
		font-size: 1rem;
	}

	.count {
		color: var(--muted);
		font-variant-numeric: tabular-nums;
	}

	.show-assigned {
		margin-left: auto;
	}

	.pool-players {
		flex: 1;
		min-height: 0;
		padding: 0.25rem;
		overflow-y: auto;
	}

	.pool-players:focus-visible {
		outline-offset: -3px;
	}

	.player {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		align-items: baseline;
		gap: 0.5rem;
		padding: 0.3rem 0.45rem;
		border-radius: var(--radius-xs);
		font-size: 0.875rem;
	}

	.player:hover {
		background: var(--hover);
	}

	.identity {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0 0.35rem;
		min-width: 0;
	}

	.identity strong {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	small {
		color: var(--muted);
		font-size: 0.75rem;
	}

	.quotation {
		font: 800 0.9rem/1 var(--font-display);
		font-variant-numeric: tabular-nums;
	}

	.inactive,
	.inactive small {
		color: var(--taken-text);
	}

	.empty {
		margin: 0;
		padding: 0.45rem;
		color: var(--muted);
		font-size: 0.8rem;
	}
</style>
