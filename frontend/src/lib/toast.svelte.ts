export type ToastKind = 'error' | 'success';

export type ToastItem = {
	id: number;
	kind: ToastKind;
	message: string;
};

let nextId = 1;

/** How long each toast kind stays on screen before it auto-dismisses. Change here only. */
const AUTO_DISMISS_MS: Record<ToastKind, number> = {
	error: 10000,
	success: 5000
};

export const toastState = $state<{ items: ToastItem[] }>({ items: [] });

export function pushToast(message: string, kind: ToastKind = 'error'): number {
	const id = nextId++;
	toastState.items = [...toastState.items, { id, kind, message }];
	const delay = AUTO_DISMISS_MS[kind];
	if (delay) setTimeout(() => dismissToast(id), delay);
	return id;
}

export function dismissToast(id: number): void {
	toastState.items = toastState.items.filter((item) => item.id !== id);
}

function errorMessage(caught: unknown): string {
	return caught instanceof Error ? caught.message : 'Si è verificato un errore inatteso.';
}

/** Shorthand for the common `pushToast(errorMessage(caught))` catch-block pattern. */
export function pushErrorToast(caught: unknown): number {
	return pushToast(errorMessage(caught));
}
