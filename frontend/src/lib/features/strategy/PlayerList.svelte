<script lang="ts">
	import { tick, type Snippet } from 'svelte';
	import type { Player } from '$lib/players';
	import type { PlayerDrag } from './playerDrag.svelte';
	import type { StrategyEditor } from './strategyEditor.svelte';

	/**
	 * A list of players to select, and to drag to another list. With one row in the Tab order
	 * (roving tabindex), ↑/↓ and Home/End move and select; Shift extends the selection, ⌘ or Ctrl
	 * leaves it as it is, and Space adds or removes the focused row.
	 */
	let {
		editor,
		drag,
		players,
		tierId,
		label,
		row
	}: {
		editor: StrategyEditor;
		drag: PlayerDrag;
		players: Player[];
		/** The tier of the list, '' for the pool. */
		tierId: string;
		label: string;
		row: Snippet<[Player]>;
	} = $props();

	let list = $state<HTMLElement>();
	let lastFocusedId = $state<string>();

	let ids = $derived(players.map((player) => player.id));
	let tabStopId = $derived(
		lastFocusedId !== undefined && ids.includes(lastFocusedId) ? lastFocusedId : ids.at(0)
	);

	// When the focused row leaves the list, the next one takes the focus.
	let previousIds: string[] = [];
	$effect.pre(() => {
		const focused = document.activeElement as HTMLElement | null;
		const focusedId = list?.contains(focused) ? focused?.dataset.playerId : undefined;
		if (focusedId !== undefined && !ids.includes(focusedId)) {
			const index = previousIds.indexOf(focusedId);
			const isLeft = (id: string) => ids.includes(id);
			const nextId =
				previousIds.slice(index).find(isLeft) ?? previousIds.slice(0, index).findLast(isLeft);
			void tick().then(() => focusRow(nextId));
		}
		previousIds = ids;
	});

	/** Focuses the list itself if it has no such row. */
	function focusRow(id: string | undefined): void {
		const index = ids.findIndex((rowId) => rowId === id);
		const target = list?.children[index] ?? list;
		(target as HTMLElement | undefined)?.focus();
	}

	function onclick(event: MouseEvent, id: string): void {
		if (event.shiftKey) editor.selection.extendTo(id, ids);
		else if (event.metaKey || event.ctrlKey) editor.selection.toggle(id);
		else editor.selection.selectOnly(id);
	}

	function onkeydown(event: KeyboardEvent, id: string): void {
		if (event.key === ' ') {
			event.preventDefault();
			editor.selection.toggle(id);
			return;
		}
		const index = ids.indexOf(id);
		const target = {
			ArrowUp: Math.max(index - 1, 0),
			ArrowDown: Math.min(index + 1, ids.length - 1),
			Home: 0,
			End: ids.length - 1
		}[event.key];
		if (target === undefined) return;
		event.preventDefault();
		focusRow(ids[target]);
		if (event.shiftKey) editor.selection.extendTo(ids[target], ids, id);
		else if (!event.metaKey && !event.ctrlKey) editor.selection.selectOnly(ids[target]);
	}
</script>

<div
	class="player-list"
	bind:this={list}
	role="listbox"
	aria-label={label}
	aria-multiselectable="true"
	tabindex="-1"
>
	{#each players as player (player.id)}
		{@const landing = drag.landsIn(tierId, player.id)}
		<div
			class="player"
			class:landing
			class:dragged={!landing && drag.isDragged(player.id)}
			class:saved={editor.entrySaved[player.id]}
			role="option"
			aria-selected={editor.selection.ids.has(player.id)}
			tabindex={player.id === tabStopId ? 0 : -1}
			data-player-id={player.id}
			onfocus={() => (lastFocusedId = player.id)}
			onclick={(event) => onclick(event, player.id)}
			onkeydown={(event) => onkeydown(event, player.id)}
		>
			<span class="grip" data-player-grip aria-hidden="true">⠿</span>
			{@render row(player)}
		</div>
	{/each}
</div>
{#if players.length === 0}
	<p class="empty">Nessun calciatore</p>
{/if}

<style>
	.player-list:focus-visible {
		outline-offset: -3px;
	}

	.player {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr);
		border-radius: var(--radius-xs);
		cursor: grab;
		user-select: none;
		-webkit-user-select: none;
		transition: background-color 220ms ease;
	}

	.player:hover {
		background: var(--hover);
	}

	.player:focus-visible {
		outline-offset: -2px;
	}

	.player.saved {
		background: var(--success-bg);
	}

	.player[aria-selected='true'] {
		background: var(--selected-bg);
		box-shadow: inset 0 0 0 var(--bw) var(--line);
	}

	.dragged {
		opacity: 0.35;
	}

	.player.landing {
		background: var(--selected-bg);
		box-shadow: none;
		outline: var(--bw) dashed var(--line);
		outline-offset: -2px;
	}

	.grip {
		display: grid;
		place-items: center;
		width: 1rem;
		color: var(--muted);
		font-size: 0.8rem;
		line-height: 1;
		opacity: 0.55;
		touch-action: none;
	}

	.player:hover .grip {
		opacity: 1;
	}

	.empty {
		margin: 0;
		padding: 0.45rem;
		color: var(--muted);
		font-size: 0.8rem;
	}
</style>
