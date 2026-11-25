/** Shared substring-search helpers, kept in one place so pages don't reimplement matching/ranking. */

/** True when the (trimmed, case-insensitive) query is a substring of any given field. An empty query always matches. */
export function matchesSearch(query: string, ...fields: (string | null | undefined)[]): boolean {
	const normalizedQuery = query.trim().toLowerCase();
	if (!normalizedQuery) return true;
	return fields.some((field) => !!field && field.toLowerCase().includes(normalizedQuery));
}

/** Ranks how closely a name matches the query: exact match first, then prefix, substring, no match. */
export function nameMatchRank(name: string, query: string): number {
	const normalizedQuery = query.trim().toLowerCase();
	if (!normalizedQuery) return 0;
	const normalizedName = name.toLowerCase();
	if (normalizedName === normalizedQuery) return 0;
	if (normalizedName.startsWith(normalizedQuery)) return 1;
	if (normalizedName.includes(normalizedQuery)) return 2;
	return 3;
}
