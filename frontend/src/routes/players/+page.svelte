<script lang="ts">
	import { onMount } from 'svelte';
	import { ApiError } from '$lib/api';
	import {
		getPlayerCounts,
		getPlayers,
		importPlayers,
		type ImportSummary,
		type Player,
		type PlayerCounts,
		type Role
	} from '$lib/players';

	const roleLabels: Record<Role, string> = {
		P: 'Portieri',
		D: 'Difensori',
		C: 'Centrocampisti',
		A: 'Attaccanti'
	};
	const roles = Object.keys(roleLabels) as Role[];

	let players = $state<Player[]>([]);
	let counts = $state<PlayerCounts>({ P: 0, D: 0, C: 0, A: 0 });
	let search = $state('');
	let role = $state<Role | ''>('');
	let includeInactive = $state(false);
	let selectedFile = $state<File>();
	let fileInput: HTMLInputElement;
	let loading = $state(true);
	let importing = $state(false);
	let error = $state('');
	let importSummary = $state<ImportSummary>();
	let total = $derived(Object.values(counts).reduce((sum, count) => sum + count, 0));

	onMount(loadCatalog);

	async function loadCatalog(): Promise<void> {
		loading = true;
		error = '';
		try {
			[players, counts] = await Promise.all([
				getPlayers({
					role: role || undefined,
					search: search.trim() || undefined,
					includeInactive
				}),
				getPlayerCounts()
			]);
		} catch (caught) {
			error = errorMessage(caught);
		} finally {
			loading = false;
		}
	}

	function chooseFile(event: Event): void {
		selectedFile = (event.currentTarget as HTMLInputElement).files?.[0];
		importSummary = undefined;
	}

	async function submitImport(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!selectedFile) return;
		await runImport(false);
	}

	async function runImport(confirmLive: boolean): Promise<void> {
		if (!selectedFile) return;
		importing = true;
		error = '';
		try {
			importSummary = await importPlayers(selectedFile, confirmLive);
			selectedFile = undefined;
			fileInput.value = '';
			await loadCatalog();
		} catch (caught) {
			if (
				caught instanceof ApiError &&
				caught.code === 'confirmation_required' &&
				window.confirm(`${caught.message}\n\nVuoi continuare comunque?`)
			) {
				await runImport(true);
				return;
			}
			error = errorMessage(caught);
		} finally {
			importing = false;
		}
	}

	function errorMessage(caught: unknown): string {
		return caught instanceof Error ? caught.message : 'Si è verificato un errore inatteso.';
	}
</script>

<svelte:head>
	<title>Listone | Asta la Vista</title>
</svelte:head>

<section class="page-heading heading-row">
	<div>
		<p class="eyebrow">Catalogo calciatori</p>
		<h1>Listone</h1>
		<p>Importa il file ufficiale e consulta ruolo, squadra e disponibilità dei calciatori.</p>
	</div>

	<form class="import-form" onsubmit={submitImport}>
		<label for="player-file">File CSV o XLSX</label>
		<div class="file-row">
			<input
				bind:this={fileInput}
				id="player-file"
				type="file"
				accept=".csv,.xlsx"
				onchange={chooseFile}
			/>
			<button type="submit" disabled={!selectedFile || importing}>
				{importing ? 'Importazione…' : 'Importa'}
			</button>
		</div>
	</form>
</section>

