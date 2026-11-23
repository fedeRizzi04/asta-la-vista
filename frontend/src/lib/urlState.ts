import { goto } from '$app/navigation';
import { page } from '$app/state';

/** Reads a copy of the current search params. Call inside $derived for reactive reads. */
export function getUrlParams(): URLSearchParams {
	return new URLSearchParams(page.url.searchParams);
}

/** Replaces the given params. Arrays use repeated keys, and null or empty values remove a key. */
export function setUrlParams(
	params: Record<string, string | readonly string[] | null>
): Promise<void> {
	const url = new URL(page.url);
	for (const [key, value] of Object.entries(params)) {
		url.searchParams.delete(key);
		for (const item of typeof value === 'string' ? [value] : (value ?? [])) {
			if (item !== '') url.searchParams.append(key, item);
		}
	}
	// eslint-disable-next-line svelte/no-navigation-without-resolve -- page.url already includes the base path.
	return goto(url, { replaceState: true, keepFocus: true, noScroll: true });
}
