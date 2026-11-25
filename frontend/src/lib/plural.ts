/** The word for a count: `${n} ${plural(n, 'purchase', 'purchases')}`. */
export function plural(count: number, one: string, many: string): string {
	return count === 1 ? one : many;
}
