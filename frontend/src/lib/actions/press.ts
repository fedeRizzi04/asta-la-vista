import type { Action } from 'svelte/action';

/**
 * Instant press feedback (WWDC18 "Designing Fluid Interfaces" §Response): mark an
 * element as pressed the moment the pointer goes down, never on click/release.
 * Pairs with the `.is-pressed` rules in `app.css`.
 */
export const press: Action<HTMLElement, { disabled?: boolean } | undefined> = (node, params) => {
	let disabled = params?.disabled ?? false;

	function setPressed(value: boolean): void {
		node.classList.toggle('is-pressed', value && !disabled);
	}

	function onPointerDown(event: PointerEvent): void {
		if (disabled || (event.pointerType === 'mouse' && event.button !== 0)) return;
		setPressed(true);
	}

	function release(): void {
		setPressed(false);
	}

	node.addEventListener('pointerdown', onPointerDown);
	node.addEventListener('pointerup', release);
	node.addEventListener('pointercancel', release);
	node.addEventListener('pointerleave', release);

	return {
		update(next) {
			disabled = next?.disabled ?? false;
			if (disabled) setPressed(false);
		},
		destroy() {
			node.removeEventListener('pointerdown', onPointerDown);
			node.removeEventListener('pointerup', release);
			node.removeEventListener('pointercancel', release);
			node.removeEventListener('pointerleave', release);
		}
	};
};
