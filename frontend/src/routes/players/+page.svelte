<script lang="ts">
	import { onMount } from 'svelte';
	import { ApiError } from '$lib/api';
	import FilePicker from '$lib/components/FilePicker.svelte';
	import Message from '$lib/components/Message.svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import SectionHeading from '$lib/components/SectionHeading.svelte';
	import { confirmDialog } from '$lib/dialog.svelte';
	import { pushErrorToast } from '$lib/toast.svelte';
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
	let loading = $state(true);
	let importing = $state(false);
	let importSummary = $state<ImportSummary>();
	let total = $derived(Object.values(counts).reduce((sum, count) => sum + count, 0));

	onMount(loadCatalog);

	async function loadCatalog(): Promise<void> {
		loading = true;
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
			pushErrorToast(caught);
		} finally {
			loading = false;
		}
	}

	async function submitImport(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!selectedFile) return;
		await runImport(false);
	}

	async function runImport(confirmLive: boolean): Promise<void> {
		if (!selectedFile) return;
		importing = true;
		try {
			importSummary = await importPlayers(selectedFile, confirmLive);
			selectedFile = undefined;
			await loadCatalog();
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
</script>

<svelte:head>
	<title>Listone | Asta la Vista</title>
</svelte:head>

<section class="page-heading heading-row">
	<div>
		<p class="eyebrow">Catalogo calciatori</p>
		<h1>Listone</h1>
		<p>Importa il file ufficiale e consulta ruolo, squadra, quotazione e disponibilità.</p>
	</div>

	<form class="import-form" onsubmit={submitImport}>
		<label for="player-file">File CSV o XLSX</label>
		<div class="file-row">
			<FilePicker
				id="player-file"
				accept=".csv,.xlsx"
				bind:selectedFile
				ariaLabel="File del Listone"
				onSelect={() => (importSummary = undefined)}
			/>
			<button type="submit" disabled={!selectedFile || importing}>
				{importing ? 'Importazione…' : 'Importa'}
			</button>
		</div>
	</form>
</section>

{#if importSummary}
	<Message kind="success">
		Importazione completata: {importSummary.added} nuovi, {importSummary.updated} aggiornati,
		{importSummary.deactivated} disattivati e {importSummary.role_changes} cambi di ruolo.
	</Message>
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
	<SectionHeading title="Calciatori">
		{#snippet trailing()}
			<span class="count-label">{loading ? 'Caricamento…' : `${players.length} risultati`}</span>
		{/snippet}
	</SectionHeading>

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
						<th scope="col">Quotazione</th>
						<th scope="col">Stato</th>
					</tr>
				</thead>
				<tbody>
					{#each players as player (player.id)}
						<tr class:inactive={!player.active}>
							<td><span class="role" data-role={player.role}>{player.role}</span></td>
							<td class="player-name"
								>{player.name}
								<MantraRoleBadges roles={player.mantra_roles} compact /></td
							>
							<td>{player.team}</td>
							<td class="quotation">{player.quotation ?? '—'}</td>
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
		border: 1px solid var(--border);
		border-radius: 0.65rem;
		background: var(--surface);
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

	button {
		min-height: 2.55rem;
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

	button:disabled {
		cursor: not-allowed;
		opacity: 0.5;
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
		border: 1px solid var(--border);
		border-radius: 0.6rem;
		background: var(--surface);
	}

	.count-card span {
		color: var(--muted);
		font-size: 0.78rem;
		font-weight: 650;
	}

	.count-card strong {
		font-size: 1.35rem;
	}

	.total-card {
		border-color: var(--border-hover);
	}

	.filters {
		display: grid;
		grid-template-columns: minmax(220px, 1fr) 220px auto auto;
		align-items: end;
		gap: 1rem;
		margin-top: 2rem;
		padding: 1rem;
		border: 1px solid var(--border);
		border-radius: 0.65rem;
		background: var(--surface);
	}

	.filters input[type='search'],
	.filters select {
		width: 100%;
		height: 2.55rem;
		padding: 0 0.75rem;
		border: 1px solid var(--border-strong);
		border-radius: 0.4rem;
		background: var(--input-bg);
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

	.table-scroll {
		overflow-x: auto;
		border: 1px solid var(--border);
		border-radius: 0.65rem;
		background: var(--surface);
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.88rem;
	}

	th,
	td {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
		text-align: left;
	}

	th {
		color: var(--subdued);
		font-size: 0.72rem;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	tbody tr:last-child td {
		border-bottom: 0;
	}

	tbody tr:hover {
		background: var(--muted-bg);
	}

	.inactive {
		color: var(--disabled-text);
		background: var(--muted-bg);
	}

	.player-name {
		font-weight: 700;
	}

	.quotation {
		font-variant-numeric: tabular-nums;
		font-weight: 700;
	}

	.role {
		display: inline-grid;
		place-items: center;
		width: 1.75rem;
		height: 1.75rem;
		border-radius: 0.35rem;
		background: var(--muted-bg);
		font-size: 0.75rem;
		font-weight: 800;
	}

	.role[data-role='P'] {
		background: var(--goalkeeper-bg);
		color: var(--goalkeeper-text);
	}

	.role[data-role='D'] {
		background: var(--defender-bg);
		color: var(--defender-text);
	}

	.role[data-role='C'] {
		background: var(--midfielder-bg);
		color: var(--midfielder-text);
	}

	.role[data-role='A'] {
		background: var(--forward-bg);
		color: var(--forward-text);
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
