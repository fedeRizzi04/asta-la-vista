import { browser } from '$app/environment';
import { SvelteMap } from 'svelte/reactivity';

const STORAGE_KEY = 'panel-visibility';
let savedVisibility: SvelteMap<string, boolean> | undefined;

function loadVisibility(): SvelteMap<string, boolean> {
	try {
		const saved: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}');
		if (saved && typeof saved === 'object') {
			return new SvelteMap(
				Object.entries(saved).filter((entry): entry is [string, boolean] => {
					return typeof entry[1] === 'boolean';
				})
			);
		}
	} catch {
		// Unavailable storage or invalid JSON falls back to the panel defaults.
	}
	return new SvelteMap();
}

/**
 * Remembers each panel's show/hide choice by key across navigation and reloads.
 * Storage is loaded on first browser use. If it is unavailable, choices stay in memory.
 */
export function panelVisibility(key: string, defaultVisible = true) {
	const visibility = browser
		? (savedVisibility ??= loadVisibility())
		: new SvelteMap<string, boolean>();
	return {
		get visible(): boolean {
			return visibility.get(key) ?? defaultVisible;
		},
		toggle(): void {
			visibility.set(key, !(visibility.get(key) ?? defaultVisible));
			if (!browser) return;
			try {
				localStorage.setItem(STORAGE_KEY, JSON.stringify(Object.fromEntries(visibility)));
			} catch {
				// Keep the in-memory choice when storage is unavailable.
			}
		}
	};
}
