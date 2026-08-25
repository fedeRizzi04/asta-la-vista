<script lang="ts">
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import {
		createStrategy,
		duplicateStrategy,
		getStrategies,
		type StrategySummary
	} from '$lib/strategies';

	let strategies = $state<StrategySummary[]>([]);
	let newStrategyName = $state('');
	let loading = $state(true);
	let saving = $state(false);
	let error = $state('');

	onMount(loadStrategies);

	async function loadStrategies(): Promise<void> {
		loading = true;
		error = '';
		try {
			strategies = await getStrategies();
		} catch (caught) {
			error = errorMessage(caught);
		} finally {
			loading = false;
		}
	}

	async function submitStrategy(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		const name = newStrategyName.trim();
		if (!name) return;
		saving = true;
		error = '';
		try {
			await createStrategy(name);
			newStrategyName = '';
			await loadStrategies();
		} catch (caught) {
			error = errorMessage(caught);
		} finally {
			saving = false;
		}
	}

	async function duplicate(strategy: StrategySummary): Promise<void> {
		const name = window.prompt('Nome della nuova strategia', `${strategy.name} - copia`)?.trim();
		if (!name) return;
		saving = true;
		error = '';
		try {
			await duplicateStrategy(strategy.id, name);
			await loadStrategies();
		} catch (caught) {
			error = errorMessage(caught);
		} finally {
			saving = false;
		}
	}

	function errorMessage(caught: unknown): string {
		return caught instanceof Error ? caught.message : 'Si è verificato un errore inatteso.';
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

{#if error}
	<div class="message" role="alert">{error}</div>
{/if}

<section class="strategy-section" aria-live="polite" aria-busy={loading}>
	<div class="section-heading">
		<h2>Le tue strategie</h2>
		<span>{loading ? 'Caricamento…' : `${strategies.length} strategie`}</span>
	</div>

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
							onclick={() => duplicate(strategy)}
							disabled={saving}
						>
							Duplica
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
		border: 1px solid #d9ddd7;
		border-radius: 0.65rem;
		background: #fafbf8;
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
		border: 1px solid #bdc5bf;
		border-radius: 0.4rem;
		font: inherit;
	}

	button,
	.actions a {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 2.55rem;
		padding: 0 1rem;
		border: 1px solid #204c39;
		border-radius: 0.45rem;
		background: #204c39;
		color: #fff;
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
		border-color: #bdc5bf;
		background: transparent;
		color: #344039;
	}

	.message {
		margin-top: 1.5rem;
		padding: 0.85rem 1rem;
		border: 1px solid #d4a7a7;
		border-radius: 0.5rem;
		background: #fff7f7;
		color: #7a2727;
		font-size: 0.9rem;
	}

	.strategy-section {
		margin-top: 3rem;
	}

	.section-heading {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 0.8rem;
	}

	.section-heading h2 {
		margin: 0;
		font-size: 1.15rem;
	}

	.section-heading span {
		color: #667069;
		font-size: 0.8rem;
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
		border: 1px solid #d9ddd7;
		border-radius: 0.65rem;
		background: #fafbf8;
	}

	article h3 {
		margin: 0;
		font-size: 1rem;
	}

	article p {
		margin: 0.4rem 0 0;
		color: #667069;
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
