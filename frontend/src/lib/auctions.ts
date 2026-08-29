import { apiRequest } from './api';
import type { Role } from './players';

export type AuctionStatus = 'draft' | 'live' | 'completed';

export type AuctionSummary = {
	id: string;
	name: string;
	status: AuctionStatus;
	initial_credits: number;
	strategy_id: string | null;
	participant_count: number;
	purchase_count: number;
};

export type SlotStatus = { filled: number; total: number };

export type Purchase = {
	id: string;
	player_id: string;
	player_name: string;
	team: string;
	role: Role;
	price: number;
	player_active: boolean;
	mantra_roles: string[];
	created_at: string;
};

export type Participant = {
	id: string;
	name: string;
	position: number;
	credits_remaining: number;
	maximum_bid: number;
	slots: Record<Role, SlotStatus>;
	purchases: Purchase[];
};

export type Auction = {
	id: string;
	name: string;
	status: AuctionStatus;
	initial_credits: number;
	strategy_id: string | null;
	slot_totals: Record<Role, number>;
	participants: Participant[];
	purchased_player_ids: string[];
};

export type AuctionInput = {
	name: string;
	initial_credits: number;
	goalkeeper_slots: number;
	defender_slots: number;
	midfielder_slots: number;
	forward_slots: number;
	participant_names: string[];
	strategy_id: string | null;
};

type EntityId = { id: string };

export function getAuctions(): Promise<AuctionSummary[]> {
	return apiRequest<AuctionSummary[]>('/api/auctions');
}

export function getAuction(auctionId: string): Promise<Auction> {
	return apiRequest<Auction>(`/api/auctions/${auctionId}`);
}

export function createAuction(input: AuctionInput): Promise<EntityId> {
	return apiRequest<EntityId>('/api/auctions', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(input)
	});
}

export function startAuction(auctionId: string): Promise<void> {
	return apiRequest<void>(`/api/auctions/${auctionId}/start`, { method: 'POST' });
}

export function completeAuction(auctionId: string): Promise<void> {
	return apiRequest<void>(`/api/auctions/${auctionId}/complete`, { method: 'POST' });
}

export function reopenAuction(auctionId: string): Promise<void> {
	return apiRequest<void>(`/api/auctions/${auctionId}/reopen`, { method: 'POST' });
}

export function deleteAuction(auctionId: string): Promise<void> {
	return apiRequest<void>(`/api/auctions/${auctionId}`, { method: 'DELETE' });
}

export function setAuctionStrategy(auctionId: string, strategyId: string | null): Promise<void> {
	return apiRequest<void>(`/api/auctions/${auctionId}/strategy`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ strategy_id: strategyId })
	});
}

export function recordPurchase(
	auctionId: string,
	playerId: string,
	participantId: string,
	price: number
): Promise<EntityId> {
	return apiRequest<EntityId>(`/api/auctions/${auctionId}/purchases`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ player_id: playerId, participant_id: participantId, price })
	});
}

export function amendPurchase(
	auctionId: string,
	purchaseId: string,
	participantId: string,
	price: number
): Promise<void> {
	return apiRequest<void>(`/api/auctions/${auctionId}/purchases/${purchaseId}`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ participant_id: participantId, price })
	});
}

export function cancelPurchase(auctionId: string, purchaseId: string): Promise<void> {
	return apiRequest<void>(`/api/auctions/${auctionId}/purchases/${purchaseId}`, {
		method: 'DELETE'
	});
}
