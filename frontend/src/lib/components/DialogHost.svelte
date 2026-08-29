<script lang="ts">
	import { acceptDialog, dialogState, dismissDialog } from '$lib/dialog.svelte';
	import { press } from '$lib/actions/press';

	let confirmButton = $state<HTMLButtonElement>();
	let inputEl = $state<HTMLInputElement>();

	$effect(() => {
		if (!dialogState.request) return;
		(dialogState.request.kind === 'prompt' ? inputEl : confirmButton)?.focus();
	});

	function onKeydown(event: KeyboardEvent): void {
		if (!dialogState.request) return;
		if (event.key === 'Escape') {
			event.preventDefault();
			dismissDialog();
		} else if (event.key === 'Enter' && dialogState.request.kind === 'prompt') {
			event.preventDefault();
			acceptDialog();
		}
	}
</script>

<svelte:window onkeydown={onKeydown} />

{#if dialogState.request}
	<div class="dialog-overlay" onclick={dismissDialog} role="presentation">
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<div
			class="dialog"
			role="alertdialog"
			tabindex="-1"
			aria-modal="true"
			aria-labelledby="dialog-title"
			aria-describedby="dialog-message"
			onclick={(event) => event.stopPropagation()}
		>
			<h2 id="dialog-title">{dialogState.request.title ?? 'Conferma'}</h2>
			<p id="dialog-message">{dialogState.request.message}</p>
			{#if dialogState.request.kind === 'prompt'}
				<input
					bind:this={inputEl}
					bind:value={dialogState.inputValue}
					placeholder={dialogState.request.placeholder}
				/>
			{/if}
			<div class="dialog-actions">
				<button type="button" class="secondary" use:press onclick={dismissDialog}>
					{dialogState.request.cancelLabel ?? 'Annulla'}
				</button>
				<button
					type="button"
					class:danger={dialogState.request.danger}
					bind:this={confirmButton}
					use:press
					onclick={acceptDialog}
				>
					{dialogState.request.confirmLabel ?? 'Conferma'}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.dialog-overlay {
		position: fixed;
		inset: 0;
		z-index: 1100;
		display: grid;
		place-items: center;
		padding: 1.5rem;
		background: var(--overlay);
		backdrop-filter: blur(0);
		animation: overlay-in 220ms cubic-bezier(0.19, 1, 0.22, 1);
	}

	.dialog {
		width: min(420px, 100%);
		padding: 1.5rem;
		border: 1px solid var(--border);
		border-radius: 0.9rem;
		background: color-mix(in srgb, var(--surface) 92%, transparent);
		backdrop-filter: blur(24px) saturate(160%);
		box-shadow:
			0 1px 0 rgb(255 255 255 / 6%) inset,
			0 24px 60px -12px rgb(0 0 0 / 32%);
		/* Materialize, don't just fade: blur and scale settle together, like a real surface arriving. */
		animation: dialog-in 260ms cubic-bezier(0.19, 1, 0.22, 1);
	}

	.dialog h2 {
		margin: 0 0 0.6rem;
		font-size: 1.1rem;
	}

	.dialog p {
		margin: 0;
		color: var(--muted);
		font-size: 0.9rem;
		line-height: 1.55;
	}

	.dialog input {
		width: 100%;
		height: 2.5rem;
		margin-top: 1rem;
		padding: 0 0.7rem;
		border: 1px solid var(--border-strong);
		border-radius: 0.4rem;
		background: var(--input-bg);
		color: inherit;
		font: inherit;
	}

	.dialog-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.6rem;
		margin-top: 1.4rem;
	}

	.dialog-actions button {
		min-height: 2.5rem;
		padding: 0 1rem;
		border: 1px solid var(--primary);
		border-radius: 0.45rem;
		background: var(--primary);
		color: var(--on-primary);
		font: inherit;
		font-size: 0.85rem;
		font-weight: 700;
		cursor: pointer;
	}

	.dialog-actions button.secondary {
		border-color: var(--border-strong);
		background: transparent;
		color: var(--text);
	}

	.dialog-actions button.danger {
		border-color: var(--danger);
		background: var(--danger);
		color: var(--on-danger);
	}

	.dialog-actions button.danger:hover {
		background: var(--danger-hover);
	}

	@keyframes overlay-in {
		from {
			opacity: 0;
			backdrop-filter: blur(0);
		}
		to {
			opacity: 1;
			backdrop-filter: blur(6px);
		}
	}

	@keyframes dialog-in {
		from {
			opacity: 0;
			transform: translateY(10px) scale(0.96);
			backdrop-filter: blur(0);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
			backdrop-filter: blur(24px) saturate(160%);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.dialog-overlay,
		.dialog {
			animation: fade-in 160ms ease;
		}

		@keyframes fade-in {
			from {
				opacity: 0;
			}
			to {
				opacity: 1;
			}
		}
	}

	@media (prefers-reduced-transparency: reduce) {
		.dialog-overlay {
			backdrop-filter: none;
		}

		.dialog {
			background: var(--surface);
			backdrop-filter: none;
		}
	}
</style>
