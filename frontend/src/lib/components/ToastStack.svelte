<script lang="ts">
	import { dismissToast, toastState } from '$lib/toast.svelte';
</script>

<div class="toast-stack">
	{#each toastState.items as toast (toast.id)}
		<div
			class="toast"
			class:success={toast.kind === 'success'}
			role={toast.kind === 'error' ? 'alert' : 'status'}
		>
			<span>{toast.message}</span>
			<button type="button" aria-label="Chiudi notifica" onclick={() => dismissToast(toast.id)}>
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
		border-radius: 0.6rem;
		background: var(--error-bg);
		color: var(--error-text);
		box-shadow: 0 12px 28px rgb(0 0 0 / 16%);
		font-size: 0.88rem;
		line-height: 1.4;
		animation: toast-in 180ms ease;
	}

	.toast.success {
		border-color: var(--success-border);
		background: var(--success-bg);
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
	}

	.toast button:hover {
		opacity: 1;
	}

	@keyframes toast-in {
		from {
			opacity: 0;
			transform: translateY(-6px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
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
