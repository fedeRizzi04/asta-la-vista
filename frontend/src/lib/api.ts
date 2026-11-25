import { errorText } from './i18n';
import type { ErrorParams } from './i18n/en';

export type ApiErrorBody = {
	code?: string;
	params?: ErrorParams;
};

export class ApiError extends Error {
	constructor(
		readonly status: number,
		readonly code?: string,
		readonly params?: ErrorParams
	) {
		super(errorText(code, params));
	}
}

export type DownloadedFile = {
	blob: Blob;
	filename: string;
};

export async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
	const response = await fetch(path, options);
	if (!response.ok) throw await apiError(response);
	if (response.status === 204) return undefined as T;
	return response.json() as Promise<T>;
}

/**
 * Fetches an endpoint that returns a file attachment. Going through fetch instead of
 * navigating to the URL keeps failures on the page, where they become a toast.
 */
export async function apiDownload(path: string): Promise<DownloadedFile> {
	const response = await fetch(path);
	if (!response.ok) throw await apiError(response);
	const disposition = response.headers.get('Content-Disposition') ?? '';
	return {
		blob: await response.blob(),
		filename: /filename="([^"]+)"/.exec(disposition)?.[1] ?? 'download'
	};
}

async function apiError(response: Response): Promise<ApiError> {
	let body: ApiErrorBody = {};
	try {
		body = await response.json();
	} catch {
		// A non-JSON error, such as one from the development server, has no code.
	}
	return new ApiError(response.status, body.code, body.params);
}

export function saveFile({ blob, filename }: DownloadedFile): void {
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	link.click();
	URL.revokeObjectURL(url);
}
