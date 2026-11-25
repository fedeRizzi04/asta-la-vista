<script lang="ts">
	import { fly } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { dismissToast, toastState } from '$lib/toast.svelte';
	import { press } from '$lib/actions/press';
	import { t } from '$lib/i18n';
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
				class="dismiss-button"
				type="button"
				aria-label={t.common.dismissNotification}
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
		top: calc(var(--header-height) + 1.25rem);
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
		border-radius: var(--radius-sm);
		background: var(--error-bg);
		color: var(--error-text);
		box-shadow: var(--shadow-sm);
		font-size: 0.88rem;
		line-height: 1.4;
	}

	.toast.success {
		border-color: var(--success-border);
		background: var(--success-bg);
		color: var(--success-text);
	}

	@media (max-width: 720px) {
		.toast-stack {
			top: 1rem;
			right: 1rem;
			left: 1rem;
			width: auto;
		}
	}
</style>
