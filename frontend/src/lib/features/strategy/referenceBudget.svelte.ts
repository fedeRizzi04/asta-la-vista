import { browser } from '$app/environment';

const STORAGE_KEY = 'strategy-reference-budget';
const DEFAULT_BUDGET = 500;

function validBudget(value: number): number {
	return Number.isSafeInteger(value) && value >= 1 ? value : DEFAULT_BUDGET;
}

function readBudget(): number {
	try {
		return validBudget(Number(localStorage.getItem(STORAGE_KEY)));
	} catch {
		return DEFAULT_BUDGET;
	}
}

let budget = $state(browser ? readBudget() : DEFAULT_BUDGET);

export const referenceBudget = {
	get value(): number {
		return budget;
	},
	set value(value: number) {
		budget = validBudget(value);
		if (!browser) return;
		try {
			localStorage.setItem(STORAGE_KEY, String(budget));
		} catch {
			// Keep the in-memory budget when storage is unavailable.
		}
	}
};
