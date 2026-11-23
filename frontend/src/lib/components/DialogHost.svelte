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
	.dialog {
		width: min(420px, 100%);
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
		margin-top: 1rem;
	}

	.dialog-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.6rem;
		margin-top: 1.4rem;
	}
</style>
