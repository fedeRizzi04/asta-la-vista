<script lang="ts" generics="T extends string">
	import { press } from '$lib/actions/press';

	/**
	 * A segmented tab list with the full ARIA tabs pattern: one tab in the Tab order (roving
	 * tabindex), ←/→ and Home/End move and select at once. The page wraps what the tabs
	 * control in `<div role="tabpanel" tabindex="0" id={panelId}
	 * aria-labelledby="{id}-{value}">`: `id` prefixes the tab ids, so the panel can name the
	 * selected tab.
	 */
	let {
		items,
		value = $bindable(),
		label,
		id,
		panelId,
		onchange
	}: {
		items: { value: T; label: string }[];
		value: T;
		label: string;
		id: string;
		panelId: string;
		onchange?: (value: T) => void;
	} = $props();

	function select(next: T): void {
		if (next === value) return;
		value = next;
		onchange?.(next);
	}

	/** `index` is the focused tab's, which may differ from the selected one. */
	function onkeydown(event: KeyboardEvent, index: number): void {
		const target = {
			ArrowLeft: index - 1,
			ArrowRight: index + 1,
			Home: 0,
			End: items.length - 1
		}[event.key];
		if (target === undefined) return;
		event.preventDefault();
		const next = items[(target + items.length) % items.length];
		select(next.value);
		document.getElementById(`${id}-${next.value}`)?.focus();
	}
</script>

<div class="tabs" role="tablist" aria-label={label}>
	{#each items as item, index (item.value)}
		<button
			type="button"
			role="tab"
			id="{id}-{item.value}"
			aria-selected={item.value === value}
			aria-controls={panelId}
			tabindex={item.value === value ? 0 : -1}
			use:press
			onclick={() => select(item.value)}
			onkeydown={(event) => onkeydown(event, index)}
		>
			{item.label}
		</button>
	{/each}
</div>

<style>
	.tabs {
		display: inline-flex;
		flex-wrap: wrap;
		gap: 0.2rem;
		padding: 0.2rem;
		border: var(--bw) solid var(--line);
		border-radius: var(--radius-sm);
		background: var(--muted-bg);
	}

	[role='tab'] {
		min-height: 1.75rem;
		padding: 0 0.7rem;
		border: 0;
		border-radius: var(--radius-xs);
		background: transparent;
		color: var(--muted);
		font-size: 0.875rem;
		font-weight: 700;
		cursor: pointer;
		transition:
			background-color 140ms ease,
			color 140ms ease;
	}

	[role='tab']:hover {
		color: var(--text);
	}

	[role='tab'][aria-selected='true'] {
		background: var(--surface);
		color: var(--text);
		box-shadow: inset 0 0 0 var(--bw) var(--line);
	}
</style>
