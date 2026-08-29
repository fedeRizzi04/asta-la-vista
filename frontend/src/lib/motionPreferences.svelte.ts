/**
 * Reactive mirror of `prefers-reduced-motion`, for the JS-driven motion (drag
 * reorder, spring presets) that CSS media queries alone can't gate. CSS still
 * owns its own `@media (prefers-reduced-motion: reduce)` blocks independently —
 * this exists only for logic that has to branch in script.
 */

function watchMediaQuery(query: string): { readonly matches: boolean } {
	let matches = $state(false);

	if (typeof window !== 'undefined' && 'matchMedia' in window) {
		const media = window.matchMedia(query);
		matches = media.matches;
		media.addEventListener('change', (event) => {
			matches = event.matches;
		});
	}

	return {
		get matches() {
			return matches;
		}
	};
}

const reducedMotionQuery = watchMediaQuery('(prefers-reduced-motion: reduce)');

export const motionPreferences = {
	get reducedMotion(): boolean {
		return reducedMotionQuery.matches;
	}
};
