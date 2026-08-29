import { Spring } from 'svelte/motion';
import type { Action } from 'svelte/action';
import { springPresets } from '$lib/motion';
import { motionPreferences } from '$lib/motionPreferences.svelte';

/**
 * Positions an absolutely-positioned indicator element under/behind whichever
 * sibling is currently "active", sliding between them with a spring instead of
 * jumping — the segmented-control pattern used for the top nav and role tabs.
 *
 * Usage: place `<span class="tab-indicator" use:slidingIndicator={activeEl}>` as a
 * child of a `position: relative` container; pass the current active element
 * (or `undefined` while none is active/measurable yet).
 */
export const slidingIndicator: Action<HTMLElement, HTMLElement | undefined> = (node, activeEl) => {
	const rect = new Spring({ left: 0, width: 0 }, springPresets.indicator);
	let resizeObserver: ResizeObserver | undefined;

	function measure(target: HTMLElement | undefined, animate: boolean): void {
		if (!target) return;
		const parent = node.offsetParent as HTMLElement | null;
		const parentBox = parent?.getBoundingClientRect();
		const targetBox = target.getBoundingClientRect();
		const next = {
			left: targetBox.left - (parentBox?.left ?? 0),
			width: targetBox.width
		};
		if (animate && !motionPreferences.reducedMotion) {
			rect.target = next;
		} else {
			rect.set(next, { instant: true });
		}
	}

	function apply(): void {
		node.style.transform = `translateX(${rect.current.left}px)`;
		node.style.width = `${rect.current.width}px`;
	}

	$effect(() => {
		apply();
	});

	measure(activeEl, false);
	node.style.opacity = activeEl ? '1' : '0';

	if (activeEl && typeof ResizeObserver !== 'undefined') {
		resizeObserver = new ResizeObserver(() => measure(activeEl, false));
		resizeObserver.observe(activeEl);
	}

	return {
		update(nextActiveEl) {
			node.style.opacity = nextActiveEl ? '1' : '0';
			resizeObserver?.disconnect();
			measure(nextActiveEl, true);
			if (nextActiveEl && typeof ResizeObserver !== 'undefined') {
				resizeObserver = new ResizeObserver(() => measure(nextActiveEl, false));
				resizeObserver.observe(nextActiveEl);
			}
		},
		destroy() {
			resizeObserver?.disconnect();
		}
	};
};
