import { tick } from 'svelte';
import { Spring } from 'svelte/motion';
import type { Action } from 'svelte/action';
import { clampOffsetRange, indexForOffset, moveItem } from '$lib/dragList';
import { rubberband, springPresets, velocityFromHistory } from '$lib/motion';
import { motionPreferences } from '$lib/motionPreferences.svelte';

/**
 * Direct-manipulation drag-to-reorder for a vertical list (WWDC18 "Designing
 * Fluid Interfaces" — 1:1 tracking, rubber-banding at the bounds, a spring
 * settle on release with a touch of bounce only when the release carried real
 * velocity).
 *
 * Attach to the list's container. Each row must carry `data-drag-id="<id>"`
 * and contain one descendant marked `data-drag-handle`.
 *
 * Deliberately does NOT reorder the underlying (keyed) list live while the
 * pointer is down: moving the dragged row's own DOM node — which is exactly
 * what a keyed `{#each}` does the instant its backing array reorders —
 * reliably drops its active pointer capture mid-gesture in Chromium, freezing
 * the drag. So during the drag this only ever shifts the *other* rows with
 * plain transforms to open a gap (the dragged row tracks the pointer 1:1, also
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
const SIBLING_TRANSITION = 'transform 220ms cubic-bezier(0.19, 1, 0.22, 1)';

export const dragReorder: Action<HTMLElement, DragReorderOptions> = (container, options) => {
	let current = options;

	function rows(): HTMLElement[] {
		return Array.from(container.querySelectorAll<HTMLElement>('[data-drag-id]'));
	}

	function onPointerDown(event: PointerEvent): void {
		if (current.disabled?.()) return;
		if (event.pointerType === 'mouse' && event.button !== 0) return;
		const handleTarget = (event.target as HTMLElement).closest<HTMLElement>('[data-drag-handle]');
		if (!handleTarget || !container.contains(handleTarget)) return;
		const rowTarget = handleTarget.closest<HTMLElement>('[data-drag-id]');
		const draggedId = rowTarget?.dataset.dragId;
		if (!rowTarget || !draggedId) return;
		// Re-bind as non-nullable `const`s: TS narrowing above doesn't survive into the
		// closures declared below, even though these can never be reassigned.
		const handle: HTMLElement = handleTarget;
		const row: HTMLElement = rowTarget;

		const allRows = rows();
		if (allRows.length < 2) return;
		const siblings = allRows.filter((el) => el !== row);

		const startIds = current.ids();
		const startIndex = startIds.indexOf(draggedId);
		if (startIndex === -1) return;

		const slotSize =
			(allRows[1]?.getBoundingClientRect().top ?? 0) -
				(allRows[0]?.getBoundingClientRect().top ?? 0) || row.getBoundingClientRect().height;
		const count = allRows.length;
		const startClientY = event.clientY;
		const history: { position: number; time: number }[] = [
			{ position: startClientY, time: performance.now() }
		];

		let liveIndex = startIndex;
		let liveDelta = 0;

		handle.setPointerCapture(event.pointerId);
		row.classList.add('is-dragging');

		/** Shifts the *other* rows to open a gap at `targetIndex`, tracking the live preview. */
		function shiftSiblings(targetIndex: number): void {
			for (const sibling of siblings) {
				const originalIndex = allRows.indexOf(sibling);
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
				sibling.style.transform = shift ? `translateY(${shift}px)` : '';
			}
		}

		function clearSiblingShifts(): void {
			for (const sibling of siblings) {
				sibling.style.transform = '';
				sibling.style.transition = '';
			}
		}

		function onPointerMove(moveEvent: PointerEvent): void {
			const raw = moveEvent.clientY - startClientY;
			const { min, max } = clampOffsetRange(startIndex, count, slotSize);
			const clamped =
				raw < min
					? min + rubberband(raw - min, slotSize)
					: raw > max
						? max + rubberband(raw - max, slotSize)
						: raw;

			const now = performance.now();
			history.push({ position: moveEvent.clientY, time: now });
			while (history.length > 2 && now - history[0].time > HISTORY_WINDOW_MS) history.shift();

			const nextIndex = indexForOffset(startIndex, clamped, slotSize, count);
			if (nextIndex !== liveIndex) {
				liveIndex = nextIndex;
				shiftSiblings(liveIndex);
			}
			liveDelta = clamped;
			row.style.transform = `translateY(${clamped}px)`;
		}

		async function onPointerUp(): Promise<void> {
			handle.releasePointerCapture(event.pointerId);
			handle.removeEventListener('pointermove', onPointerMove);
			handle.removeEventListener('pointerup', onPointerUp);
			handle.removeEventListener('pointercancel', onPointerUp);

			const releaseVelocity = velocityFromHistory(history);
			const bouncy = Math.abs(releaseVelocity) > VELOCITY_THRESHOLD;
			// The row's own DOM position never moved during the drag — bridge from where it
			// visually sits now to where it'll actually land once the real reorder below lands
			// it in its new slot (§Interruptibility: always animate from the presentation value).
			const bridgeFrom = liveDelta - (liveIndex - startIndex) * slotSize;

			current.onCommit(moveItem(startIds, startIndex, liveIndex));
			await tick();
			clearSiblingShifts();
			row.style.transform = `translateY(${bridgeFrom}px)`;

			if (motionPreferences.reducedMotion) {
				row.classList.remove('is-dragging');
				row.style.transform = '';
				return;
			}

			const settle = new Spring(bridgeFrom, bouncy ? springPresets.momentum : springPresets.settle);
			let raf = requestAnimationFrame(paint);
			function paint(): void {
				row.style.transform = `translateY(${settle.current}px)`;
				raf = requestAnimationFrame(paint);
			}
			settle.set(0).finally(() => {
				cancelAnimationFrame(raf);
				row.classList.remove('is-dragging');
				row.style.transform = '';
			});
		}

		handle.addEventListener('pointermove', onPointerMove);
		handle.addEventListener('pointerup', onPointerUp);
		handle.addEventListener('pointercancel', onPointerUp);
	}

	/** Keyboard fallback: focus a handle, Arrow Up/Down moves it one slot — no pointer required. */
	function onKeyDown(event: KeyboardEvent): void {
		if (current.disabled?.()) return;
		if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') return;
		const handle = (event.target as HTMLElement).closest<HTMLElement>('[data-drag-handle]');
		if (!handle || !container.contains(handle)) return;
		const row = handle.closest<HTMLElement>('[data-drag-id]');
		const id = row?.dataset.dragId;
		if (!row || !id) return;

		const ids = current.ids();
		const index = ids.indexOf(id);
		const targetIndex = index + (event.key === 'ArrowUp' ? -1 : 1);
		if (targetIndex < 0 || targetIndex >= ids.length) return;

		event.preventDefault();
		current.onCommit(moveItem(ids, index, targetIndex));
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
