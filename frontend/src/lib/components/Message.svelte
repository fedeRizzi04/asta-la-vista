<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		kind = 'error',
		children
	}: {
		kind?: 'error' | 'success';
		children: Snippet;
	} = $props();
</script>

<div
	class="message"
	class:success={kind === 'success'}
	role={kind === 'error' ? 'alert' : 'status'}
>
	{@render children()}
</div>

<style>
	.message {
		margin-top: 1.5rem;
		padding: 0.85rem 1rem;
		border: 1px solid var(--error-border);
		border-radius: 0.5rem;
		background: var(--error-bg);
		color: var(--error-text);
		font-size: 0.9rem;
	}

	.message.success {
		border-color: var(--success-border);
		background: var(--success-bg);
		color: var(--success-text);
	}
</style>
