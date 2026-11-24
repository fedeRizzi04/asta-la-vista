<script lang="ts">
	import { tick } from 'svelte';
	import Button from './Button.svelte';

	let {
		label,
		items,
		size = 'md',
		disabled = false
	}: {
		label: string;
		items: { label: string; onselect: () => void }[];
		size?: 'md' | 'sm';
		disabled?: boolean;
	} = $props();
	const menuId = $props.id();
	let open = $state(false);
	let root = $state<HTMLElement>();
	let menu = $state<HTMLElement>();

	async function openAndFocus(): Promise<void> {
		open = true;
		await tick();
		menu?.querySelector('button')?.focus();
	}

	function closeAndFocus(): void {
		open = false;
		root?.querySelector('button')?.focus();
	}

	function onTriggerKeydown(event: KeyboardEvent): void {
		if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
			event.preventDefault();
			void openAndFocus();
		} else if (event.key === 'Escape' && open) {
			event.preventDefault();
			closeAndFocus();
		}
	}

	function onItemKeydown(event: KeyboardEvent, index: number): void {
		if (event.key === 'Escape') {
			event.preventDefault();
			closeAndFocus();
		} else if (event.key === 'Tab') {
			// A click does not focus a button in Safari, so closing on blur would eat the click.
			open = false;
		} else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
			event.preventDefault();
			const offset = event.key === 'ArrowDown' ? 1 : -1;
			const next = (index + offset + items.length) % items.length;
			menu?.querySelectorAll('button')[next]?.focus();
		}
	}
</script>

<svelte:window
	onpointerdown={(event) => {
		if (open && event.target instanceof Node && !root?.contains(event.target)) open = false;
	}}
/>

<div class="menu-wrap" bind:this={root}>
	<Button
		variant="secondary"
		{size}
		{disabled}
		aria-label={label}
		aria-haspopup="menu"
		aria-expanded={open}
		aria-controls={open ? menuId : undefined}
		onkeydown={onTriggerKeydown}
		onclick={() => {
			if (open) closeAndFocus();
			else void openAndFocus();
		}}
	>
		⋯
	</Button>
	{#if open}
		<div id={menuId} class="panel menu" role="menu" aria-label={label} bind:this={menu}>
			{#each items as item, index (item.label)}
				<Button
					variant="text"
					role="menuitem"
					tabindex={-1}
					onkeydown={(event) => onItemKeydown(event, index)}
					onclick={() => {
						closeAndFocus();
						item.onselect();
					}}
				>
					{item.label}
				</Button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.menu-wrap {
		position: relative;
	}

	.menu {
		position: absolute;
		z-index: 30;
		inset: calc(100% + 0.4rem) 0 auto auto;
		display: grid;
		min-width: 10rem;
		padding: 0.3rem;
	}

	.menu :global(.button) {
		justify-content: flex-start;
		color: var(--text);
	}
</style>
