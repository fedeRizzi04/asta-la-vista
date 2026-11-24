<script lang="ts">
	import { purchasesForRole } from '$lib/auctions';
	import HorizontalScroller from '$lib/components/HorizontalScroller.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Tabs from '$lib/components/ui/Tabs.svelte';
	import { panelVisibility } from '$lib/panelVisibility.svelte';
	import { roleLabels, roles } from '$lib/players';
	import type { AuctionState } from './auctionState.svelte';
	import RosterDrawer from './RosterDrawer.svelte';

	let { auctionState }: { auctionState: AuctionState } = $props();

	type View = 'roster' | 'compact';
	const views: { value: View; label: string }[] = [
		{ value: 'roster', label: 'Rose' },
		{ value: 'compact', label: 'Compatta' }
	];
	const id = $props.id();
	const visibleSlots = 12;
	let view = $state<View>('roster');
	let selectedId = $state<string>();
	let auction = $derived(auctionState.auction);
	let visibility = $derived(auction && panelVisibility(`auction:${auction.id}:teams`));
	let selected = $derived(
		auction?.participants.find((participant) => participant.id === selectedId)
	);
	let hasTallRoster = $derived(
		!!auction && roles.some((role) => auction.slot_totals[role] > visibleSlots)
	);
</script>

{#if auction && visibility}
	<section class="teams" aria-label="Squadre">
		<div class="strip-header">
			<Button
				variant="secondary"
				size="sm"
				aria-expanded={visibility.visible}
				aria-controls="{id}-teams"
				onclick={() => {
					view = 'roster';
					visibility?.toggle();
				}}
			>
				<span aria-hidden="true">{visibility.visible ? '▾' : '▸'}</span> Squadre
			</Button>
			{#if visibility.visible}
				<Tabs items={views} bind:value={view} label="Vista squadre" {id} panelId="{id}-teams" />
			{:else}
				<!-- svelte-ignore a11y_no_noninteractive_tabindex (Allow keyboard scrolling in the credit summary.) -->
				<div class="credit-pills" role="region" aria-label="Crediti residui" tabindex="0">
					{#each auction.participants as participant (participant.id)}
						<span>{participant.name} <strong>{participant.credits_remaining}</strong></span>
					{/each}
				</div>
			{/if}
		</div>

		<div
			id="{id}-teams"
			role="tabpanel"
			aria-labelledby={visibility.visible ? `${id}-${view}` : undefined}
			tabindex="0"
			hidden={!visibility.visible}
		>
			{#if visibility.visible}
				<HorizontalScroller
					ariaLabel={view === 'roster' ? 'Rose dei partecipanti' : 'Slot dei partecipanti'}
				>
					<div class="strip" class:compact={view === 'compact'}>
						{#each auction.participants as participant (participant.id)}
							<article class="panel team-card">
								<button
									type="button"
									class="team-header"
									aria-haspopup="dialog"
									aria-label={`Rosa di ${participant.name}, ${participant.credits_remaining} crediti residui, puntata massima ${participant.maximum_bid}`}
									onclick={() => (selectedId = participant.id)}
								>
									<span class="team-name" title={participant.name}>{participant.name}</span>
									<span class="budget">
										<strong>{participant.credits_remaining}</strong>
										<span>max {participant.maximum_bid}</span>
									</span>
								</button>
								<!-- svelte-ignore a11y_no_noninteractive_tabindex (Allow keyboard scrolling in tall rosters.) -->
								<div
									class="team-slots"
									style:--visible-slots={visibleSlots}
									role="group"
									aria-label="Slot di {participant.name}"
									tabindex={view === 'roster' && hasTallRoster ? 0 : undefined}
								>
									{#each roles as role (role)}
										<div
											class="role-column"
											data-role={role}
											role="group"
											aria-label={roleLabels[role]}
										>
											<span class="role-badge" data-role={role} aria-hidden="true">{role}</span>
											{#if view === 'compact'}
												<div
													class="mini-bar"
													style:--slot-count={auction.slot_totals[role]}
													role="img"
													aria-label="{participant.slots[role].filled} slot occupati su {auction
														.slot_totals[role]}"
												>
													{#each { length: auction.slot_totals[role] }, index (index)}
														<span class:filled={index < participant.slots[role].filled}></span>
													{/each}
												</div>
											{:else}
												{@const purchases = purchasesForRole(participant, role)}
												{#each { length: auction.slot_totals[role] }, index (index)}
													{@const purchase = purchases[index]}
													{#if purchase}
														{@const tier = auctionState.tierForPlayer(purchase.player_id)}
														<div
															class="slot"
															style:--tier-color={tier?.color ?? 'transparent'}
															title={`${purchase.player_name} · ${purchase.team} · ${purchase.price} cr${tier ? ` · ${tier.name}` : ''}`}
														>
															<span class="surname"
																>{purchase.player_name.replace(/(?:\s+\p{L}\.)+$/u, '')}</span
															>
															<span class="price">{purchase.price}</span>
														</div>
													{:else}
														<div class="slot empty" aria-hidden="true"></div>
													{/if}
												{/each}
											{/if}
										</div>
									{/each}
								</div>
							</article>
						{/each}
					</div>
				</HorizontalScroller>
			{/if}
		</div>
	</section>
{/if}

{#if selected}
	<RosterDrawer {auctionState} participant={selected} onclose={() => (selectedId = undefined)} />
{/if}

<style>
	.teams {
		--strip-gap: 0.5rem;
		container-type: inline-size;
	}
	.strip-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		min-height: 2.5rem;
	}
	.credit-pills,
	.strip {
		display: flex;
		gap: var(--strip-gap);
	}
	.credit-pills {
		min-width: 0;
		padding: 0.2rem;
		overflow-x: auto;
		scrollbar-width: thin;
	}
	.credit-pills span {
		padding: 0.15rem 0.5rem;
		border: 1px solid var(--border);
		border-radius: 999px;
		background: var(--surface);
		font-size: 0.8rem;
		white-space: nowrap;
	}
	.strip {
		--strip-padding: 0.25rem;
		padding: var(--strip-padding);
	}
	.team-card {
		flex: none;
		width: min(
			calc(100cqw - 2 * var(--strip-padding)),
			max(14rem, calc((100cqw - 3 * var(--strip-gap) - 2 * var(--strip-padding)) / 4))
		);
		padding: 0.35rem;
	}
	.compact .team-card {
		width: 10.5rem;
	}
	.team-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.4rem;
		width: 100%;
		padding: 0.25rem 0.35rem;
		border: 0;
		border-radius: var(--radius-xs);
		background: transparent;
		text-align: left;
		cursor: pointer;
	}
	.team-header:hover {
		background: var(--hover);
	}
	.team-name,
	.surname {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.team-name {
		font: 800 1rem/1.15 var(--font-display);
	}
	.budget {
		display: grid;
		justify-items: end;
		color: var(--muted);
		font-size: 0.75rem;
		line-height: 1.05;
		white-space: nowrap;
	}
	.budget strong {
		color: var(--text);
		font: 800 1.4rem/1 var(--font-display);
	}
	.budget,
	.credit-pills strong,
	.price {
		font-variant-numeric: tabular-nums;
	}
	.team-slots {
		--slot-height: 1.125rem;
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.25rem;
		max-height: calc((var(--visible-slots) + 1) * var(--slot-height) + 0.25rem + 1px);
		padding-top: 0.25rem;
		border-top: 1px dashed var(--border);
		overflow-y: auto;
		scrollbar-width: thin;
	}
	.team-slots .role-badge {
		display: grid;
		width: var(--slot-height);
		height: var(--slot-height);
		font-size: 0.7rem;
	}
	.slot {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.15rem;
		height: var(--slot-height);
		font-size: 0.75rem;
	}
	.slot::before {
		flex: 0 0 2px;
		align-self: stretch;
		margin-block: 0.15rem;
		border-radius: var(--radius-xs);
		background: var(--tier-color, transparent);
		content: '';
	}
	.surname {
		flex: 1;
		font-weight: 700;
	}
	.price {
		color: var(--muted);
		font-size: 0.7rem;
	}
	.empty::after {
		flex: 1;
		border-top: 1px dashed var(--muted);
		content: '';
	}
	.compact .team-slots {
		grid-template-columns: minmax(0, 1fr);
	}
	.compact .role-column {
		display: grid;
		grid-template-columns: var(--slot-height) minmax(0, 1fr);
		align-items: center;
		gap: 0.35rem;
	}
	.role-column[data-role='P'] {
		--role-color: var(--goalkeeper-bg);
	}
	.role-column[data-role='D'] {
		--role-color: var(--defender-bg);
	}
	.role-column[data-role='C'] {
		--role-color: var(--midfielder-bg);
	}
	.role-column[data-role='A'] {
		--role-color: var(--forward-bg);
	}
	.mini-bar {
		display: flex;
		gap: min(1px, calc(25% / max(1, var(--slot-count))));
	}
	.mini-bar span {
		flex: 1;
		height: 0.45rem;
		border-radius: 2px;
		background: color-mix(in srgb, var(--role-color) 25%, var(--surface));
	}
	.mini-bar .filled {
		background: var(--role-color);
		box-shadow: inset 0 0 0 1px var(--line);
	}

	@container (min-width: 24rem) {
		/* Put the scroller controls in the header where they leave every slot visible. */
		.teams :global(.rail-button) {
			top: -1.25rem;
			width: 1.75rem;
			height: 1.75rem;
		}
		.teams :global(.rail-button.previous) {
			right: 2.55rem;
			left: auto;
		}
	}
</style>
