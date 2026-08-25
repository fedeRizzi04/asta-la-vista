import { apiRequest } from './api';

export type Role = 'P' | 'D' | 'C' | 'A';

export type Player = {
	id: string;
	name: string;
	team: string;
	role: Role;
	quotation: number | null;
	active: boolean;
};

export type PlayerCounts = Record<Role, number>;

export type ImportSummary = {
	added: number;
	updated: number;
	deactivated: number;
	role_changes: number;
};

export type PlayerFilters = {
	role?: Role;
	search?: string;
	includeInactive?: boolean;
};

export function getPlayers(filters: PlayerFilters = {}): Promise<Player[]> {
	const query = new URLSearchParams();
	if (filters.role) query.set('role', filters.role);
	if (filters.search) query.set('search', filters.search);
	if (filters.includeInactive) query.set('include_inactive', 'true');
	const suffix = query.size ? `?${query.toString()}` : '';
	return apiRequest<Player[]>(`/api/players${suffix}`);
}

export function getPlayerCounts(): Promise<PlayerCounts> {
	return apiRequest<PlayerCounts>('/api/players/counts');
}

export function importPlayers(file: File, confirmLive = false): Promise<ImportSummary> {
	const data = new FormData();
	data.set('file', file);
	return apiRequest<ImportSummary>(`/api/players/import?confirm_live=${confirmLive}`, {
		method: 'POST',
		body: data
	});
}
