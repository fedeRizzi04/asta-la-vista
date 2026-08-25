export type DialogOptions = {
	title?: string;
	message: string;
	confirmLabel?: string;
	cancelLabel?: string;
	/** Highlights the confirm button as a destructive action. */
	danger?: boolean;
};

type ConfirmRequest = DialogOptions & { kind: 'confirm'; resolve: (value: boolean) => void };
type PromptRequest = DialogOptions & {
	kind: 'prompt';
	placeholder?: string;
	resolve: (value: string | null) => void;
};

export const dialogState = $state<{
	request: ConfirmRequest | PromptRequest | null;
	inputValue: string;
}>({ request: null, inputValue: '' });

/** Replaces window.confirm(): resolves true when the user confirms, false otherwise. */
export function confirmDialog(options: DialogOptions): Promise<boolean> {
	return new Promise((resolve) => {
		dialogState.request = { kind: 'confirm', ...options, resolve };
	});
}

/** Replaces window.prompt(): resolves the trimmed input, or null when cancelled/empty. */
export function promptDialog(
	options: DialogOptions & { defaultValue?: string; placeholder?: string }
): Promise<string | null> {
	return new Promise((resolve) => {
		dialogState.inputValue = options.defaultValue ?? '';
		dialogState.request = { kind: 'prompt', ...options, resolve };
	});
}

export function acceptDialog(): void {
	const request = dialogState.request;
	if (!request) return;
	dialogState.request = null;
	if (request.kind === 'confirm') request.resolve(true);
	else request.resolve(dialogState.inputValue.trim() || null);
}

export function dismissDialog(): void {
	const request = dialogState.request;
	if (!request) return;
	dialogState.request = null;
	if (request.kind === 'confirm') request.resolve(false);
	else request.resolve(null);
}
