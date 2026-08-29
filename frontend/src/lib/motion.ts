/**
 * Pure motion math shared across the app — no DOM, no Svelte runes, no framework
 * dependency. Components and actions build on these primitives; this module never
 * imports either, so it stays trivially testable and reusable.
 *
 * Concepts follow Apple's "Designing Fluid Interfaces" (WWDC18): critically-damped
 * springs by default, momentum projection on release, and rubber-banding at bounds.
 */

/** A Svelte `Spring` accepts `stiffness`/`damping` in [0, 1], not physical units. */
export type SpringConfig = { stiffness: number; damping: number };

/**
 * Spring presets, named by intent rather than by number. Each approximates an
 * Apple damping-ratio/response pair (noted in the comment) translated into
 * Svelte's stiffness/damping model.
 */
export const springPresets = {
	/** Damping ~1.0, response ~0.35s — the default for anything that isn't gesture momentum. */
	settle: { stiffness: 0.22, damping: 0.86 },
	/** Damping ~0.8, response ~0.35s — a touch of overshoot, for releases that carry velocity. */
	momentum: { stiffness: 0.3, damping: 0.72 },
	/** Damping ~0.8, response ~0.3s — sheets, drawers, dialogs materializing. */
	drawer: { stiffness: 0.34, damping: 0.74 },
	/** Damping 1.0, snappier response — small UI chrome like a sliding tab indicator. */
	indicator: { stiffness: 0.28, damping: 0.92 }
} as const satisfies Record<string, SpringConfig>;

/**
 * Apple's exponential-decay momentum projection: where would this gesture come to
 * rest if released right now? `velocity` is in px/s. `decelerationRate` mirrors
 * iOS scroll deceleration (`0.998` normal, `0.99` snappier).
 */
export function projectMomentum(velocity: number, decelerationRate = 0.998): number {
	return ((velocity / 1000) * decelerationRate) / (1 - decelerationRate);
}

/**
 * Progressive resistance past a boundary — the further the overshoot, the less it
 * follows. `dimension` is the size of the resisting region (e.g. list height),
 * `constant` tunes how quickly resistance ramps up (Apple ships ~0.55).
 */
export function rubberband(overshoot: number, dimension: number, constant = 0.55): number {
	if (dimension <= 0) return 0;
	const sign = overshoot < 0 ? -1 : 1;
	const magnitude = Math.abs(overshoot);
	return (sign * (magnitude * dimension * constant)) / (dimension + constant * magnitude);
}

/** Average velocity (px/s) from a short history of timestamped positions. */
export function velocityFromHistory(history: { position: number; time: number }[]): number {
	if (history.length < 2) return 0;
	const first = history[0];
	const last = history[history.length - 1];
	const dt = last.time - first.time;
	if (dt <= 0) return 0;
	return ((last.position - first.position) / dt) * 1000;
}
