import { apiRequest } from './api';
import type { Role } from './players';

export type StrategySummary = {
	id: string;
	name: string;
	tier_count: number;
	assigned_player_count: number;
};

export type Tier = {
	id: string;
	role: Role;
	name: string;
	position: number;
	color: string | null;
};

export type StrategyEntry = {
	player_id: string;
	name: string;
	team: string;
	role: Role;
	active: boolean;
	tier_id: string | null;
	note: string;
};

export type Strategy = {
	id: string;
	name: string;
	tiers: Tier[];
	entries: StrategyEntry[];
};

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
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name })
	});
}

export function addTier(
	strategyId: string,
	role: Role,
	name: string,
	color: string | null
): Promise<EntityId> {
	return apiRequest<EntityId>(`/api/strategies/${strategyId}/tiers`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ role, name, color })
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
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, color })
	});
}

export function removeTier(strategyId: string, tierId: string): Promise<void> {
	return apiRequest<void>(`/api/strategies/${strategyId}/tiers/${tierId}`, { method: 'DELETE' });
}

export function reorderTiers(strategyId: string, role: Role, tierIds: string[]): Promise<void> {
	return apiRequest<void>(`/api/strategies/${strategyId}/tiers/order`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ role, tier_ids: tierIds })
	});
}

export function updateStrategyEntry(
	strategyId: string,
	playerId: string,
	tierId: string | null,
	note: string
): Promise<void> {
	return apiRequest<void>(`/api/strategies/${strategyId}/players/${playerId}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ tier_id: tierId, note })
	});
}
