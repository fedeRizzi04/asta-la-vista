<script lang="ts" module>
	import { withShortcut } from '$lib/shortcuts.svelte';
	import type { Tier } from '$lib/strategies';

	/** Only the first tiers have a key: 1–9. */
	const TIER_KEYS = 9;

	/** A tooltip with the name of a tier and the key that moves players to it. */
	export function tierTitle(tier: Tier, index: number): string {
		return index < TIER_KEYS ? withShortcut(tier.name, `${index + 1}`) : tier.name;
	}
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import { t } from '$lib/i18n';
	import { nameFit } from '$lib/names';
	import { registerShortcuts } from '$lib/shortcuts.svelte';
	import type { StrategyEditor } from './strategyEditor.svelte';

	/**
	 * Moves the selected players without dragging them: with the buttons shown while there is a
	 * selection, and with the keys 1–9 and 0. `workspaceId` is the element with the players, which
	 * takes the focus when the buttons go away.
	 */
	let { editor, workspaceId }: { editor: StrategyEditor; workspaceId: string } = $props();

	const group = t.strategies.strategy;
	const keys = { remove: '0', clear: 'escape' };

	let selection = $derived(editor.selection);
	let selectedPlayers = $derived(editor.players.filter((player) => selection.ids.has(player.id)));
	let selectedLabel = $derived(
		selectedPlayers.length === 1
			? selectedPlayers[0].name
			: t.strategies.playerCount(selectedPlayers.length)
	);
	let anyInTier = $derived(selectedPlayers.some((player) => editor.tierOfPlayer(player.id)));

	$effect(() =>
		registerShortcuts(
			editor.orderedTiers.slice(0, TIER_KEYS).map((tier, index) => ({
				keys: `${index + 1}`,
				description: t.strategies.moveToTier(tier.name),
				group,
				handler: () => moveWithKey(tier.id)
			}))
		)
	);

	onMount(() =>
		registerShortcuts([
			{
				keys: keys.remove,
				description: t.strategies.removeFromTier,
				group,
				handler: () => moveWithKey('')
			},
			{
				keys: keys.clear,
				description: t.strategies.clearSelection,
				group,
				handler: () => selection.clear(),
				when: () => selection.ids.size > 0
			}
		])
	);

	/** With nothing selected, moves the player with the keyboard focus. */
	function moveWithKey(tierId: string): void {
		if (editor.saving) return;
		if (selection.ids.size === 0) {
			const row = document.activeElement?.closest<HTMLElement>('[data-player-id]:focus-visible');
			if (row?.dataset.playerId) selection.selectOnly(row.dataset.playerId);
		}
		editor.movePlayers(selection.ids, tierId);
	}

	function moveWithButton(tierId: string): void {
		editor.movePlayers(selection.ids, tierId);
		close();
	}

	function close(): void {
		document.getElementById(workspaceId)?.focus({ preventScroll: true });
		selection.clear();
	}
</script>

<!-- Always in the layout: in a narrow window it wraps under the tabs, and appearing would push the lists down. -->
<div
	class="selection-bar"
	class:idle={selectedPlayers.length === 0}
	role="group"
	aria-label={t.strategies.selection}
>
	{#if selectedPlayers.length > 0}
		<span class={['selected', 'name-line', nameFit(selectedLabel)]}>{selectedLabel}</span>
		{#each editor.orderedTiers as tier, index (tier.id)}
			<Button
				variant="secondary"
				size="sm"
				class="tier"
				style="--tier-color: {tier.color ?? 'var(--tier-default)'}"
				title={tierTitle(tier, index)}
				aria-label={t.strategies.moveToTier(tier.name)}
				disabled={editor.saving}
				onclick={() => moveWithButton(tier.id)}
			>
				<span class={['tier-name', 'name-line', nameFit(tier.name)]}>{tier.name}</span>
			</Button>
		{/each}
		{#if anyInTier}
			<Button
				variant="secondary"
				size="sm"
				title={withShortcut(t.strategies.removeFromTier, keys.remove)}
				disabled={editor.saving}
				onclick={() => moveWithButton('')}
			>
				{t.strategies.remove}
			</Button>
		{/if}
		<Button
			variant="text"
			size="sm"
			title={withShortcut(t.strategies.clearSelection, keys.clear)}
			aria-label={t.strategies.clearSelection}
			onclick={close}
		>
			✕
		</Button>
	{/if}
</div>
<p class="announcement" role="status">{editor.lastMove}</p>

<style>
	.selection-bar {
		display: flex;
		flex: 1 1 24rem;
		/* With many or long tier names the buttons go to a second row instead of shrinking. */
		flex-wrap: wrap;
		align-items: center;
		justify-content: flex-end;
		gap: 0.35rem;
		min-width: 0;
		min-height: var(--control-height);
	}

	.idle {
		visibility: hidden;
	}

	.selected {
		flex: 0 1 auto;
		max-width: 12rem;
		margin-right: 0.25rem;
		font-weight: 700;
	}

	.selection-bar :global(.button) {
		box-shadow: none;
	}

	.selection-bar :global(.tier) {
		/* Only a name wider than the whole bar is cut. */
		max-width: 100%;
		border-left: 0.5rem solid var(--tier-color);
	}

	/* Only for screen readers. */
	.announcement {
		position: absolute;
		width: 1px;
		height: 1px;
		margin: 0;
		overflow: hidden;
		clip-path: inset(50%);
		white-space: nowrap;
	}
</style>
