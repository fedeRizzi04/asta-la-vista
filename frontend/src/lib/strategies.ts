import { apiDownload, apiRequest, type DownloadedFile } from './api';
import type { Role } from './players';

export type StrategySummary = {
	id: string;
	name: string;
	tier_count: number;
	assigned_player_count: number;
};

export type Tier = {
	id: string;
	name: string;
	position: number;
	color: string | null;
};

/** The colors given to new tiers, in turn. */
export const tierColors = [
	'#8e6cf0',
	'#2fa596',
	'#d9a531',
	'#5b8fd9',
	'#e0709f',
	'#9a8f80',
	'#e2763b',
	'#4caf50'
];

export type StrategyEntry = {
	player_id: string;
	name: string;
	team: string;
	role: Role;
	active: boolean;
	mantra_roles: string[];
	tier_id: string | null;
	note: string;
	maximum_price_percentage: number | null;
};

export type Strategy = {
	id: string;
	name: string;
	tiers: Tier[];
	entries: StrategyEntry[];
};

export function strategyIndex(strategy: Strategy) {
	return {
		entryByPlayerId: new Map(strategy.entries.map((entry) => [entry.player_id, entry])),
		tierById: new Map(strategy.tiers.map((tier) => [tier.id, tier])),
		sortedTiers: [...strategy.tiers].sort((first, second) => first.position - second.position)
	};
}

type EntityId = { id: string };

export function getStrategies(): Promise<StrategySummary[]> {
	return apiRequest<StrategySummary[]>('/api/strategies');
}

export function getStrategy(strategyId: string): Promise<Strategy> {
	return apiRequest<Strategy>(`/api/strategies/${strategyId}`);
}

export function createStrategy(name: string): Promise<EntityId> {
	return apiRequest<EntityId>('/api/strategies', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name })
	});
}

export type ImportSummary = {
	strategy_id: string;
	tiers_created: number;
	players_assigned: number;
	unmatched: string[];
};

export function importStrategy(
	name: string,
	file: File,
	confirmUnmatched = false
): Promise<ImportSummary> {
	const data = new FormData();
	data.set('file', file);
	return apiRequest<ImportSummary>(
		`/api/strategies/import?name=${encodeURIComponent(name)}&confirm_unmatched=${confirmUnmatched}`,
		{ method: 'POST', body: data }
	);
}

export function exportStrategy(strategyId: string): Promise<DownloadedFile> {
	return apiDownload(`/api/strategies/${strategyId}/export`);
}

export function duplicateStrategy(strategyId: string, name: string): Promise<EntityId> {
	return apiRequest<EntityId>(`/api/strategies/${strategyId}/duplicate`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name })
	});
}

export function renameStrategy(strategyId: string, name: string): Promise<void> {
	return apiRequest<void>(`/api/strategies/${strategyId}`, {
		method: 'PATCH',
		// Let autosaves started on pagehide finish after the page unloads.
		keepalive: true,
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name })
	});
}

export function deleteStrategy(strategyId: string): Promise<void> {
	return apiRequest<void>(`/api/strategies/${strategyId}`, { method: 'DELETE' });
}

export function addTier(strategyId: string, name: string, color: string | null): Promise<EntityId> {
	return apiRequest<EntityId>(`/api/strategies/${strategyId}/tiers`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, color })
	});
}

export function updateTier(
	strategyId: string,
	tierId: string,
	name: string,
	color: string | null
): Promise<void> {
	return apiRequest<void>(`/api/strategies/${strategyId}/tiers/${tierId}`, {
		method: 'PATCH',
		// Let autosaves started on pagehide finish after the page unloads.
		keepalive: true,
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, color })
	});
}

export function removeTier(strategyId: string, tierId: string): Promise<void> {
	return apiRequest<void>(`/api/strategies/${strategyId}/tiers/${tierId}`, { method: 'DELETE' });
}

export function reorderTiers(strategyId: string, tierIds: string[]): Promise<void> {
	return apiRequest<void>(`/api/strategies/${strategyId}/tiers/order`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ tier_ids: tierIds })
	});
}

export function updateStrategyEntry(
	strategyId: string,
	playerId: string,
	tierId: string | null,
	note: string,
	maximumPricePercentage: number | null
): Promise<void> {
	return apiRequest<void>(`/api/strategies/${strategyId}/players/${playerId}`, {
		method: 'PUT',
		keepalive: true, // as in updateTier
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			tier_id: tierId,
			note,
			maximum_price_percentage: maximumPricePercentage
		})
	});
}

/**
 * Converts a strategy entry's maximum-price percentage into an absolute credit amount
 * for a specific auction budget, using standard rounding.
 */
export function percentageToCredits(percentage: number, budget: number): number {
	return Math.round((percentage / 100) * budget);
}

/**
 * Comparator for sorting items with a maximum-price percentage highest-first, treating
 * unset percentages as lowest priority. `getPercentage` picks the field out of whatever
 * shape the caller has (a strategy entry, a board draft, …).
 */
export function byMaxPercentageDesc<T>(
	getPercentage: (item: T) => number | null | undefined
): (first: T, second: T) => number {
	return (first, second) => (getPercentage(second) ?? -1) - (getPercentage(first) ?? -1);
}
