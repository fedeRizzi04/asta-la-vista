<script lang="ts" module>
	export const entryTierFieldId = 'entry-editor-tier';
</script>

<script lang="ts">
	import Button from '$lib/components/ui/Button.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import { mantraRoleLabel, sortMantraRoles } from '$lib/mantraRoles';
	import { MAX_PERCENTAGE, percentageToCredits } from '$lib/strategies';
	import { referenceBudget } from './referenceBudget.svelte';
	import type { StrategyEditor } from './strategyEditor.svelte';

	let { editor }: { editor: StrategyEditor } = $props();
	let detail = $derived(editor.detail);
	let player = $derived(detail && editor.players.find(({ id }) => id === detail?.playerId));

	$effect(() => {
		if (detail && (editor.selection.ids.size !== 1 || !editor.selection.ids.has(detail.playerId))) {
			editor.closeDetail();
		}
	});

	function position(panel: HTMLElement, anchor: HTMLElement, playerId: string): () => void {
		const gap = 8;
		const { clientWidth, clientHeight } = document.documentElement;
		const { width, height } = panel.getBoundingClientRect();
		const row = anchor.getBoundingClientRect();
		const right = row.right + gap;
		const left = right + width <= clientWidth - gap ? right : row.left - width - gap;
		const top = Math.max(gap, Math.min(row.top, clientHeight - height - gap));
		panel.style.left = `${Math.max(gap, Math.min(left, clientWidth - width - gap))}px`;
		panel.style.top = `${top}px`;
		panel.style.maxHeight = `${clientHeight - top - gap}px`;

		const listeners = new AbortController();
		const options = { signal: listeners.signal, capture: true };
		window.addEventListener(
			'pointerdown',
			(event) => {
				if (
					event.target instanceof Element &&
					!panel.contains(event.target) &&
					!event.target.closest('[data-player-id]')
				) {
					editor.closeDetail();
				}
			},
			options
		);
		window.addEventListener(
			'scroll',
			(event) => {
				if (!(event.target instanceof Node && panel.contains(event.target))) editor.closeDetail();
			},
			options
		);
		window.addEventListener('resize', () => editor.closeDetail(), options);

		return () => {
			listeners.abort();
			void editor.flushEntrySave(playerId);
		};
	}

	/** Moves the focus first: a field losing it saves its draft, which needs the panel still open. */
	function closeAndFocus(anchor: HTMLElement): void {
		if (anchor.isConnected) anchor.focus({ preventScroll: true });
		editor.closeDetail();
	}
</script>

{#if detail && player}
	{@const { playerId, anchor } = detail}
	{@const draft = editor.entryDrafts[playerId]}
	{@const pct = draft.maximumPricePercentage}
	{#key detail}
		<div
			class="panel entry-editor"
			role="dialog"
			tabindex="-1"
			aria-label={`Dettaglio di ${player.name}`}
			{@attach (panel) => position(panel, anchor, playerId)}
			onkeydown={(event) => {
				if (event.key !== 'Escape') return;
				event.preventDefault();
				closeAndFocus(anchor);
			}}
		>
			<header>
				<h3>{player.name}</h3>
				<Button variant="text" size="sm" aria-label="Chiudi" onclick={() => closeAndFocus(anchor)}>
					✕
				</Button>
			</header>
			<p class="player-meta">
				{player.team}{player.active ? '' : ' · inattivo'} · Q. {player.quotation ?? '—'}
				{#if player.mantra_roles.length}
					· {sortMantraRoles(player.mantra_roles).map(mantraRoleLabel).join(' ')}
				{/if}
			</p>

			<Field label="Fascia" for={entryTierFieldId}>
				<Select
					id={entryTierFieldId}
					value={draft.tierId}
					onchange={(event) => editor.movePlayers([playerId], event.currentTarget.value)}
				>
					<option value="">Senza fascia</option>
					{#each editor.orderedTiers as tier (tier.id)}
						<option value={tier.id}>{tier.name}</option>
					{/each}
				</Select>
			</Field>
			<Field label="Prezzo massimo" for="entry-editor-percentage">
				<span class="price">
					<Input
						id="entry-editor-percentage"
						bind:value={draft.maximumPricePercentage}
						type="number"
						min="0.1"
						max={MAX_PERCENTAGE}
						step="0.1"
						oninput={() => editor.scheduleEntrySave(playerId)}
						onblur={() => editor.flushEntrySave(playerId)}
					/>
					<span>%</span>
					<strong
						>= {pct === undefined
							? '—'
							: `${percentageToCredits(pct, referenceBudget.value)} cr`}</strong
					>
					<small>su {referenceBudget.value}</small>
				</span>
			</Field>
			<Field label="Nota" for="entry-editor-note">
				<textarea
					id="entry-editor-note"
					class="control"
					rows="2"
					bind:value={draft.note}
					oninput={() => editor.scheduleEntrySave(playerId)}
					onblur={() => editor.flushEntrySave(playerId)}></textarea>
			</Field>

			<span class="save-status" role="status">{editor.entrySaved[playerId] ? 'Salvato' : ''}</span>
		</div>
	{/key}
{/if}

<style>
	.entry-editor {
		position: fixed;
		z-index: 910;
		inset: 0 auto auto 0;
		width: min(300px, calc(100% - 1rem));
		max-height: calc(100% - 1rem);
		display: grid;
		gap: 0.55rem;
		padding: 0.75rem;
		overflow: auto;
	}

	header,
	.price {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}

	header {
		justify-content: space-between;
	}

	h3,
	.player-meta {
		margin: 0;
	}

	.player-meta,
	.price small {
		color: var(--muted);
		font-size: 0.78rem;
	}

	.price :global(input) {
		width: 5rem;
	}

	.price {
		flex-wrap: wrap;
	}

	.save-status {
		min-height: 1lh;
	}
</style>
