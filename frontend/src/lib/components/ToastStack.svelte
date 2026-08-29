<script lang="ts">
	import { fly } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { dismissToast, toastState } from '$lib/toast.svelte';
	import { press } from '$lib/actions/press';
	import { motionPreferences } from '$lib/motionPreferences.svelte';

	let flyIn = $derived(
		motionPreferences.reducedMotion
			? { duration: 120 }
			: { y: -16, duration: 260, easing: cubicOut }
	);
	let flyOut = $derived(
		motionPreferences.reducedMotion ? { duration: 120 } : { y: -8, duration: 180, easing: cubicOut }
	);
</script>

<div class="toast-stack">
	{#each toastState.items as toast (toast.id)}
		<div
			class="toast"
			class:success={toast.kind === 'success'}
			role={toast.kind === 'error' ? 'alert' : 'status'}
			in:fly={flyIn}
			out:fly={flyOut}
		>
			<span>{toast.message}</span>
			<button
				type="button"
				aria-label="Chiudi notifica"
				use:press
				onclick={() => dismissToast(toast.id)}
			>
				&times;
			</button>
		</div>
	{/each}
</div>

<style>
	.toast-stack {
		position: fixed;
		top: calc(4.5rem + 1.25rem);
		right: 1.25rem;
		z-index: 1000;
		display: grid;
		gap: 0.6rem;
		width: min(360px, calc(100% - 2.5rem));
	}

	.toast {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.85rem 1rem;
		border: 1px solid var(--error-border);
		border-radius: 0.65rem;
		background: color-mix(in srgb, var(--error-bg) 92%, transparent);
		backdrop-filter: blur(16px) saturate(160%);
		color: var(--error-text);
		box-shadow: 0 16px 32px -8px rgb(0 0 0 / 22%);
		font-size: 0.88rem;
		font-weight: 550;
		letter-spacing: 0.005em;
		line-height: 1.4;
	}

	.toast.success {
		border-color: var(--success-border);
		background: color-mix(in srgb, var(--success-bg) 92%, transparent);
		color: var(--success-text);
	}

	.toast button {
		flex: 0 0 auto;
		min-height: auto;
		padding: 0;
		border: 0;
		background: transparent;
		color: inherit;
		font-size: 1.15rem;
		line-height: 1;
		opacity: 0.7;
		cursor: pointer;
		transition: opacity 140ms ease;
	}

	.toast button:hover {
		opacity: 1;
	}

	@media (max-width: 720px) {
		.toast-stack {
			top: 1rem;
			right: 1rem;
			left: 1rem;
			width: auto;
		}
	}

	@media (prefers-reduced-transparency: reduce) {
		.toast {
			background: var(--error-bg);
			backdrop-filter: none;
		}

		.toast.success {
			background: var(--success-bg);
		}
	}
</style>
