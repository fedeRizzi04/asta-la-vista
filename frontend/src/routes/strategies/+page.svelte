<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { ApiError, saveFile } from '$lib/api';
	import FilePicker from '$lib/components/FilePicker.svelte';
	import Message from '$lib/components/Message.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Dialog from '$lib/components/ui/Dialog.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Menu from '$lib/components/ui/Menu.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import { confirmDialog, promptDialog } from '$lib/dialog.svelte';
	import { t } from '$lib/i18n';
	import { pushErrorToast } from '$lib/toast.svelte';
	import {
		createStrategy,
		deleteStrategy,
		duplicateStrategy,
		exportStrategy,
		getStrategies,
		importStrategy,
		type ImportSummary,
		type StrategySummary
	} from '$lib/strategies';

	let strategies = $state<StrategySummary[]>();
	let createOpen = $state(false);
	let newStrategyName = $state('');
	let loading = $state(true);
	let saving = $state(false);
	let loadVersion = 0;

	let importOpen = $state(false);
	let importName = $state('');
	let importFile = $state<File>();
	let importing = $state(false);
	let importSummary = $state<ImportSummary>();

	onMount(loadStrategies);

	async function loadStrategies(): Promise<void> {
		const version = ++loadVersion;
		loading = true;
		try {
			const result = await getStrategies();
			if (version === loadVersion) strategies = result;
		} catch (caught) {
			if (version === loadVersion) pushErrorToast(caught);
		} finally {
			if (version === loadVersion) loading = false;
		}
	}

	async function submitStrategy(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		const name = newStrategyName.trim();
		if (!name || saving) return;
		saving = true;
		try {
			const { id } = await createStrategy(name);
			newStrategyName = '';
			createOpen = false;
			await goto(resolve('/strategies/[strategyId]', { strategyId: id }));
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			saving = false;
		}
	}

	async function submitImport(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		const name = importName.trim();
		const file = importFile;
		if (!name || !file || importing) return;
		importing = true;
		try {
			const summary = await importStrategy(name, file).catch(async (caught: unknown) => {
				if (!(caught instanceof ApiError) || caught.code !== 'unmatched_players') throw caught;
				const names = caught.params?.names as string[] | undefined;
				if (
					importOpen &&
					(await confirmDialog({
						message: t.strategies.unmatchedPlayersWarning(names ?? []),
						confirmLabel: t.common.continueAnyway
					}))
				) {
					return importStrategy(name, file, true);
				}
			});
			if (!summary) return;
			importSummary = summary;
			importName = '';
			importFile = undefined;
			importOpen = false;
			await loadStrategies();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			importing = false;
		}
	}

	async function duplicate(strategy: StrategySummary): Promise<void> {
		const name = await promptDialog({
			title: t.strategies.duplicateStrategy,
			message: t.strategies.copyNameLabel,
			defaultValue: t.strategies.copyName(strategy.name),
			confirmLabel: t.strategies.duplicate
		});
		if (!name) return;
		saving = true;
		try {
			await duplicateStrategy(strategy.id, name);
			await loadStrategies();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			saving = false;
		}
	}

	async function downloadStrategy(strategy: StrategySummary): Promise<void> {
		try {
			saveFile(await exportStrategy(strategy.id));
		} catch (caught) {
			pushErrorToast(caught);
		}
	}

	async function removeStrategy(strategy: StrategySummary): Promise<void> {
		const confirmed = await confirmDialog({
			title: t.strategies.deleteStrategy,
			message: t.strategies.deleteStrategyMessage(strategy.name),
			confirmLabel: t.strategies.delete,
			danger: true
		});
		if (!confirmed) return;
		saving = true;
		try {
			await deleteStrategy(strategy.id);
			await loadStrategies();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>{t.navigation.strategies} | Asta la Vista</title>
</svelte:head>

<PageHeader title={t.navigation.strategies} compact>
	{#snippet actions()}
		<Button
			variant="secondary"
			size="sm"
			aria-haspopup="dialog"
			aria-disabled={importing || undefined}
			onclick={() => {
				if (!importing) importOpen = true;
			}}
			disabled={saving}
		>
			{t.strategies.importCsv}
		</Button>
		<Button
			size="sm"
			aria-haspopup="dialog"
			onclick={() => (createOpen = true)}
			disabled={saving || importing}
		>
			{t.strategies.newStrategy}
		</Button>
	{/snippet}
</PageHeader>

<Dialog bind:open={createOpen} title={t.strategies.newStrategy} closeLabel={t.common.close}>
	<form onsubmit={submitStrategy}>
		<Field label={t.strategies.strategyName}>
			<Input bind:value={newStrategyName} required data-autofocus />
		</Field>
		<Button class="submit" type="submit" loading={saving} disabled={!newStrategyName.trim()}>
			{t.strategies.create}
		</Button>
	</form>
</Dialog>

<Dialog
	bind:open={importOpen}
	title={t.strategies.importCsv}
	closeLabel={t.common.close}
	onclose={() => (importFile = undefined)}
>
	<form onsubmit={submitImport}>
		<Field label={t.strategies.strategyName}>
			<Input bind:value={importName} required data-autofocus />
		</Field>
		<Field label={t.strategies.csvFile} for="strategy-import-file">
			<FilePicker
				id="strategy-import-file"
				accept=".csv"
				bind:selectedFile={importFile}
				ariaLabel={t.strategies.csvFile}
				onSelect={() => (importSummary = undefined)}
			/>
		</Field>
		<details>
			<summary>{t.strategies.csvFormat}</summary>
			<p>
				{t.strategies.csvColumns} <code>Nome,Fascia,MaxPrezzo%,Note</code>. {t.strategies
					.csvNameRequired}
				<code>Colore</code>
				{t.strategies.csvOptionalColor} <code>#ef4444</code>). {t.strategies.csvUnmatched}
			</p>
		</details>
		<Button
			class="submit"
			type="submit"
			loading={importing}
			disabled={!importName.trim() || !importFile}
		>
			{t.common.import}
		</Button>
	</form>
</Dialog>

{#if importSummary}
	<div class="import-summary">
		<Message kind="success">
			{t.strategies.importSummary(
				importSummary.tiers_created,
				importSummary.players_assigned,
				importSummary.unmatched
			)}
		</Message>
	</div>
{/if}

<div aria-busy={loading}>
	{#if loading && !strategies?.length}
		<p class="count-label">{t.common.loading}</p>
	{:else if !strategies}
		<EmptyState>{t.strategies.loadFailed}</EmptyState>
	{:else if strategies.length === 0}
		<EmptyState>{t.strategies.noStrategies}</EmptyState>
	{:else}
		<div class="strategy-list">
			{#each strategies as strategy (strategy.id)}
				<article>
					<div class="details">
						<h2>{strategy.name}</h2>
						<p>
							{t.strategies.strategySummary(strategy.tier_count, strategy.assigned_player_count)}
						</p>
					</div>
					<div class="actions">
						<Button
							href={resolve('/strategies/[strategyId]', { strategyId: strategy.id })}
							variant="secondary"
							size="sm"
							aria-label={t.strategies.openStrategy(strategy.name)}
						>
							{t.strategies.open}
						</Button>
						<Menu
							label={t.strategies.actionsForStrategy(strategy.name)}
							size="sm"
							disabled={saving || importing}
							items={[
								{ label: t.strategies.exportCsv, onselect: () => downloadStrategy(strategy) },
								{ label: t.strategies.duplicateMenu, onselect: () => duplicate(strategy) },
								{ label: t.strategies.deleteMenu, onselect: () => removeStrategy(strategy) }
							]}
						/>
					</div>
				</article>
			{/each}
		</div>
	{/if}
</div>

<style>
	form {
		display: grid;
		gap: 0.8rem;
	}

	form :global(.submit) {
		justify-self: end;
	}

	details {
		color: var(--muted);
		font-size: 0.8rem;
	}

	summary {
		width: fit-content;
		font-weight: 700;
		cursor: pointer;
	}

	details p {
		margin: 0.35rem 0 0;
		overflow-wrap: anywhere;
	}

	.import-summary {
		margin-bottom: 0.65rem;
		overflow-wrap: anywhere;
	}

	.strategy-list {
		display: grid;
		gap: 0.65rem;
	}

	article {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 0.6rem 1rem;
		padding: 0.75rem;
		border: var(--bw) solid var(--line);
		border-radius: var(--radius-sm);
		background: var(--surface);
	}

	.details {
		min-width: 0;
		overflow-wrap: anywhere;
	}

	h2 {
		margin: 0;
		font-size: 1rem;
		font-weight: 800;
	}

	article p {
		margin: 0.3rem 0 0;
		color: var(--muted);
		font-size: 0.85rem;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}
</style>
