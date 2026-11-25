import { en, type ErrorParams, type Messages } from './en';
import { it } from './it';

const catalogs = { en, it };
export type Locale = keyof typeof catalogs;

function savedLocale(): string | null {
	try {
		return localStorage.getItem('locale');
	} catch {
		// Storage can be unavailable (e.g. blocked site data): as if no language was chosen.
		return null;
	}
}

function initialLocale(): Locale {
	const preferred = savedLocale() ?? navigator.language.slice(0, 2);
	return preferred === 'it' ? 'it' : 'en';
}

export const locale = initialLocale();
export const t: Messages = catalogs[locale];
document.documentElement.lang = locale;

/** Reloads the page, so every text is a plain constant that never changes while the app runs. */
export function setLocale(next: Locale): void {
	try {
		localStorage.setItem('locale', next);
	} catch {
		// The choice cannot be kept: the reload brings the selector back to the language in use.
	}
	location.reload();
}

/** The text for an error code of the API, which may be missing from this catalog. */
export function errorText(code: string | undefined, params: ErrorParams = {}): string {
	const errors: Record<string, string | ((params: ErrorParams) => string)> = t.errors;
	const text = errors[code ?? ''] ?? t.errors.unexpected;
	return typeof text === 'string' ? text : text(params);
}
