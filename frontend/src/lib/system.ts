import { apiRequest } from './api';

export type AppVersion = {
	version: string;
};

export function getVersion(): Promise<AppVersion> {
	return apiRequest<AppVersion>('/api/version');
}
