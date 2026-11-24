/**
 * Pure helpers for the drags of the strategy editor (the tier list, and the
 * players between the tiers). No DOM, no Svelte — the component owns pointer events and
 * spring wiring; this module only does the array/geometry math, so it's easy to
 * reason about and to unit-test in isolation.
 */

/** Returns a new array with the item at `from` moved to `to`. Never mutates `list`. */
export function moveItem<T>(list: readonly T[], from: number, to: number): T[] {
	if (from === to || from < 0 || from >= list.length || to < 0 || to >= list.length) {
		return [...list];
	}
	const next = [...list];
	const [moved] = next.splice(from, 1);
	next.splice(to, 0, moved);
	return next;
}

/**
 * Given how far (in px) the dragged item's center has moved from its original
 * slot, and the uniform size of each slot (item height + gap), returns which
 * index it should currently occupy.
 */
export function indexForOffset(
	startIndex: number,
	offset: number,
	slotSize: number,
	count: number
): number {
	if (slotSize <= 0) return startIndex;
	const shift = Math.round(offset / slotSize);
	const target = startIndex + shift;
	return Math.min(count - 1, Math.max(0, target));
}

const SCROLL_EDGE = 60; // px from the edge of the scroller
const SCROLL_STEP = 14; // px per frame

/**
 * How far to scroll on one axis, in the next frame, a scroller from `min` to `max` while a drag
 * from `start` is at `position`: the nearer to an edge, the faster. An item grabbed near an edge
 * scrolls only once it moves towards that edge.
 */
export function edgeScrollStep(position: number, start: number, min: number, max: number): number {
	const startsInside = start >= min && start <= max;
	const step = (depth: number) =>
		Math.ceil(SCROLL_STEP * Math.min(1, Math.max(0, depth / SCROLL_EDGE)));
	const backward = !startsInside || position < start ? step(min + SCROLL_EDGE - position) : 0;
	const forward = !startsInside || position > start ? step(position - max + SCROLL_EDGE) : 0;
	return forward - backward;
}

/** Clamps a drag offset to the travel available between the list's first and last slot. */
export function clampOffsetRange(
	startIndex: number,
	count: number,
	slotSize: number
): { min: number; max: number } {
	return {
		min: -startIndex * slotSize,
		max: (count - 1 - startIndex) * slotSize
	};
}
