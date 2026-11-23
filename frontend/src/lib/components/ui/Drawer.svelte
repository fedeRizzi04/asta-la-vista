<script lang="ts">
	import type { Snippet } from 'svelte';
	import Dialog from './Dialog.svelte';

	/** A full-height side panel (a roster, the purchase registry) with the Dialog behaviour. */
	let {
		open = $bindable(false),
		title,
		width = '440px',
		onclose,
		children
	}: {
		open?: boolean;
		title: string;
		width?: string;
		onclose?: () => void;
		children: Snippet;
	} = $props();
</script>

<Dialog bind:open {title} {width} {onclose} placement="side" closeLabel="Chiudi">
	{@render children()}
</Dialog>
