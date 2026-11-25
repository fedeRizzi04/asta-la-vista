<script lang="ts">
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { getAuctions, type AuctionSummary } from '$lib/auctions';
	import Button from '$lib/components/ui/Button.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import AuctionCard from '$lib/features/auction/AuctionCard.svelte';
	import { t } from '$lib/i18n';
	import { getPlayerCounts, roleLabels, roles, type PlayerCounts } from '$lib/players';
	import { getStrategies, type StrategySummary } from '$lib/strategies';
	import { pushErrorToast } from '$lib/toast.svelte';

	let loading = $state(true);
	let overview = $state<{
		liveAuctions: AuctionSummary[];
		strategies: StrategySummary[];
		counts: PlayerCounts;
		total: number;
	}>();

	onMount(async () => {
		try {
			const [auctions, strategies, counts] = await Promise.all([
				getAuctions(),
				getStrategies(),
				getPlayerCounts()
			]);
			overview = {
				liveAuctions: auctions.filter((auction) => auction.status === 'live'),
				strategies: strategies.slice(0, 4),
				counts,
				total: roles.reduce((sum, role) => sum + counts[role], 0)
			};
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>{t.navigation.home} | Asta la Vista</title>
</svelte:head>

<PageHeader title={t.navigation.home} compact />

<div aria-busy={loading}>
	{#if loading}
		<p class="count-label">{t.common.loading}</p>
	{:else if overview}
		<div class="dashboard">
			<section class="panel">
				<header><h2>{t.home.liveAuction}</h2></header>
				{#if overview.liveAuctions.length}
					<div class="live-auctions">
						{#each overview.liveAuctions as auction (auction.id)}
							<AuctionCard {auction} highlighted heading="h3" />
						{/each}
					</div>
				{:else}
					<EmptyState compact>
						{t.home.noLiveAuction} <a href={resolve('/auctions')}>{t.home.goToAuctions}</a>
					</EmptyState>
				{/if}
			</section>

			<section class="panel">
				<header>
					<h2>{t.navigation.strategies}</h2>
					<Button
						href={resolve('/strategies')}
						variant="secondary"
						size="sm"
						aria-label={t.home.allStrategies}
					>
						{t.home.all}
					</Button>
				</header>
				{#if overview.strategies.length}
					<ul class="strategies">
						{#each overview.strategies as strategy (strategy.id)}
							<li>
								<a href={resolve('/strategies/[strategyId]', { strategyId: strategy.id })}>
									<strong>{strategy.name}</strong>
									<span
										>{t.home.strategySummary(
											strategy.tier_count,
											strategy.assigned_player_count
										)}</span
									>
								</a>
							</li>
						{/each}
					</ul>
				{:else}
					<EmptyState compact>{t.home.noSavedStrategies}</EmptyState>
				{/if}
			</section>

			<section class="panel">
				<header>
					<h2>{t.navigation.playerList}</h2>
					<Button href={resolve('/players')} variant="secondary" size="sm"
						>{t.home.openPlayerList}</Button
					>
				</header>
				{#if overview.total > 0}
					<p class="player-total">
						<strong>{overview.total}</strong>
						{t.home.playerTotalLabel(overview.total)}
					</p>
					<dl class="role-counts">
						{#each roles as role (role)}
							<div>
								<dt>
									<span class="role-badge" data-role={role} aria-hidden="true">{role}</span>
									{roleLabels[role]}
								</dt>
								<dd>{overview.counts[role]}</dd>
							</div>
						{/each}
					</dl>
				{:else}
					<EmptyState compact>{t.home.emptyPlayerList}</EmptyState>
				{/if}
			</section>
		</div>
	{:else}
		<EmptyState>{t.home.loadFailed}</EmptyState>
	{/if}
</div>

<style>
	.dashboard {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
		align-items: start;
		gap: 1rem;
	}

	header {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	h2 {
		margin: 0;
	}

	.live-auctions {
		display: grid;
		gap: 0.5rem;
	}

	.strategies {
		margin: 0;
		padding: 0;
		list-style: none;
	}

	.strategies li + li {
		border-top: 1px solid var(--border);
	}

	.strategies a {
		display: grid;
		gap: 0.15rem;
		padding: 0.4rem 0;
		text-decoration: none;
		overflow-wrap: anywhere;
	}

	.strategies strong {
		text-decoration: underline;
	}

	.strategies span {
		color: var(--muted);
		font-size: 0.85rem;
	}

	.player-total {
		margin: 0 0 0.6rem;
	}

	.role-counts {
		display: grid;
		gap: 0.45rem;
		margin: 0;
		font-size: 0.9rem;
	}

	.role-counts div,
	.role-counts dt {
		display: flex;
		align-items: center;
		gap: 0.45rem;
	}

	.role-counts div {
		justify-content: space-between;
	}

	.role-counts dd {
		margin: 0;
		font-variant-numeric: tabular-nums;
	}
</style>
