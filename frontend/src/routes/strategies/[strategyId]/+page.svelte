<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onDestroy, untrack } from 'svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Menu from '$lib/components/ui/Menu.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Tabs from '$lib/components/ui/Tabs.svelte';
	import EntryEditor from '$lib/features/strategy/EntryEditor.svelte';
	import { PlayerDrag } from '$lib/features/strategy/playerDrag.svelte';
	import PlayerDragPreview from '$lib/features/strategy/PlayerDragPreview.svelte';
	import PlayerPool from '$lib/features/strategy/PlayerPool.svelte';
	import { referenceBudget } from '$lib/features/strategy/referenceBudget.svelte';
	import SelectionBar from '$lib/features/strategy/SelectionBar.svelte';
	import { StrategyEditor } from '$lib/features/strategy/strategyEditor.svelte';
	import StrategyTiers from '$lib/features/strategy/StrategyTiers.svelte';
	import { roleLabels, roles, type Role } from '$lib/players';

	const strategyId = $derived(page.params.strategyId);
	const editor = new StrategyEditor(() => strategyId);
	const drag = new PlayerDrag(editor);
	const strategy = $derived(editor.strategy);
	const roleTabs = roles.map((role) => ({ value: role, label: roleLabels[role] }));

	let selectedRole = $state<Role>('P');
	let budgetInput = $state<number | undefined>(referenceBudget.value);

	async function duplicate(): Promise<void> {
		const sourceId = strategyId;
		const copyId = await editor.duplicate();
		if (copyId && strategyId === sourceId) {
			await goto(resolve('/strategies/[strategyId]', { strategyId: copyId }));
		}
	}

	$effect(() => {
		if (strategyId) untrack(() => void editor.load());
	});
	onDestroy(() => void editor.flushAll());
</script>

<!-- A reload or a closed window does not destroy the component. -->
<svelte:window onpagehide={() => editor.flushOnUnload()} />

<svelte:head>
	<title>{strategy?.name ?? 'Strategia'} | Asta la Vista</title>
</svelte:head>

<div class="editor">
	<PageHeader compact back={{ href: resolve('/strategies'), label: 'Strategie' }}>
		{#snippet title()}
			{#if strategy && !editor.loading}
				<span class="strategy-title">
					<Input
						class="inline-name"
						bind:value={editor.strategyName}
						aria-label="Nome della strategia"
						autocomplete="off"
						oninput={() => editor.scheduleNameSave()}
						onblur={() => editor.flushNameSave()}
						onkeydown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
					/>
					<span class="save-status" role="status">
						{editor.strategySaved[strategy.id] ? 'Salvato' : ''}
					</span>
				</span>
			{:else}
				Strategia
			{/if}
		{/snippet}
		{#snippet actions()}
			{#if strategy && !editor.loading}
				<Field label="Budget di riferimento" inline for="reference-budget">
					<Input
						id="reference-budget"
						class="budget-input"
						type="number"
						min="1"
						bind:value={budgetInput}
						oninput={(event) => (referenceBudget.value = event.currentTarget.valueAsNumber)}
						onblur={() => (budgetInput = referenceBudget.value)}
					/>
					<span class="budget-unit">cr</span>
				</Field>
				<Menu
					label="Azioni della strategia"
					items={[
						{ label: 'Esporta CSV', onselect: () => void editor.exportCsv() },
						{ label: 'Duplica…', onselect: () => void duplicate() }
					]}
				/>
			{/if}
		{/snippet}
	</PageHeader>

	{#if editor.loading}
		<EmptyState>Caricamento della strategia…</EmptyState>
	{:else if strategy}
		<div class="toolbar">
			<Tabs
				items={roleTabs}
				bind:value={selectedRole}
				label="Ruoli"
				id="strategy-role"
				panelId="strategy-role-panel"
				onchange={() => editor.selection.clear()}
			/>
			<SelectionBar {editor} workspaceId="strategy-role-panel" />
		</div>
		<div
			id="strategy-role-panel"
			class="workspace"
			role="tabpanel"
			tabindex="0"
			aria-labelledby="strategy-role-{selectedRole}"
			use:drag.area
		>
			<PlayerPool {editor} {drag} role={selectedRole} />
			<StrategyTiers {editor} {drag} role={selectedRole} />
		</div>
		<PlayerDragPreview {drag} />
		<EntryEditor {editor} />
	{/if}
</div>

<style>
	/* The tiers need the whole width of the window. */
	:global(main):has(.editor) {
		width: calc(100% - 3rem);
	}

	/* Fills the window, down to a gap as big as the padding above, so that only the pool and
	   the board scroll. */
	.editor {
		display: flex;
		flex-direction: column;
		height: calc(100dvh - var(--header-height) - 3rem);
		min-height: 30rem;
	}

	.toolbar {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem 1rem;
		margin-bottom: 0.6rem;
	}

	.workspace {
		display: grid;
		flex: 1;
		grid-template: minmax(0, 1fr) / 19.5rem minmax(0, 1fr);
		gap: 1rem;
		min-height: 0;
	}

	.strategy-title {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}

	.strategy-title :global(.inline-name) {
		width: min(25rem, 100%);
		font: inherit;
	}

	.strategy-title .save-status {
		flex: none;
		font-family: var(--font-text);
	}

	.editor :global(.budget-input) {
		width: 5.5rem;
		text-align: right;
	}

	.budget-unit {
		color: var(--muted);
		font-size: 0.8rem;
	}

	@media (max-width: 900px) {
		.editor {
			height: auto;
		}

		.workspace {
			grid-template: 24rem auto / minmax(0, 1fr);
		}
	}

	@media (max-width: 720px) {
		:global(main):has(.editor) {
			width: calc(100% - 2rem);
		}
	}
</style>
