import { apiRequest } from './api';

export type AppVersion = {
	version: string;
	/** Filled only when the server checks GitHub for updates (on by default in the desktop app). */
	latest_version: string | null;
	release_url: string | null;
	update_available: boolean;
};

export function getVersion(): Promise<AppVersion> {
	return apiRequest<AppVersion>('/api/version');
}
