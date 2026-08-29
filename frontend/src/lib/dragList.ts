/**
 * Pure helpers for a vertical drag-to-reorder list (the tier list in the
 * strategy editor). No DOM, no Svelte — the component owns pointer events and
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
