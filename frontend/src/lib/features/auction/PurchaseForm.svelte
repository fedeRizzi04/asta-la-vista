<script lang="ts">
	import Button from '$lib/components/ui/Button.svelte';
	import Combobox from '$lib/components/ui/Combobox.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import type { Participant } from '$lib/auctions';
	import { t } from '$lib/i18n';
	import type { Player } from '$lib/players';
	import { matchesSearch, nameMatchRank } from '$lib/search';
	import { registerShortcuts, withShortcut } from '$lib/shortcuts.svelte';

	/** Who won the called player and at what price, filled in whenever the bidding ends. */
	let {
		player,
		participants,
		saving,
		onregister
	}: {
		player: Player | undefined;
		participants: Participant[];
		saving: boolean;
		onregister: (participantId: string, price: number) => void;
	} = $props();

	const winnerKeys = 'mod+enter';
	const winnerInputId = $props.id();
	let winnerSearch = $state('');
	let winnerId = $state('');
	let price = $state<number | null>(null);
	let winnerInput = $state<HTMLInputElement>();
	let priceInput = $state<HTMLInputElement>();

	$effect(() =>
		registerShortcuts([
			{
				keys: winnerKeys,
				description: t.auction.goToWinner,
				group: t.auction.title,
				handler: () => winnerInput?.focus()
			}
		])
	);

	let winner = $derived(participants.find((participant) => participant.id === winnerId));
	let matchingParticipants = $derived(
		participants
			.filter((participant) => matchesSearch(winnerSearch, participant.name))
			.sort(
				(first, second) =>
					nameMatchRank(first.name, winnerSearch) - nameMatchRank(second.name, winnerSearch)
			)
	);

	function searchWinner(text: string): void {
		winnerSearch = text;
		winnerId = '';
	}

	function chooseWinner(participant: Participant): void {
		winnerSearch = participant.name;
		winnerId = participant.id;
		priceInput?.focus();
	}

	function isRoleFull(participant: Participant): boolean {
		if (!player) return false;
		const { filled, total } = participant.slots[player.role];
		return filled >= total;
	}

	function submit(event: SubmitEvent): void {
		event.preventDefault();
		if (winner && price !== null) onregister(winner.id, price);
	}
</script>

<form onsubmit={submit}>
	<Field
		label={winner ? t.auction.winnerWithMaximum(winner.maximum_bid) : t.auction.winner}
		for={winnerInputId}
	>
		<Combobox
			id={winnerInputId}
			bind:value={() => winnerSearch, searchWinner}
			bind:element={winnerInput}
			title={withShortcut(t.auction.winner, winnerKeys)}
			items={matchingParticipants}
			emptyMessage={t.auction.noParticipants}
			openOnFocus
			disabled={!player}
			onchoose={chooseWinner}
		>
			{#snippet option(participant)}
				<span class="participant" class:full={isRoleFull(participant)}>
					<strong>{participant.name}</strong>
					<span>max {participant.maximum_bid}</span>
				</span>
			{/snippet}
		</Combobox>
	</Field>
	<Field label={t.auction.price}>
		<Input
			bind:value={price}
			bind:element={priceInput}
			type="number"
			min="1"
			required
			disabled={!player}
		/>
	</Field>
	<Button type="submit" disabled={!winner || saving}>{t.auction.record}</Button>
</form>

<style>
	form {
		display: grid;
		grid-template-columns: 12rem 5.5rem auto;
		align-items: end;
		gap: 0.6rem;
	}

	.participant {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 0.75rem;
	}

	.participant span {
		color: var(--muted);
		font-size: 0.8rem;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}

	.participant.full {
		opacity: 0.5;
	}

	@media (max-width: 620px) {
		form {
			grid-template-columns: 1fr 5.5rem;
		}

		form :global(button) {
			grid-column: 1 / -1;
		}
	}
</style>
