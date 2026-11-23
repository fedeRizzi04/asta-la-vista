<script lang="ts">
	import type { HTMLSelectAttributes } from 'svelte/elements';

	/** A native select with the shared `.control` look; options go in as children. */
	let { value = $bindable(), class: className, children, ...rest }: HTMLSelectAttributes = $props();
</script>

<select bind:value class={['control', className]} {...rest}>
	{@render children?.()}
</select>
