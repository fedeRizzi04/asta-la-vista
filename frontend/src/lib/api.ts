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

export async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
	const response = await fetch(path, options);
	if (!response.ok) {
		let body: ApiErrorBody = {};
		try {
			body = await response.json();
		} catch {
			// The fallback below covers non-JSON errors from the development server.
		}
		throw new ApiError(
			body.message ?? 'La richiesta non è andata a buon fine.',
			response.status,
			body.code
		);
	}
	return response.json() as Promise<T>;
}
