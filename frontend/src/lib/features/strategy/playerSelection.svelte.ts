import { SvelteSet } from 'svelte/reactivity';

/** The players selected in the strategy editor, to move together. */
export class PlayerSelection {
	readonly ids = new SvelteSet<string>();
	/** Where a range selection starts. */
	#anchorId: string | undefined;

	selectOnly(id: string): void {
		this.#replace([id]);
		this.#anchorId = id;
	}

	toggle(id: string): void {
		if (!this.ids.delete(id)) this.ids.add(id);
		this.#anchorId = id;
	}

	/** Selects the ids of `list` from the last one picked there, or else `fromId`, to `toId`. */
	extendTo(toId: string, list: string[], fromId = toId): void {
		const anchorId =
			this.#anchorId !== undefined && list.includes(this.#anchorId) ? this.#anchorId : fromId;
		const anchor = list.indexOf(anchorId);
		const to = list.indexOf(toId);
		this.#replace(list.slice(Math.min(anchor, to), Math.max(anchor, to) + 1));
		this.#anchorId = anchorId;
	}

	clear(): void {
		this.#replace([]);
		this.#anchorId = undefined;
	}

	#replace(ids: string[]): void {
		this.ids.clear();
		for (const id of ids) this.ids.add(id);
	}
}
