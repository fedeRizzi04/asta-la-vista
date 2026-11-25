<script lang="ts">
	import { getAbortSignal } from 'svelte';
	import { ApiError } from '$lib/api';
	import FilePicker from '$lib/components/FilePicker.svelte';
	import Message from '$lib/components/Message.svelte';
	import MantraRoleBadges from '$lib/components/MantraRoleBadges.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Dialog from '$lib/components/ui/Dialog.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Field from '$lib/components/ui/Field.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import PageHeader from '$lib/components/ui/PageHeader.svelte';
	import Tabs from '$lib/components/ui/Tabs.svelte';
	import ToggleChip from '$lib/components/ui/ToggleChip.svelte';
	import { confirmDialog } from '$lib/dialog.svelte';
	import { t } from '$lib/i18n';
	import { pushErrorToast } from '$lib/toast.svelte';
	import { getUrlParams, setUrlParams } from '$lib/urlState';
	import {
		getPlayerCounts,
		getPlayers,
		importPlayers,
		roleLabels,
		roles,
		type ImportSummary,
		type Player,
		type PlayerCounts,
		type PlayerFilters,
		type Role
	} from '$lib/players';

	type RoleFilter = Role | 'all';
	type SortColumn = 'name' | 'team' | 'quotation';

	let players = $state<Player[]>([]);
	let counts = $state<PlayerCounts>({ P: 0, D: 0, C: 0, A: 0 });
	let search = $state('');
	let includeInactive = $state(false);
	let loading = $state(true);
	let catalogRevision = $state(0);
	let sort = $state<{ column: SortColumn; direction: 'ascending' | 'descending' }>();
	let tablePanel: HTMLDivElement;
	let importOpen = $state(false);
	let selectedFile = $state<File>();
	let importing = $state(false);
	let importSummary = $state<ImportSummary>();

	const role = $derived.by<RoleFilter>(() => {
		const value = getUrlParams().get('role');
		return roles.find((candidate) => candidate === value) ?? 'all';
	});
	const total = $derived(roles.reduce((sum, role) => sum + counts[role], 0));
	const roleTabs = $derived([
		{ value: 'all' as const, label: t.players.allCount(total), title: t.players.allRoles },
		...roles.map((value) => ({
			value,
			label: `${value} ${counts[value]}`,
			title: roleLabels[value]
		}))
	]);
	const sortedPlayers = $derived.by(() => {
		if (!sort) return players;
		const { column, direction } = sort;
		const order = direction === 'ascending' ? 1 : -1;
		return [...players].sort((first, second) => {
			if (column === 'quotation') {
				if (first.quotation === null) return second.quotation === null ? 0 : 1;
				if (second.quotation === null) return -1;
				return order * (first.quotation - second.quotation);
			}
			return order * first[column].localeCompare(second[column], 'it');
		});
	});

	const searchFilter = $derived(search.trim() || undefined);
	const immediateFilters = $derived({ role, includeInactive, catalogRevision });
	let previousFilters: typeof immediateFilters | undefined;

	$effect(() => {
		const filters = immediateFilters;
		const query: PlayerFilters = {
			role: filters.role === 'all' ? undefined : filters.role,
			includeInactive: filters.includeInactive,
			search: searchFilter
		};
		const signal = getAbortSignal();
		// Only search changes wait. A role change, toggle, or import uses the current search.
		const debounce = previousFilters === filters;
		previousFilters = filters;
		loading = true;

		if (!debounce) {
			void loadPlayers(query, signal);
			return;
		}
		const timer = setTimeout(() => void loadPlayers(query, signal), 250);
		return () => clearTimeout(timer);
	});

	$effect(() => {
		void catalogRevision;
		const signal = getAbortSignal();
		void loadCounts(signal);
	});

	function setRole(next: RoleFilter): void {
		void setUrlParams({ role: next === 'all' ? null : next });
	}

	function sortBy(column: SortColumn): void {
		const descending = sort?.column === column && sort.direction === 'ascending';
		sort = { column, direction: descending ? 'descending' : 'ascending' };
		tablePanel.scrollTop = 0;
	}

	async function loadPlayers(filters: PlayerFilters, signal: AbortSignal): Promise<void> {
		try {
			const result = await getPlayers(filters);
			if (signal.aborted) return;
			players = result;
			tablePanel.scrollTop = 0;
		} catch (caught) {
			if (!signal.aborted) pushErrorToast(caught);
		} finally {
			if (!signal.aborted) loading = false;
		}
	}

	async function loadCounts(signal: AbortSignal): Promise<void> {
		try {
			const result = await getPlayerCounts();
			if (!signal.aborted) counts = result;
		} catch (caught) {
			if (!signal.aborted) pushErrorToast(caught);
		}
	}

	async function submitImport(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!selectedFile || importing) return;
		await runImport(false);
	}

	async function runImport(confirmLive: boolean): Promise<void> {
		if (!selectedFile) return;
		importing = true;
		try {
			importSummary = await importPlayers(selectedFile, confirmLive);
			selectedFile = undefined;
			importOpen = false;
			catalogRevision += 1;
		} catch (caught) {
			if (caught instanceof ApiError && caught.code === 'live_auction_import') {
				const confirmed = await confirmDialog({
					message: t.players.liveImportWarning,
					confirmLabel: t.common.continueAnyway
				});
				if (confirmed) await runImport(true);
				return;
			}
			pushErrorToast(caught);
		} finally {
			importing = false;
		}
	}
