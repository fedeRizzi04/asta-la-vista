<script lang="ts">
	let {
		id,
		accept,
		selectedFile = $bindable<File | undefined>(),
		ariaLabel = 'Scegli un file',
		onSelect
	}: {
		id: string;
		accept: string;
		selectedFile?: File;
		ariaLabel?: string;
		onSelect?: (file: File | undefined) => void;
	} = $props();

	let input: HTMLInputElement;

	function chooseFile(event: Event): void {
		selectedFile = (event.currentTarget as HTMLInputElement).files?.[0];
		onSelect?.(selectedFile);
	}

	$effect(() => {
		if (!selectedFile && input?.value) input.value = '';
	});
</script>

<input
	bind:this={input}
	{id}
	class="file-input"
	type="file"
	{accept}
	onchange={chooseFile}
	aria-label={ariaLabel}
/>
<label for={id} class="file-picker" class:has-file={!!selectedFile}>
	<svg class="file-icon" viewBox="0 0 24 24" aria-hidden="true">
		<path d="M6 3.5h8.5L19 8v12a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" />
		<path d="M14.5 3.5V8H19" />
		<path d="M8 12h8M8 15.5h8M11.5 12v6.5" />
	</svg>
	<span class="file-picker-text">{selectedFile ? selectedFile.name : 'Scegli file…'}</span>
</label>

<style>
	.file-input {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	.file-picker {
		display: flex;
		flex: 1;
		min-width: 0;
		align-items: center;
		gap: 0.55rem;
		height: 2.55rem;
		padding: 0 0.75rem;
		border: 1px solid var(--border-strong);
		border-radius: 0.4rem;
		background: var(--input-bg);
		color: var(--muted);
		font-size: 0.78rem;
		cursor: pointer;
		transition:
			border-color 0.15s ease,
			background 0.15s ease,
			color 0.15s ease;
	}

	.file-picker:hover {
		border-color: var(--border-hover);
	}

	.file-input:focus-visible + .file-picker {
		outline: 2px solid var(--primary);
		outline-offset: 1px;
	}

	.file-picker.has-file {
		border-color: var(--primary);
		background: var(--primary-soft);
		color: var(--primary-soft-text);
	}

	.file-icon {
		flex-shrink: 0;
		width: 1.15rem;
		height: 1.15rem;
		fill: none;
		stroke: currentColor;
		stroke-width: 1.6;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.file-picker-text {
		overflow: hidden;
		white-space: nowrap;
		text-overflow: ellipsis;
	}
</style>