{#if error}
	<div class="message error" role="alert">{error}</div>
{/if}

{#if importSummary}
	<div class="message success" role="status">
		Importazione completata: {importSummary.added} nuovi, {importSummary.updated} aggiornati,
		{importSummary.deactivated} disattivati e {importSummary.role_changes} cambi di ruolo.
	</div>
{/if}

<section class="counts" aria-label="Calciatori attivi per ruolo">
	<div class="count-card total-card">
		<span>Totale</span>
		<strong>{total}</strong>
	</div>
	{#each roles as currentRole (currentRole)}
		<div class="count-card">
			<span>{roleLabels[currentRole]}</span>
			<strong>{counts[currentRole]}</strong>
		</div>
	{/each}
</section>

<form
	class="filters"
	onsubmit={(event) => {
		event.preventDefault();
		loadCatalog();
	}}
>
	<label>
		<span>Cerca</span>
		<input bind:value={search} type="search" placeholder="Nome o squadra" />
	</label>
	<label>
		<span>Ruolo</span>
		<select bind:value={role}>
			<option value="">Tutti i ruoli</option>
			{#each roles as currentRole (currentRole)}
				<option value={currentRole}>{roleLabels[currentRole]}</option>
			{/each}
		</select>
	</label>
	<label class="checkbox">
		<input bind:checked={includeInactive} type="checkbox" />
		<span>Mostra inattivi</span>
	</label>
	<button type="submit" disabled={loading}>Applica filtri</button>
</form>

<section class="table-section" aria-live="polite" aria-busy={loading}>
	<div class="table-heading">
		<h2>Calciatori</h2>
		<span>{loading ? 'Caricamento…' : `${players.length} risultati`}</span>
	</div>

	{#if !loading && players.length === 0}
		<div class="empty-state">Nessun calciatore corrisponde ai filtri selezionati.</div>
	{:else}
		<div class="table-scroll">
			<table>
				<thead>
					<tr>
						<th scope="col">Ruolo</th>
						<th scope="col">Calciatore</th>
						<th scope="col">Squadra</th>
						<th scope="col">Stato</th>
					</tr>
				</thead>
				<tbody>
					{#each players as player (player.id)}
						<tr class:inactive={!player.active}>
							<td><span class="role" data-role={player.role}>{player.role}</span></td>
							<td class="player-name">{player.name}</td>
							<td>{player.team}</td>
							<td>{player.active ? 'Disponibile' : 'Inattivo'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
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

	.import-form {
		width: min(100%, 390px);
		padding: 1rem;
		border: 1px solid #d9ddd7;
		border-radius: 0.65rem;
		background: #fafbf8;
	}

	.import-form > label,
	.filters label > span:first-child {
		display: block;
		margin-bottom: 0.45rem;
		font-size: 0.78rem;
		font-weight: 700;
	}

	.file-row {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.file-row input {
		min-width: 0;
		font-size: 0.78rem;
	}

	button {
		min-height: 2.55rem;
		padding: 0 1rem;
		border: 1px solid #204c39;
		border-radius: 0.45rem;
		background: #204c39;
		color: #fff;
		font: inherit;
		font-size: 0.85rem;
		font-weight: 700;
		cursor: pointer;
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.5;
	}

	.message {
		margin-top: 1.5rem;
		padding: 0.85rem 1rem;
		border: 1px solid;
		border-radius: 0.5rem;
		font-size: 0.9rem;
	}

	.error {
		border-color: #d4a7a7;
		background: #fff7f7;
		color: #7a2727;
	}

	.success {
		border-color: #a9c6b5;
		background: #f3faf5;
		color: #204c39;
	}

	.counts {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 0.75rem;
		margin-top: 3rem;
	}

	.count-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 1rem;
		border: 1px solid #d9ddd7;
		border-radius: 0.6rem;
		background: #fafbf8;
	}

	.count-card span {
		color: #5d665f;
		font-size: 0.78rem;
		font-weight: 650;
	}

	.count-card strong {
		font-size: 1.35rem;
	}

	.total-card {
		border-color: #9eaaa2;
	}

	.filters {
		display: grid;
		grid-template-columns: minmax(220px, 1fr) 220px auto auto;
		align-items: end;
		gap: 1rem;
		margin-top: 2rem;
		padding: 1rem;
		border: 1px solid #d9ddd7;
		border-radius: 0.65rem;
		background: #fafbf8;
	}

	.filters input[type='search'],
	.filters select {
		width: 100%;
		height: 2.55rem;
		padding: 0 0.75rem;
		border: 1px solid #bdc5bf;
		border-radius: 0.4rem;
		background: #fff;
		color: inherit;
		font: inherit;
	}

	.checkbox {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		min-height: 2.55rem;
		font-size: 0.85rem;
	}

	.checkbox span {
		margin: 0;
	}

	.table-section {
		margin-top: 2.5rem;
	}

	.table-heading {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 0.8rem;
	}

	.table-heading h2 {
		margin: 0;
		font-size: 1.15rem;
	}

	.table-heading span {
		color: #667069;
		font-size: 0.8rem;
	}

	.table-scroll {
		overflow-x: auto;
		border: 1px solid #d9ddd7;
		border-radius: 0.65rem;
		background: #fafbf8;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.88rem;
	}

	th,
	td {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid #e1e4df;
		text-align: left;
	}

	th {
		color: #667069;
		font-size: 0.72rem;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	tbody tr:last-child td {
		border-bottom: 0;
	}

	tbody tr:hover {
		background: #f1f3ef;
	}

	.inactive {
		color: #8b918d;
		background: #f0f1ef;
	}

	.player-name {
		font-weight: 700;
	}

	.role {
		display: inline-grid;
		place-items: center;
		width: 1.75rem;
		height: 1.75rem;
		border-radius: 0.35rem;
		background: #e2e6e2;
		font-size: 0.75rem;
		font-weight: 800;
	}

	.role[data-role='P'] {
		background: #f3e6bf;
		color: #72560c;
	}

	.role[data-role='D'] {
		background: #d8eadf;
		color: #24583b;
	}

	.role[data-role='C'] {
		background: #dce7f2;
		color: #2b557a;
	}

	.role[data-role='A'] {
		background: #efdddd;
		color: #773434;
	}

	@media (max-width: 900px) {
		.heading-row {
			align-items: stretch;
			flex-direction: column;
			gap: 2rem;
		}

		.counts {
			grid-template-columns: repeat(2, 1fr);
		}

		.filters {
			grid-template-columns: 1fr 1fr;
		}
	}

	@media (max-width: 560px) {
		.counts,
		.filters {
			grid-template-columns: 1fr;
		}
	}
</style>
