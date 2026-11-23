<script lang="ts">
	import type { Snippet } from 'svelte';

	/**
	 * A label above (or, `inline`, beside) a form control. The label wraps the control, unless
	 * `for` names the control's id: needed when the control brings its own label, as FilePicker.
	 */
	let {
		label,
		for: htmlFor,
		inline = false,
		class: className = '',
		children
	}: {
		label: string;
		for?: string;
		inline?: boolean;
		class?: string;
		children: Snippet;
	} = $props();
</script>

{#if htmlFor}
	<div class="field {className}" class:inline>
		<label class="field-label" for={htmlFor}>{label}</label>
		{@render children()}
	</div>
{:else}
	<label class="field {className}" class:inline>
		<span class="field-label">{label}</span>
		{@render children()}
	</label>
{/if}

<style>
	.field {
		display: grid;
		gap: 0.4rem;
		min-width: 0;
	}

	.inline {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		white-space: nowrap;
	}

	.field-label {
		font-size: 0.78rem;
		font-weight: 700;
	}
</style>
