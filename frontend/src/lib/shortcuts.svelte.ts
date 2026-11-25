import { SvelteMap, SvelteSet } from 'svelte/reactivity';

export type Shortcut = {
	keys: string;
	description: string;
	group?: string;
	handler: () => void;
	when?: () => boolean;
	/** Also fires while a dialog is open, which blocks every other shortcut. */
	inDialog?: boolean;
	/** Keeps the shortcut for the browser in a field with text, e.g. ⌘Z undoes the typing there. */
	emptyFieldOnly?: boolean;
};

const isMac = typeof navigator !== 'undefined' && /Mac/i.test(navigator.platform);
const modifierLabels: Record<string, string> = {
	mod: isMac ? '⌘' : 'Ctrl',
	shift: isMac ? '⇧' : 'Shift',
	alt: isMac ? '⌥' : 'Alt'
};
// On macOS the modifiers are symbols (⌘ ⌥ ⇧), but the other keys are words: the symbols for
// escape and return (⎋ ⏎) are not printed on the keyboard, so nobody recognises them.
const keyLabels: Record<string, string> = {
	escape: isMac ? 'esc' : 'Esc',
	enter: isMac ? 'invio' : 'Invio',
	tab: isMac ? 'tab' : 'Tab',
	arrowup: '↑',
	arrowdown: '↓',
	arrowleft: '←',
	arrowright: '→',
	' ': 'Spazio'
};
const punctuationCodes: Record<string, string> = {
	'/': 'slash',
	'\\': 'backslash',
	',': 'comma',
	'.': 'period',
	';': 'semicolon',
	"'": 'quote',
	'[': 'bracketleft',
	']': 'bracketright',
	'-': 'minus',
	'=': 'equal',
	'`': 'backquote',
	' ': 'space'
};

const registrations = new SvelteSet<Shortcut[]>();
const shortcuts = $derived.by(() => {
	const latest = new SvelteMap<string, Shortcut>();
	for (const registration of registrations) {
		for (const shortcut of registration) {
			const { key, modifiers } = parseKeys(shortcut.keys);
			const spec = [...modifiers.sort(), key].join('+');
			latest.delete(spec);
			latest.set(spec, shortcut);
		}
	}
	return [...latest.values()];
});

export const shortcutsPanel = $state({ open: false });

export function registerShortcuts(shortcuts: Shortcut[]): () => void {
	const registration = [...shortcuts];
	registrations.add(registration);
	return () => {
		registrations.delete(registration);
	};
}

export function getShortcuts(): Shortcut[] {
	return shortcuts.filter((shortcut) => shortcut.when?.() ?? true);
}

function parseKeys(spec: string): { key: string; modifiers: string[] } {
	const modifiers = spec.toLowerCase().split(/\+(?=.)/);
	const key = modifiers.pop() ?? '';
	return { key, modifiers };
}

export function shortcutKeys(spec: string): string[] {
	const { key, modifiers } = parseKeys(spec);
	return [
		...modifiers.map((modifier) => modifierLabels[modifier]),
		keyLabels[key] ?? key.toUpperCase()
	];
}

/**
 * On macOS the symbols are joined as they are ("⌘K"), but a word needs a space ("⌘ invio");
 * elsewhere the keys are joined with "+" ("Ctrl+Invio").
 */
export function shortcutLabel(spec: string): string {
	const keys = shortcutKeys(spec);
	const hasWord = keys.some((key) => /\p{L}{2,}/u.test(key));
	return keys.join(isMac ? (hasWord ? ' ' : '') : '+');
}

/** A tooltip text: the label followed by the shortcut, e.g. "Registro acquisti (⌘J)". */
export function withShortcut(label: string, spec: string): string {
	return `${label} (${shortcutLabel(spec)})`;
}

function keyCode(key: string): string {
	if (/^[a-z]$/.test(key)) return `key${key}`;
	if (/^\d$/.test(key)) return `digit${key}`;
	return punctuationCodes[key] ?? key;
}

function matches(event: KeyboardEvent, spec: string, typing: boolean): boolean {
	const { key, modifiers } = parseKeys(spec);
	const mod = modifiers.includes('mod');
	const alt = modifiers.includes('alt');
	const shift = modifiers.includes('shift');
	// Punctuation can require Shift on some layouts, so use the resulting character.
	const impliedShift = !alt && /^[\p{P}\p{S}]$/u.test(key);
	return (
		(!typing || mod || key === 'escape') &&
		event.metaKey === (mod && isMac) &&
		event.ctrlKey === (mod && !isMac) &&
		event.altKey === alt &&
		(event.shiftKey === shift || (!shift && impliedShift)) &&
		(alt ? event.code.toLowerCase() === keyCode(key) : event.key.toLowerCase() === key)
	);
}

function handleKeydown(event: KeyboardEvent): void {
	if (event.defaultPrevented || event.isComposing || event.repeat) return;

	const target = event.target;
	const typing =
		target instanceof HTMLElement &&
		(target.matches('input, textarea, select') || target.isContentEditable);
	const shortcut = shortcuts.findLast(({ keys }) => matches(event, keys, typing));
	if (!shortcut || shortcut.when?.() === false) return;
	if (document.querySelector('dialog[open]') && !shortcut.inDialog) return;
	if (typing && shortcut.emptyFieldOnly && (target as HTMLInputElement).value) return;
	event.preventDefault();
	shortcut.handler();
}

export function installShortcuts(): () => void {
	window.addEventListener('keydown', handleKeydown);
	return () => window.removeEventListener('keydown', handleKeydown);
}
