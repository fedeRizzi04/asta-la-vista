import { tick } from 'svelte';
import { Spring } from 'svelte/motion';
import type { Action } from 'svelte/action';
import { clampOffsetRange, indexForOffset, moveItem } from '$lib/dragList';
import { rubberband, springPresets, velocityFromHistory } from '$lib/motion';
import { motionPreferences } from '$lib/motionPreferences.svelte';

/**
 * Direct-manipulation drag-to-reorder for a horizontal list (WWDC18 "Designing
 * Fluid Interfaces" — 1:1 tracking, rubber-banding at the bounds, a spring
 * settle on release with a touch of bounce only when the release carried real
 * velocity).
 *
 * Attach to an ancestor of the items. Each item must carry `data-drag-id="<id>"`
 * and contain one descendant marked `data-drag-handle`. If the items scroll, the
 * drag scrolls them when the pointer nears an edge.
 *
 * Deliberately does NOT reorder the underlying (keyed) list live while the
 * pointer is down: moving the dragged item's own DOM node — which is exactly
 * what a keyed `{#each}` does the instant its backing array reorders —
 * reliably drops its active pointer capture mid-gesture in Chromium, freezing
 * the drag. So during the drag this only ever shifts the *other* items with
 * plain transforms to open a gap (the dragged item tracks the pointer 1:1, also
 * via a plain transform); the real array only reorders once, on release.
 */
export interface DragReorderOptions {
	/** Current id order — the single source of truth this action reorders. */
	ids: () => string[];
	/** Called once, on release, with the final order — the moment to persist it. */
	onCommit: (nextIds: string[]) => void;
	disabled?: () => boolean;
}

const VELOCITY_THRESHOLD = 300; // px/s — above this, the release keeps a touch of bounce
const HISTORY_WINDOW_MS = 80;
const SCROLL_EDGE = 60; // px from the edge of the scroller
const SCROLL_STEP = 14; // px per frame
const SIBLING_TRANSITION = 'transform 220ms cubic-bezier(0.19, 1, 0.22, 1)';

/** The element that scrolls `element` sideways, if any. */
function horizontalScroller(element: HTMLElement): HTMLElement | undefined {
	for (let parent = element.parentElement; parent; parent = parent.parentElement) {
		const scrolls = ['auto', 'scroll'].includes(getComputedStyle(parent).overflowX);
		if (scrolls && parent.scrollWidth > parent.clientWidth) return parent;
	}
}

