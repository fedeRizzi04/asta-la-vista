<script lang="ts">
	import { tick } from 'svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import TierBadge from '$lib/components/TierBadge.svelte';
	import Combobox from '$lib/components/ui/Combobox.svelte';
	import { t } from '$lib/i18n';
	import { matchesSearch, nameMatchRank } from '$lib/search';
	import { registerShortcuts, withShortcut } from '$lib/shortcuts.svelte';
	import type { AuctionState } from './auctionState.svelte';
	import PurchaseForm from './PurchaseForm.svelte';

	/**
	 * The call of a live auction: find a player, see what the strategy says about them and, when
	 * the bidding ends, record the winner and the price. Sticky, so calling a player from the
	 * lists below never needs scrolling; in narrow windows, where it is not, a call scrolls to it.
	 */
	let { auctionState }: { auctionState: AuctionState } = $props();

	const RESULT_LIMIT = 20;
	const searchKeys = 'mod+k';

	let searchInput = $state<HTMLInputElement>();
	let callBar = $state<HTMLElement>();
	/** Read out by screen readers, which would otherwise hear nothing of a registered purchase. */
	let announcement = $state('');
	let player = $derived(auctionState.calledPlayer);
	let entry = $derived(player && auctionState.entryForPlayer(player.id));
	let tier = $derived(player && auctionState.tierForPlayer(player.id));
	let maximumCredits = $derived(auctionState.maximumPriceCredits(entry?.maximum_price_percentage));

	/** The name of the called player, until the user types something else. */
	let query = $derived(player?.name ?? '');
	let results = $derived(
		query.trim()
			? auctionState.callablePlayers
					.filter((candidate) => matchesSearch(query, candidate.name, candidate.team))
					.sort(
						(first, second) =>
							nameMatchRank(first.name, query) - nameMatchRank(second.name, query) ||
							(second.quotation ?? -1) - (first.quotation ?? -1)
					)
					.slice(0, RESULT_LIMIT)
			: []
	);

	function focusSearch(): void {
		searchInput?.focus();
		searchInput?.select();
	}

	/**
	 * Takes the cursor out of the text fields, so the keys that act on the page (P D C A, ?, /)
	 * work at once. Focus goes to the call bar itself rather than being lost: Tab continues from
	 * here, into the search, and screen readers hear where they are.
	 */
	function leaveFields(): void {
		callBar?.focus({ preventScroll: true });
	}

	$effect(() =>
		registerShortcuts([
			{
				keys: searchKeys,
				description: t.auction.searchForPlayer,
				group: t.auction.title,
				handler: focusSearch
			},
			{
				keys: '/',
				description: t.auction.searchForPlayer,
				group: t.auction.title,
				handler: focusSearch
			},
			{
				keys: 'escape',
				description: t.auction.cancelCall,
				group: t.auction.title,
				handler: cancelCall
			}
		])
	);

	/** Scrolls only if the bar is not all in view. Not smoothly: the URL update would stop it. */
	async function reveal(): Promise<void> {
		// The called player makes the bar taller.
		await tick();
		callBar?.scrollIntoView({ block: 'nearest' });
	}

	$effect(() => {
		auctionState.onCall = reveal;
	});

	function search(text: string): void {
		// Before setting the text: a change of call resets it.
		auctionState.cancelCall();
		query = text;
	}

	function cancelCall(): void {
		// Before the call is cancelled: the winner and price fields go away with it.
		const inCallBar = callBar?.contains(document.activeElement);
		search('');
		if (inCallBar) leaveFields();
	}

	async function registerPurchase(participantId: string, price: number): Promise<void> {
		const called = player;
		const winner = auctionState.auction?.participants.find(({ id }) => id === participantId);
		if (!(await auctionState.registerPurchase(participantId, price)) || !called) return;
		announcement = t.auction.purchaseAnnouncement(called.name, winner?.name ?? '', price);
		// Not when another player has been called in the meantime: the user has moved on.
		if (!auctionState.calledPlayer) leaveFields();
	}
</script>

