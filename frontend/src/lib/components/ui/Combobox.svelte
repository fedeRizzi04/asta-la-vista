<script lang="ts" generics="Item extends { id: string }">
	import { tick, type Snippet } from 'svelte';
	import type { HTMLInputAttributes } from 'svelte/elements';

	/**
	 * A text field with a list of matches below it (ARIA combobox). The parent filters `items`
	 * from the typed `value`; arrows move through them, Enter (or Tab, once something is typed)
	 * chooses the highlighted one and Esc closes the list. Set `--combobox-width` to make the
	 * list wider than the field.
	 */
	let {
		value = $bindable(),
		element = $bindable(),
		items,
		option,
		emptyMessage,
		openOnFocus = false,
		onchoose,
		...rest
	}: {
		value: string;
		element?: HTMLInputElement;
		items: Item[];
		option: Snippet<[Item]>;
		/** Shown instead of the list when nothing matches. */
		emptyMessage?: string;
		openOnFocus?: boolean;
		onchoose: (item: Item) => void;
	} & Omit<HTMLInputAttributes, 'value'> = $props();

	const listId = $props.id();
	let open = $state(false);
	let activeIndex = $state(0);
	let activeItem = $derived(items[Math.min(activeIndex, items.length - 1)]);
	let listVisible = $derived(open && items.length > 0);

	function optionId(item: Item): string {
		return `${listId}-${item.id}`;
	}

	function show(): void {
		open = true;
		activeIndex = 0;
	}

	function choose(item: Item): void {
		open = false;
		onchoose(item);
	}

	async function move(step: 1 | -1): Promise<void> {
		if (!open) {
			show();
			return;
		}
		activeIndex = Math.max(0, Math.min(activeIndex + step, items.length - 1));
		await tick();
		if (activeItem)
			document.getElementById(optionId(activeItem))?.scrollIntoView({ block: 'nearest' });
	}

	function handleKeydown(event: KeyboardEvent): void {
		if (event.isComposing) return;
		if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
			event.preventDefault();
			void move(event.key === 'ArrowDown' ? 1 : -1);
		} else if (event.key === 'Enter') {
			event.preventDefault();
			if (listVisible) choose(activeItem);
		} else if (event.key === 'Tab' && !event.shiftKey && listVisible && value.trim()) {
			choose(activeItem);
			// Do not tab past the field that `onchoose` moved to.
			if (document.activeElement !== element) event.preventDefault();
		} else if (event.key === 'Escape' && open) {
			event.preventDefault();
			open = false;
		}
	}
</script>

<div class="combobox">
	<input
		bind:value
		bind:this={element}
		class="control"
		type="search"
		role="combobox"
		autocomplete="off"
		spellcheck="false"
		aria-autocomplete="list"
		aria-expanded={listVisible}
		aria-controls={listId}
		aria-activedescendant={listVisible ? optionId(activeItem) : undefined}
		oninput={show}
		onkeydown={handleKeydown}
		onfocus={() => openOnFocus && show()}
		onclick={() => openOnFocus && show()}
		onblur={() => (open = false)}
		{...rest}
	/>
	{#if listVisible}
		<ul id={listId} class="popup" role="listbox" aria-label={rest['aria-label']}>
			{#each items as item (item.id)}
				<!-- Focus stays in the field, whose keydown handler covers the keyboard. -->
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<li
					id={optionId(item)}
					role="option"
					aria-selected={item === activeItem}
					onmousedown={(event) => event.preventDefault()}
					onclick={() => choose(item)}
				>
					{@render option(item)}
				</li>
			{/each}
		</ul>
	{:else if open && emptyMessage}
		<p class="popup" role="status">{emptyMessage}</p>
	{/if}
</div>

<style>
	.combobox {
		position: relative;
		min-width: 0;
	}

	.popup {
		position: absolute;
		top: calc(100% + 0.4rem);
		left: 0;
		z-index: 1;
		width: var(--combobox-width, 100%);
		max-width: calc(100vw - 2rem);
		max-height: min(21rem, 50vh);
		margin: 0;
		padding: 0.35rem;
		overflow-y: auto;
		border: var(--bw) solid var(--line);
		border-radius: var(--radius-sm);
		background: var(--surface);
		box-shadow: var(--shadow-sm);
		font-size: 0.875rem;
		list-style: none;
	}

	p.popup {
		padding: 0.6rem 0.8rem;
		color: var(--muted);
	}

	li {
		padding: 0.3rem 0.5rem;
		border-radius: var(--radius-xs);
		cursor: pointer;
	}

	li:hover {
		background: var(--hover);
	}

	li[aria-selected='true'] {
		background: var(--selected-bg);
	}
</style>
