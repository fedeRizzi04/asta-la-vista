import { tick } from 'svelte';
import type { Action } from 'svelte/action';
import { edgeScrollStep } from '$lib/dragList';
import { motionPreferences } from '$lib/motionPreferences.svelte';
import type { Player } from '$lib/players';
import type { StrategyEditor } from './strategyEditor.svelte';

/** Pointer movement, in px, before a press counts as a drag rather than a click. */
const DRAG_THRESHOLD = 6;
const SETTLE_MS = 180;

/**
 * Drags the selected players between the pool and the tiers. In the element with the `area`
 * action, each player row carries `data-player-id` and contains a `data-player-grip` (the only
 * part that drags on touch, as the rest scrolls); each place to drop them carries
 * `data-drop-tier`, the id of its tier or '' for the pool; the scrollers carry `data-drag-scroll`.
 *
 * The dragged rows stay where they are until the drop: only a preview follows the pointer, which
 * is captured by the area, as no move ever takes it out of the DOM.
 */
export class PlayerDrag {
	/** The dragged players, the grabbed one first. Empty when nothing is dragged. */
	players = $state.raw<Player[]>([]);
	/** The `data-drop-tier` where a drop would move the players now. */
	target = $state<string>();
	x = $state(0);
	y = $state(0);
	preview = $state<HTMLElement>();

	readonly #editor: StrategyEditor;

	constructor(editor: StrategyEditor) {
		this.#editor = editor;
	}

	isDragged(playerId: string): boolean {
		return this.players.some((player) => player.id === playerId);
	}

	/** Whether a drop now would add the player to the tier, or to the pool for ''. */
	landsIn(tierId: string, playerId: string): boolean {
		return (
			this.target === tierId &&
			this.isDragged(playerId) &&
			this.#editor.entryDrafts[playerId].tierId !== tierId
		);
	}

	readonly area: Action<HTMLElement> = (area) => {
		const lifetime = new AbortController();
		const { signal } = lifetime;
		area.addEventListener('pointerdown', (event) => this.#press(area, event, signal), { signal });
		return { destroy: () => lifetime.abort() };
	};

	#press(area: HTMLElement, press: PointerEvent, lifetime: AbortSignal): void {
		if (press.button !== 0 || this.players.length > 0 || this.#editor.saving) return;
		const pressed = press.target as HTMLElement;
		if (press.pointerType === 'touch' && !pressed.closest('[data-player-grip]')) return;
		const row = pressed.closest<HTMLElement>('[data-player-id]');
		const origin = row?.closest<HTMLElement>('[data-drop-tier]')?.dataset.dropTier;
		const grabbed = this.#editor.players.find((player) => player.id === row?.dataset.playerId);
		if (!grabbed || origin === undefined) return;

		const gesture = new AbortController();
		const { signal } = gesture;
		lifetime.addEventListener('abort', () => gesture.abort(), { signal });
		let frame: number | undefined;

		const start = () => {
			area.setPointerCapture(press.pointerId);
			// The focused row is about to move: the focus must not go to the next one.
			const focused = document.activeElement as HTMLElement | null;
			if (focused?.closest('[data-player-id]')) focused.blur();
			const { players, selection } = this.#editor;
			if (!selection.ids.has(grabbed.id)) selection.selectOnly(grabbed.id);
			this.players = [
				grabbed,
				...players.filter((player) => player !== grabbed && selection.ids.has(player.id))
			];
			signal.addEventListener('abort', () => cancelAnimationFrame(frame ?? 0));
			follow();
		};

		const follow = () => {
			this.#scrollAtEdges(area, press, origin);
			this.target = this.#targetAtPointer(area, origin);
			frame = requestAnimationFrame(follow);
		};

		const finish = (drop: boolean) => {
			gesture.abort();
			if (frame === undefined) return;
			area.releasePointerCapture(press.pointerId);
			skipNextClick();
			const target = drop ? this.#targetAtPointer(area, origin) : undefined;
			this.target = undefined;
			if (target !== undefined) {
				const ids = this.players.map((player) => player.id);
				this.#editor.movePlayers(ids, target);
			}
			void this.#settle(area, grabbed.id, target ?? origin);
		};

		const ownEvent = (event: PointerEvent) => event.pointerId === press.pointerId;
		window.addEventListener(
			'pointermove',
			(event) => {
				if (!ownEvent(event)) return;
				this.x = event.clientX;
				this.y = event.clientY;
				const distance = Math.hypot(this.x - press.clientX, this.y - press.clientY);
				if (frame === undefined && distance >= DRAG_THRESHOLD) start();
			},
			{ signal }
		);
		window.addEventListener('pointerup', (event) => ownEvent(event) && finish(true), { signal });
		window.addEventListener('pointercancel', (event) => ownEvent(event) && finish(false), {
			signal
		});
		window.addEventListener(
			'keydown',
			(event) => {
				if (event.key !== 'Escape' || frame === undefined) return;
				event.preventDefault();
				event.stopPropagation();
				finish(false);
			},
			{ signal, capture: true }
		);
	}

	#targetAtPointer(area: HTMLElement, origin: string): string | undefined {
		const zone = document
			.elementFromPoint(this.x, this.y)
			?.closest<HTMLElement>('[data-drop-tier]');
		const tierId = zone && area.contains(zone) ? zone.dataset.dropTier : undefined;
		if (tierId === undefined || tierId === origin) return;
		const { entryDrafts } = this.#editor;
		if (this.players.some((player) => entryDrafts[player.id].tierId !== tierId)) return tierId;
	}

	#scrollAtEdges(area: HTMLElement, press: PointerEvent, origin: string): void {
		// Past the edge of the area, e.g. in the margin of the page, it keeps scrolling.
		const bounds = area.getBoundingClientRect();
		const scroller = document
			.elementFromPoint(
				Math.max(bounds.left + 1, Math.min(this.x, bounds.right - 1)),
				Math.max(bounds.top + 1, Math.min(this.y, bounds.bottom - 1))
			)
			?.closest<HTMLElement>('[data-drag-scroll]');
		// Nothing can be dropped in the list the players come from.
		const list = scroller?.closest<HTMLElement>('[data-drop-tier]');
		if (!scroller || !area.contains(scroller) || list?.dataset.dropTier === origin) return;
		const { left, right, top, bottom } = scroller.getBoundingClientRect();
		scroller.scrollBy(
			edgeScrollStep(this.x, press.clientX, left, right),
			edgeScrollStep(this.y, press.clientY, top, bottom)
		);
	}

	/** Takes the preview to the row of the grabbed player, then ends the drag. */
	async #settle(area: HTMLElement, playerId: string, tierId: string): Promise<void> {
		await tick();
		const row = area.querySelector(
			`[data-drop-tier="${CSS.escape(tierId)}"] [data-player-id="${CSS.escape(playerId)}"]`
		);
		if (row && this.preview && !motionPreferences.reducedMotion) {
			const { left, top } = row.getBoundingClientRect();
			await this.preview.animate(
				{ transform: `translate(${left}px, ${top}px)` },
				{ duration: SETTLE_MS, easing: 'cubic-bezier(0.19, 1, 0.22, 1)', fill: 'forwards' }
			).finished;
		}
		this.players = [];
	}
}

/** The release that ends a drag must not also click what is under the pointer. */
function skipNextClick(): void {
	const skip = new AbortController();
	window.addEventListener('click', (event) => event.stopPropagation(), {
		capture: true,
		signal: skip.signal
	});
	setTimeout(() => skip.abort());
}
