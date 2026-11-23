<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	/** A text-like input (text, search, number, color) with the shared `.control` look. */
	let { value = $bindable(), class: className, ...rest }: HTMLInputAttributes = $props();
</script>

<input bind:value class={['control', className]} {...rest} />
