<script lang="ts">
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { ApiError, saveFile } from '$lib/api';
	import FilePicker from '$lib/components/FilePicker.svelte';
	import Message from '$lib/components/Message.svelte';
	import SectionHeading from '$lib/components/SectionHeading.svelte';
	import { confirmDialog, promptDialog } from '$lib/dialog.svelte';
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

	let strategies = $state<StrategySummary[]>([]);
	let newStrategyName = $state('');
	let loading = $state(true);
	let saving = $state(false);

	let importName = $state('');
	let importFile = $state<File>();
	let importing = $state(false);
	let importSummary = $state<ImportSummary>();

	onMount(loadStrategies);

	async function loadStrategies(): Promise<void> {
		loading = true;
		try {
			strategies = await getStrategies();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			loading = false;
		}
	}

	async function submitStrategy(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		const name = newStrategyName.trim();
		if (!name) return;
		saving = true;
		try {
			await createStrategy(name);
			newStrategyName = '';
			await loadStrategies();
		} catch (caught) {
			pushErrorToast(caught);
		} finally {
			saving = false;
		}
	}

	async function submitImport(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!importName.trim() || !importFile) return;
		await runImport(false);
	}

	async function runImport(confirmUnmatched: boolean): Promise<void> {
		const name = importName.trim();
		if (!name || !importFile) return;
		importing = true;
		try {
			importSummary = await importStrategy(name, importFile, confirmUnmatched);
			importName = '';
			importFile = undefined;
			await loadStrategies();
		} catch (caught) {
			if (
				caught instanceof ApiError &&
				caught.code === 'confirmation_required' &&
				(await confirmDialog({ message: caught.message, confirmLabel: 'Continua comunque' }))
			) {
				await runImport(true);
				return;
			}
			pushErrorToast(caught);
		} finally {
			importing = false;
		}
	}

	async function duplicate(strategy: StrategySummary): Promise<void> {
		const name = await promptDialog({
			title: 'Duplica strategia',
			message: 'Nome della nuova strategia',
			defaultValue: `${strategy.name} - copia`,
			confirmLabel: 'Duplica'
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
			title: 'Elimina strategia',
			message: `Eliminare la strategia “${strategy.name}”? Questa azione non può essere annullata.`,
			confirmLabel: 'Elimina',
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
	<title>Strategie | Asta la Vista</title>
</svelte:head>

<section class="page-heading heading-row">
	<div>
		<p class="eyebrow">Pianificazione dell'asta</p>
		<h1>Strategie</h1>
		<p>Crea fasce globali riutilizzabili e organizza al loro interno i calciatori di ogni ruolo.</p>
	</div>

	<form class="create-form" onsubmit={submitStrategy}>
		<label for="strategy-name">Nuova strategia</label>
		<div>
			<input
				id="strategy-name"
				bind:value={newStrategyName}
				placeholder="Ad esempio: Asta principale"
			/>
			<button type="submit" disabled={!newStrategyName.trim() || saving}>Crea</button>
		</div>
	</form>
</section>

<section class="import-section">
	<form class="import-form" onsubmit={submitImport}>
		<div class="import-intro">
			<label for="import-strategy-name">Importa una strategia da CSV</label>
			<p>Crea una nuova strategia a partire dalle fasce che hai già preparato.</p>
		</div>
		<div class="import-fields">
			<input id="import-strategy-name" bind:value={importName} placeholder="Nome della strategia" />
			<div class="file-row">
				<FilePicker
					id="strategy-import-file"
					accept=".csv"
					bind:selectedFile={importFile}
					ariaLabel="File CSV della strategia"
					onSelect={() => (importSummary = undefined)}
				/>
				<button type="submit" disabled={!importName.trim() || !importFile || importing}>
					{importing ? 'Importazione…' : 'Importa'}
				</button>
			</div>
		</div>
		<p class="hint">
			Il file deve contenere le colonne <code>Nome,Fascia,MaxPrezzo%,Note</code>. Fascia, prezzo
			massimo e nota sono facoltativi. Puoi aggiungere anche una colonna facoltativa
			<code>Colore</code> con il colore della fascia in esadecimale (per esempio
			<code>#ef4444</code>): è quello che trovi nei file esportati da qui. Se un nome non
			corrisponde a nessun calciatore del Listone ti verrà chiesto se vuoi procedere comunque,
			ignorando quel calciatore.
		</p>
	</form>
</section>

{#if importSummary}
	<Message kind="success">
		Strategia creata: {importSummary.tiers_created} fasce e {importSummary.players_assigned} calciatori
		assegnati.
		{#if importSummary.unmatched.length}
			{importSummary.unmatched.length} non trovati e ignorati: {importSummary.unmatched.join(', ')}.
		{/if}
	</Message>
{/if}

<section class="strategy-section" aria-live="polite" aria-busy={loading}>
	<SectionHeading title="Le tue strategie">
		{#snippet trailing()}
			<span class="count-label">{loading ? 'Caricamento…' : `${strategies.length} strategie`}</span>
		{/snippet}
	</SectionHeading>

	{#if !loading && strategies.length === 0}
		<div class="empty-state">Non ci sono ancora strategie. Creane una per iniziare.</div>
	{:else}
		<div class="strategy-list">
			{#each strategies as strategy (strategy.id)}
				<article>
					<div>
						<h3>{strategy.name}</h3>
						<p>
							{strategy.tier_count} fasce · {strategy.assigned_player_count} calciatori assegnati
						</p>
					</div>
					<div class="actions">
						<button
							class="secondary"
							type="button"
							onclick={() => downloadStrategy(strategy)}
							disabled={saving}
						>
							Esporta
						</button>
						<button
							class="secondary"
							type="button"
							onclick={() => duplicate(strategy)}
							disabled={saving}
						>
							Duplica
						</button>
						<button
							class="danger"
							type="button"
							onclick={() => removeStrategy(strategy)}
							disabled={saving}
						>
							Elimina
						</button>
						<a href={resolve('/strategies/[strategyId]', { strategyId: strategy.id })}>Apri</a>
					</div>
				</article>
			{/each}
		</div>
	{/if}
</section>

<style>
	.heading-row {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 3rem;
		max-width: none;
	}

	.heading-row > div:first-child {
		max-width: 680px;
	}

	.create-form {
		width: min(100%, 390px);
		padding: 1rem;
		border: 1px solid var(--border);
		border-radius: 0.65rem;
		background: var(--surface);
	}

	.create-form label {
		display: block;
		margin-bottom: 0.45rem;
		font-size: 0.78rem;
		font-weight: 700;
	}

	.create-form > div,
	.actions {
		display: flex;
		gap: 0.65rem;
	}

	.create-form input {
		min-width: 0;
		flex: 1;
		height: 2.55rem;
		padding: 0 0.75rem;
		border: 1px solid var(--border-strong);
		border-radius: 0.4rem;
		font: inherit;
	}

	.import-section {
		margin-top: 1.5rem;
	}

	.import-form {
		width: min(100%, 560px);
		padding: 1.2rem;
		border: 1px solid var(--border);
		border-radius: 0.75rem;
		background: var(--surface);
	}

	.import-intro label {
		margin: 0;
		font-size: 0.95rem;
	}

	.import-intro p {
		margin: 0.3rem 0 0;
		color: var(--subdued);
		font-size: 0.8rem;
	}

	.import-fields {
		display: grid;
		gap: 0.65rem;
		margin-top: 0.9rem;
	}

	.import-fields > input {
		width: 100%;
		min-width: 0;
		height: 2.55rem;
		padding: 0 0.75rem;
		border: 1px solid var(--border-strong);
		border-radius: 0.4rem;
		font: inherit;
	}

	.file-row {
		display: flex;
		align-items: center;
		gap: 0.65rem;
	}

	.import-form .hint {
		margin: 0.8rem 0 0;
		color: var(--subdued);
		font-size: 0.76rem;
	}

	.import-form .hint code {
		font-size: 0.74rem;
	}

	button,
	.actions a {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 2.55rem;
		padding: 0 1rem;
		border: 1px solid var(--primary);
		border-radius: 0.45rem;
		background: var(--primary);
		color: var(--on-primary);
		font: inherit;
		font-size: 0.85rem;
		font-weight: 700;
		text-decoration: none;
		cursor: pointer;
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.5;
	}

	button.secondary {
		border-color: var(--border-strong);
		background: transparent;
		color: var(--text);
	}

	button.danger {
		border-color: transparent;
		background: transparent;
		color: var(--error-text);
	}

	.strategy-section {
		margin-top: 3rem;
	}

	.strategy-list {
		display: grid;
		gap: 0.75rem;
	}

	article {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 2rem;
		padding: 1.25rem;
		border: 1px solid var(--border);
		border-radius: 0.65rem;
		background: var(--surface);
	}

	article h3 {
		margin: 0;
		font-size: 1rem;
	}

	article p {
		margin: 0.4rem 0 0;
		color: var(--subdued);
		font-size: 0.84rem;
	}

	@media (max-width: 720px) {
		.heading-row,
		article {
			align-items: stretch;
			flex-direction: column;
		}

		.actions > * {
			flex: 1;
		}
	}
</style>
