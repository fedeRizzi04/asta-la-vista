import { SvelteMap } from 'svelte/reactivity';

/**
 * Backs every collapsible panel's show/hide state (see CollapsibleSection.svelte), keyed
 * by a caller-chosen id such as `strategy:${id}:global-tiers`. Living in a module-level
 * reactive map means the choice survives client-side navigation between pages — going to
 * another strategy and back keeps what you picked — while a full page reload still starts
 * fresh, with no localStorage plumbing needed for that.
 */
const visibility = new SvelteMap<string, boolean>();

export function panelVisibility(key: string, defaultVisible = true) {
	return {
		get visible(): boolean {
			return visibility.get(key) ?? defaultVisible;
		},
		toggle(): void {
			visibility.set(key, !(visibility.get(key) ?? defaultVisible));
		}
	};
}