</script>

<svelte:head>
	<title>{t.navigation.playerList} | Asta la Vista</title>
</svelte:head>

<PageHeader title={t.navigation.playerList} compact>
	{#snippet actions()}
		<Button
			variant="secondary"
			size="sm"
			aria-haspopup="dialog"
			onclick={() => (importOpen = true)}
		>
			{t.common.import}
		</Button>
	{/snippet}
</PageHeader>

<Dialog
	bind:open={importOpen}
	title={t.players.importPlayerList}
	width="28rem"
	closeLabel={t.common.close}
>
	<form onsubmit={submitImport}>
		<Field label={t.players.fileLabel} for="player-file">
			<div class="file-row">
				<FilePicker
					id="player-file"
					accept=".csv,.xlsx"
					bind:selectedFile
					ariaLabel={t.players.fileLabel}
					onSelect={() => (importSummary = undefined)}
					disabled={importing}
					data-autofocus
				/>
				<Button type="submit" loading={importing} disabled={!selectedFile}>{t.common.import}</Button
				>
			</div>
		</Field>
	</form>
</Dialog>

{#if importSummary}
	<Message kind="success">
		{t.players.importSummary(
			importSummary.added,
			importSummary.updated,
			importSummary.deactivated,
			importSummary.role_changes
		)}
	</Message>
{/if}

<div class="filters">
	<Tabs
		items={roleTabs}
		bind:value={() => role, setRole}
		label={t.common.role}
		id="player-role"
		panelId="player-role-panel"
	/>
	<div class="search">
		<Input
			bind:value={search}
			type="search"
			aria-label={t.players.search}
			placeholder={t.players.search}
		/>
	</div>
	<ToggleChip pressed={includeInactive} onclick={() => (includeInactive = !includeInactive)}>
		{t.players.showInactive}
	</ToggleChip>
	<span class="count-label" aria-live="polite" aria-atomic="true">
		{loading ? t.common.loading : t.players.resultCount(players.length)}
	</span>
</div>

{#snippet sortHeader(column: SortColumn, label: string)}
	{@const direction = sort?.column === column ? sort.direction : undefined}
	<th scope="col" aria-sort={direction}>
		<button type="button" class="sort-button" onclick={() => sortBy(column)}>
			{label}
			{#if direction}
				<span class="sort-direction" aria-hidden="true"
					>{direction === 'ascending' ? '↑' : '↓'}</span
				>
			{/if}
		</button>
	</th>
{/snippet}

<div
	bind:this={tablePanel}
	class:table-scroll={loading || players.length > 0}
	id="player-role-panel"
	role="tabpanel"
	tabindex="0"
	aria-labelledby="player-role-{role}"
	aria-busy={loading}
>
	{#if !loading && players.length === 0}
		<EmptyState>{t.players.noMatchingPlayers}</EmptyState>
	{:else}
		<table>
			<thead>
				<tr>
					<th scope="col">{t.common.role}</th>
					{@render sortHeader('name', t.players.player)}
					{@render sortHeader('team', t.common.club)}
					{@render sortHeader('quotation', t.common.quotation)}
					<th scope="col">{t.players.status}</th>
				</tr>
			</thead>
			<tbody>
				{#each sortedPlayers as player (player.id)}
					<tr class:inactive={!player.active}>
						<td><span class="role-badge" data-role={player.role}>{player.role}</span></td>
						<td class="player-name">
							{player.name}
							<MantraRoleBadges roles={player.mantra_roles} compact />
						</td>
						<td>{player.team}</td>
						<td class="quotation">{player.quotation ?? '—'}</td>
						<td>{player.active ? t.players.available : t.players.inactive}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>

<style>
	.file-row {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		/* A long file name is cut inside the picker instead of widening the window. */
		min-width: 0;
	}

	.filters {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem;
		margin: 0.75rem 0;
	}

	.search {
		width: min(100%, 16rem);
	}

	.count-label {
		margin-left: auto;
		color: var(--muted);
		font-size: 0.8rem;
		font-variant-numeric: tabular-nums;
	}

	.table-scroll {
		max-height: max(12rem, calc(100dvh - var(--header-height) - 12.75rem));
		overflow: auto;
	}

	table {
		border-collapse: separate;
		border-spacing: 0;
	}

	th {
		position: sticky;
		top: 0;
		z-index: 1;
	}

	.sort-button {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		min-height: 1.5rem;
		padding: 0;
		border: 0;
		background: transparent;
		cursor: pointer;
	}

	.sort-button:hover {
		text-decoration: underline;
	}

	.sort-direction {
		font-size: 0.8em;
	}

	tbody tr.inactive {
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
</style>