export const dragReorder: Action<HTMLElement, DragReorderOptions> = (container, options) => {
	let current = options;

	function items(): HTMLElement[] {
		return Array.from(container.querySelectorAll<HTMLElement>('[data-drag-id]'));
	}

	function onPointerDown(event: PointerEvent): void {
		if (current.disabled?.()) return;
		if (event.pointerType === 'mouse' && event.button !== 0) return;
		const handleTarget = (event.target as HTMLElement).closest<HTMLElement>('[data-drag-handle]');
		if (!handleTarget || !container.contains(handleTarget)) return;
		const itemTarget = handleTarget.closest<HTMLElement>('[data-drag-id]');
		const draggedId = itemTarget?.dataset.dragId;
		if (!itemTarget || !draggedId) return;
		// Re-bind as non-nullable `const`s: TS narrowing above doesn't survive into the
		// closures declared below, even though these can never be reassigned.
		const handle: HTMLElement = handleTarget;
		const item: HTMLElement = itemTarget;

		const allItems = items();
		if (allItems.length < 2) return;
		const siblings = allItems.filter((el) => el !== item);

		const startIds = current.ids();
		const startIndex = startIds.indexOf(draggedId);
		if (startIndex === -1) return;

		const slotSize =
			(allItems[1]?.getBoundingClientRect().left ?? 0) -
				(allItems[0]?.getBoundingClientRect().left ?? 0) || item.getBoundingClientRect().width;
		const count = allItems.length;
		const scroller = horizontalScroller(item);
		const startScrollLeft = scroller?.scrollLeft ?? 0;
		const startClientX = event.clientX;
		const history: { position: number; time: number }[] = [
			{ position: startClientX, time: performance.now() }
		];

		let liveIndex = startIndex;
		let liveDelta = 0;
		let clientX = startClientX;
		let scrollFrame = requestAnimationFrame(scrollAtEdges);

		handle.setPointerCapture(event.pointerId);
		item.classList.add('is-dragging');

		/** Shifts the *other* items to open a gap at `targetIndex`, tracking the live preview. */
		function shiftSiblings(targetIndex: number): void {
			for (const sibling of siblings) {
				const originalIndex = allItems.indexOf(sibling);
				let shift = 0;
				if (
					startIndex < targetIndex &&
					originalIndex > startIndex &&
					originalIndex <= targetIndex
				) {
					shift = -slotSize;
				} else if (
					startIndex > targetIndex &&
					originalIndex >= targetIndex &&
					originalIndex < startIndex
				) {
					shift = slotSize;
				}
				sibling.style.transition = SIBLING_TRANSITION;
				sibling.style.transform = shift ? `translateX(${shift}px)` : '';
			}
		}

		function clearSiblingShifts(): void {
			for (const sibling of siblings) {
				sibling.style.transform = '';
				sibling.style.transition = '';
			}
		}

		function scrollAtEdges(): void {
			if (!scroller) return;
			const { left, right } = scroller.getBoundingClientRect();
			const before = scroller.scrollLeft;
			// A handle pressed near an edge scrolls only once it moves towards that edge.
			if (clientX < Math.min(left + SCROLL_EDGE, startClientX)) scroller.scrollLeft -= SCROLL_STEP;
			else if (clientX > Math.max(right - SCROLL_EDGE, startClientX))
				scroller.scrollLeft += SCROLL_STEP;
			if (scroller.scrollLeft !== before) track();
			scrollFrame = requestAnimationFrame(scrollAtEdges);
		}

		function onPointerMove(moveEvent: PointerEvent): void {
			clientX = moveEvent.clientX;
			const now = performance.now();
			history.push({ position: clientX, time: now });
			while (history.length > 2 && now - history[0].time > HISTORY_WINDOW_MS) history.shift();
			track();
		}

		/** Moves the item to where the pointer is, and the others out of its way. */
		function track(): void {
			const raw = clientX - startClientX + (scroller?.scrollLeft ?? 0) - startScrollLeft;
			const { min, max } = clampOffsetRange(startIndex, count, slotSize);
			const clamped =
				raw < min
					? min + rubberband(raw - min, slotSize)
					: raw > max
						? max + rubberband(raw - max, slotSize)
						: raw;

			const nextIndex = indexForOffset(startIndex, clamped, slotSize, count);
			if (nextIndex !== liveIndex) {
				liveIndex = nextIndex;
				shiftSiblings(liveIndex);
			}
			liveDelta = clamped;
			item.style.transform = `translateX(${clamped}px)`;
		}

		async function onPointerUp(): Promise<void> {
			cancelAnimationFrame(scrollFrame);
			handle.releasePointerCapture(event.pointerId);
			handle.removeEventListener('pointermove', onPointerMove);
			handle.removeEventListener('pointerup', onPointerUp);
			handle.removeEventListener('pointercancel', onPointerUp);

			const releaseVelocity = velocityFromHistory(history);
			const bouncy = Math.abs(releaseVelocity) > VELOCITY_THRESHOLD;
			// The item's own DOM position never moved during the drag — bridge from where it
			// visually sits now to where it'll actually land once the real reorder below lands
			// it in its new slot (§Interruptibility: always animate from the presentation value).
			const bridgeFrom = liveDelta - (liveIndex - startIndex) * slotSize;

			if (liveIndex !== startIndex) current.onCommit(moveItem(startIds, startIndex, liveIndex));
			await tick();
			clearSiblingShifts();
			item.style.transform = `translateX(${bridgeFrom}px)`;

			if (motionPreferences.reducedMotion) {
				item.classList.remove('is-dragging');
				item.style.transform = '';
				return;
			}

			const settle = new Spring(bridgeFrom, bouncy ? springPresets.momentum : springPresets.settle);
			let raf = requestAnimationFrame(paint);
			function paint(): void {
				item.style.transform = `translateX(${settle.current}px)`;
				raf = requestAnimationFrame(paint);
			}
			settle.set(0).finally(() => {
				cancelAnimationFrame(raf);
				item.classList.remove('is-dragging');
				item.style.transform = '';
			});
		}

		handle.addEventListener('pointermove', onPointerMove);
		handle.addEventListener('pointerup', onPointerUp);
		handle.addEventListener('pointercancel', onPointerUp);
	}

	/** Keyboard fallback: focus a handle, Arrow Left/Right moves it one slot — no pointer required. */
	async function onKeyDown(event: KeyboardEvent): Promise<void> {
		if (current.disabled?.()) return;
		if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
		const handle = (event.target as HTMLElement).closest<HTMLElement>('[data-drag-handle]');
		if (!handle || !container.contains(handle)) return;
		const id = handle.closest<HTMLElement>('[data-drag-id]')?.dataset.dragId;
		if (!id) return;

		const ids = current.ids();
		const index = ids.indexOf(id);
		const targetIndex = index + (event.key === 'ArrowLeft' ? -1 : 1);
		if (targetIndex < 0 || targetIndex >= ids.length) return;

		event.preventDefault();
		current.onCommit(moveItem(ids, index, targetIndex));
		await tick();
		// Moving the item in the DOM can drop the focus, which also scrolls it into view.
		handle.focus();
	}

	container.addEventListener('pointerdown', onPointerDown);
	container.addEventListener('keydown', onKeyDown);

	return {
		update(next) {
			current = next;
		},
		destroy() {
			container.removeEventListener('pointerdown', onPointerDown);
			container.removeEventListener('keydown', onKeyDown);
		}
	};
};
