<script lang="ts">
	import type { Snippet } from 'svelte';
	import { t } from '$lib/i18n';
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

<Dialog bind:open {title} {width} {onclose} placement="side" closeLabel={t.common.close}>
	{@render children()}
</Dialog>
