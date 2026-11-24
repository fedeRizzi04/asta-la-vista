<script lang="ts">
	import { acceptDialog, dialogState, dismissDialog } from '$lib/dialog.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Dialog from '$lib/components/ui/Dialog.svelte';
	import Input from '$lib/components/ui/Input.svelte';

	const messageId = $props.id();

	function submit(event: SubmitEvent): void {
		event.preventDefault();
		acceptDialog();
	}
</script>

<Dialog
	open={dialogState.request !== null}
	title={dialogState.request?.title ?? 'Conferma'}
	role="alertdialog"
	aria-describedby={messageId}
	onclose={dismissDialog}
>
	{#if dialogState.request}
		<form onsubmit={submit}>
			<p id={messageId}>{dialogState.request.message}</p>
			{#if dialogState.request.kind === 'prompt'}
				<Input
					bind:value={dialogState.inputValue}
					placeholder={dialogState.request.placeholder}
					data-autofocus
				/>
			{/if}
			<div class="actions">
				<!-- A stray Enter must not confirm a destructive action: focus starts on Cancel. -->
				<Button
					variant="secondary"
					onclick={dismissDialog}
					data-autofocus={dialogState.request.danger || undefined}
				>
					{dialogState.request.cancelLabel ?? 'Annulla'}
				</Button>
				<Button
					type="submit"
					variant={dialogState.request.danger ? 'danger' : 'primary'}
					data-autofocus={(dialogState.request.kind === 'confirm' && !dialogState.request.danger) ||
						undefined}
				>
					{dialogState.request.confirmLabel ?? 'Conferma'}
				</Button>
			</div>
		</form>
	{/if}
</Dialog>

<style>
	form {
		display: grid;
		gap: 1rem;
	}

	p {
		margin: 0;
		color: var(--muted);
		font-size: 0.9rem;
		line-height: 1.55;
	}

	.actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.6rem;
		margin-top: 0.4rem;
	}
</style>
