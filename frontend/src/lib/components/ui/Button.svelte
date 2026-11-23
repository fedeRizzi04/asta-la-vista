<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLAnchorAttributes, HTMLButtonAttributes } from 'svelte/elements';
	import { press } from '$lib/actions/press';

	type Variant = 'primary' | 'secondary' | 'danger' | 'text';
	type Size = 'md' | 'sm';

	/**
	 * The app's one button. With `href` it renders a link that looks like a button: pass a
	 * `resolve()`d app path or an absolute external URL (`disabled` and `loading` are for
	 * buttons only). `loading` keeps the label, shows a spinner and blocks clicks meanwhile.
	 */
	let {
		variant = 'primary',
		size = 'md',
		loading = false,
		disabled = false,
		type = 'button',
		href,
		class: className = '',
		children,
		...rest
	}: {
		variant?: Variant;
		size?: Size;
		loading?: boolean;
		disabled?: boolean;
		type?: HTMLButtonAttributes['type'];
		href?: string;
		class?: string;
		children: Snippet;
	} & Omit<
		HTMLButtonAttributes & HTMLAnchorAttributes,
		'type' | 'href' | 'class' | 'disabled'
	> = $props();

	let inactive = $derived(disabled || loading);
</script>

{#if href}
	<!-- Callers pass resolve()d app paths or external URLs (the update banner's release page). -->
	<!-- eslint-disable svelte/no-navigation-without-resolve -->
	<a {href} class="button {variant} {size} {className}" use:press {...rest}>
		{@render children()}
	</a>
	<!-- eslint-enable svelte/no-navigation-without-resolve -->
{:else}
	<button
		{type}
		class="button {variant} {size} {className}"
		disabled={inactive}
		aria-busy={loading || undefined}
		use:press={{ disabled: inactive }}
		{...rest}
	>
		{#if loading}<span class="spinner" aria-hidden="true"></span>{/if}
		{@render children()}
	</button>
{/if}

<style>
	.button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.45rem;
		min-height: var(--control-height);
		padding: 0 0.8rem;
		border: var(--bw) solid var(--line);
		border-radius: var(--radius-sm);
		box-shadow: var(--shadow-xs);
		font-size: 0.875rem;
		font-weight: 700;
		white-space: nowrap;
		text-decoration: none;
		cursor: pointer;
		transition:
			background-color 140ms ease,
			box-shadow 100ms ease;
	}

	.button:not(:disabled):hover {
		filter: brightness(1.06);
	}

	.button:not(:disabled):active {
		box-shadow: none;
	}

	.button:disabled {
		cursor: not-allowed;
		opacity: 0.55;
		box-shadow: none;
	}

	.button[aria-busy='true'] {
		cursor: progress;
	}

	.primary {
		background: var(--primary);
		color: var(--on-primary);
	}

	.secondary {
		background: var(--surface);
		color: var(--text);
	}

	.danger {
		background: var(--surface);
		color: var(--danger);
	}

	.text {
		border-color: transparent;
		background: transparent;
		box-shadow: none;
		color: var(--muted);
	}

	.text:not(:disabled):hover {
		background: var(--hover);
		color: var(--text);
		filter: none;
	}

	.sm {
		min-height: 1.75rem;
		padding: 0 0.55rem;
		border-radius: var(--radius-xs);
		font-size: 0.8rem;
	}

	.spinner {
		width: 0.85em;
		height: 0.85em;
		border: 2px solid currentColor;
		border-right-color: transparent;
		border-radius: 50%;
		animation: spin 700ms linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
