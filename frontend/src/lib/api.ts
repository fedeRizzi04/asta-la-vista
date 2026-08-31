export type ApiErrorBody = {
	code?: string;
	message?: string;
};

export class ApiError extends Error {
	constructor(
		message: string,
		readonly status: number,
		readonly code?: string
	) {
		super(message);
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
		// The fallback below covers non-JSON errors from the development server.
	}
	return new ApiError(
		body.message ?? 'La richiesta non è andata a buon fine.',
		response.status,
		body.code
	);
}

export function saveFile({ blob, filename }: DownloadedFile): void {
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	link.click();
	URL.revokeObjectURL(url);
}
