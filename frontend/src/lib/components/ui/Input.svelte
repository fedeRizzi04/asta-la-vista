<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	/** A text-like input (text, search, number, color) with the shared `.control` look. */
	let {
		value = $bindable(),
		element = $bindable(),
		class: className,
		...rest
	}: HTMLInputAttributes & { element?: HTMLInputElement } = $props();
</script>

<input bind:value bind:this={element} class={['control', className]} {...rest} />