<!-- tabindex="-1": reachable by script only, see leaveFields. -->
<section class="call-bar" aria-label={t.auction.call} tabindex="-1" bind:this={callBar}>
	<div class="panel">
		<Combobox
			bind:value={() => query, search}
			bind:element={searchInput}
			items={results}
			emptyMessage={query.trim() ? t.auction.noPlayersFound : undefined}
			placeholder={t.common.searchPlayerOrClub}
			aria-label={t.auction.searchPlayer}
			title={withShortcut(t.auction.searchPlayer, searchKeys)}
			onchoose={(result) => auctionState.callPlayer(result.id)}
			--combobox-width="36rem"
		>
			{#snippet option(result)}
				{@const resultTier = auctionState.tierForPlayer(result.id)}
				{@const percentage = auctionState.entryForPlayer(result.id)?.maximum_price_percentage}
				<span class="result">
					<span class="role-badge" data-role={result.role}>{result.role}</span>
					<span class="result-name name-line name-min"
						><strong>{result.name}</strong> <small>{result.team}</small></span
					>
					<MantraRoleBadges roles={result.mantra_roles} compact />
					{#if resultTier}<TierBadge name={resultTier.name} color={resultTier.color} compact />{/if}
					<small>{t.common.quotationValue(result.quotation ?? '—')}</small>
					{#if auctionState.viewedStrategy}
						<span class="result-percentage">{percentage != null ? `${percentage}%` : '—'}</span>
					{/if}
				</span>
			{/snippet}
		</Combobox>

		<div class="called-player">
			{#if player}
				<div class="identity">
					<strong class="name">{player.name}</strong>
					<span class="role-badge" data-role={player.role}>{player.role}</span>
					<MantraRoleBadges roles={player.mantra_roles} compact />
					{#if tier}
						<TierBadge name={tier.name} color={tier.color} compact />
					{:else if auctionState.viewedStrategy}
						<span class="no-tier">{t.common.noTier}</span>
					{/if}
				</div>
				<div class="details">
					<span>{player.team} · {t.common.quotationValue(player.quotation ?? '—')}</span>
					{#if maximumCredits !== null}
						<strong>max {maximumCredits} cr · {entry?.maximum_price_percentage}%</strong>
					{/if}
					{#if entry?.note}<em title={entry.note}>{entry.note}</em>{/if}
				</div>
			{/if}
		</div>

		<!-- A new call starts with no winner and no price. -->
		{#key auctionState.calledPlayer}
			<PurchaseForm
				{player}
				participants={auctionState.auction?.participants ?? []}
				saving={auctionState.saving}
				onregister={registerPurchase}
			/>
		{/key}
	</div>
	<p class="announcement" role="status">{player ? '' : announcement}</p>
</section>

<style>
	.call-bar {
		position: sticky;
		top: var(--header-height);
		z-index: 80;
		margin-top: 1rem;
		/* Room for the panel's hard shadow above the content scrolling underneath. */
		padding: 0.5rem 0 0.6rem;
		background: var(--page-bg);
	}

	/* Focused by script after a purchase; a ring around the whole bar would only be noise. */
	.call-bar:focus {
		outline: none;
	}

	.announcement {
		position: absolute;
		width: 1px;
		height: 1px;
		margin: 0;
		overflow: hidden;
		clip-path: inset(50%);
		white-space: nowrap;
	}

	.panel {
		display: grid;
		grid-template-columns: 17rem minmax(0, 1fr) auto;
		align-items: center;
		gap: 1rem;
		min-height: 5.4rem;
		padding: 0.65rem 0.8rem;
	}

	.called-player {
		display: grid;
		gap: 0.3rem;
		min-width: 0;
	}

	.identity,
	.details,
	.result {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
		min-width: 0;
	}

	.name {
		font: 800 1.25rem/1.1 var(--font-display);
	}

	.no-tier,
	.details {
		color: var(--muted);
		font-size: 0.82rem;
	}

	.details > span,
	.details strong {
		flex: none;
	}

	.details strong {
		color: var(--text);
	}

	/* What does not fit goes to the next line: a name or a note is never cut to a sliver. */
	.details em {
		flex: 1 1 12ch;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.result-name {
		flex: 1 1 14ch;
	}

	.result small {
		color: var(--muted);
		white-space: nowrap;
	}

	.result-percentage {
		min-width: 2.75rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		text-align: right;
	}

	@media (max-width: 950px) {
		.call-bar {
			position: static;
			/* Not under the app header when scrolled into view. */
			scroll-margin-top: var(--header-height);
		}

		.panel {
			grid-template-columns: minmax(0, 1fr);
		}
	}
</style>
