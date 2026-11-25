<script lang="ts">
	import type { Snippet } from 'svelte';
	import { registerOpenDialog } from '$lib/toast.svelte';
	import ToastStack from '../ToastStack.svelte';
	import Button from './Button.svelte';

	/**
	 * A modal on the native <dialog>: the browser traps focus, makes the page behind inert,
	 * stacks a second dialog (e.g. a confirmation) above the first and closes the top one on
	 * Esc. Every way of closing (Esc, a click on the backdrop, the close button) goes through
	 * the native `close` event, which sets `open` to false and calls `onclose` (only for these
	 * dismissals, not when the parent sets `open` to false itself). After opening,
	 * focus moves to the element marked `data-autofocus`, if any.
	 */
	let {
		open = $bindable(false),
		title,
		role = 'dialog',
		placement = 'center',
		width = '420px',
		closeLabel,
		onclose,
		children,
		...rest
	}: {
		open?: boolean;
		title: string;
		role?: 'dialog' | 'alertdialog';
		/** `side` slides in from the right edge, full height: see Drawer. */
		placement?: 'center' | 'side';
		width?: string;
		/** Shows a close button in the header when set. */
		closeLabel?: string;
		onclose?: () => void;
		children: Snippet;
		'aria-describedby'?: string;
	} = $props();

	const titleId = $props.id();
	let dialog = $state<HTMLDialogElement>();
	let pressStartedOnBackdrop = false;

	$effect(() => {
		if (!dialog) return;
		if (open && !dialog.open) {
			dialog.showModal();
			dialog.querySelector<HTMLElement>('[data-autofocus]')?.focus();
		} else if (!open && dialog.open) {
			dialog.close();
		}
	});

	// Covers every way of closing, including a dialog destroyed while open (no `close` event).
	$effect(() => {
		if (open) return registerOpenDialog(titleId);
	});

	function handleClose(): void {
		// Skip closes the parent asked for, and a late `close` from a dialog reopened since.
		if (!open || dialog?.open) return;
		open = false;
		onclose?.();
	}

	// The backdrop is the <dialog> element itself (its content sits in .dialog-body), and a
	// press that starts inside and ends outside (selecting text) must not close it.
	function handlePointerDown(event: PointerEvent): void {
		pressStartedOnBackdrop = event.target === dialog;
	}

	function handleClick(event: MouseEvent): void {
		if (pressStartedOnBackdrop && event.target === dialog) dialog?.close();
		pressStartedOnBackdrop = false;
	}
</script>

<!-- The backdrop click has a keyboard equivalent: Esc, handled natively by <dialog>. -->
<dialog
	bind:this={dialog}
	class={placement}
	{role}
	aria-labelledby={titleId}
	style:--dialog-width={width}
	onclose={handleClose}
	onpointerdown={handlePointerDown}
	onclick={handleClick}
	{...rest}
>
	{#if open}
		<div class="dialog-body">
			<header>
				<h2 id={titleId}>{title}</h2>
				{#if closeLabel}
					<Button variant="text" size="sm" onclick={() => dialog?.close()}>{closeLabel}</Button>
				{/if}
			</header>
			{@render children()}
		</div>
	{/if}
	<!-- After the content, so that opening never focuses a toast's dismiss button. -->
	<ToastStack dialogId={titleId} />
</dialog>

<style>
	dialog {
		width: min(var(--dialog-width), calc(100vw - 2rem));
		max-height: min(85vh, 720px);
		padding: 0;
		border: var(--bw) solid var(--line);
		border-radius: var(--radius);
		background: var(--surface);
		color: var(--text);
		box-shadow: var(--shadow);
	}

	dialog[open] {
		display: flex;
		flex-direction: column;
		animation: dialog-in 180ms ease-out;
	}

	/* A literal colour: older WebKit (the macOS app's web view) does not resolve custom
	   properties on ::backdrop. */
	dialog::backdrop {
		background: rgb(20 15 10 / 50%);
		animation: backdrop-in 160ms ease;
	}

	.side {
		height: 100dvh;
		max-height: none;
		margin: 0 0 0 auto;
		border-width: 0 0 0 var(--bw);
		border-radius: 0;
		box-shadow: -4px 0 0 var(--line);
	}

	.side[open] {
		animation-name: drawer-in;
	}

	.dialog-body {
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
		min-height: 0;
		padding: 1.5rem;
		overflow: auto;
	}

	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	h2 {
		margin: 0;
		font-size: 1.15rem;
	}

	/* Moved with insets: a transform would make the dialog, rather than the viewport, the
	   containing block of the fixed toasts inside it. */
	@keyframes dialog-in {
		from {
			opacity: 0;
			top: 12px;
		}
	}

	@keyframes drawer-in {
		from {
			right: -2rem;
			opacity: 0;
		}
	}

	@keyframes backdrop-in {
		from {
			opacity: 0;
		}
	}
</style>
