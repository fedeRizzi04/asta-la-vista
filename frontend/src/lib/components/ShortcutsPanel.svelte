<script lang="ts">
	import { SvelteMap } from 'svelte/reactivity';
	import { t } from '$lib/i18n';
	import { getShortcuts, shortcutKeys, shortcutsPanel } from '$lib/shortcuts.svelte';
	import Dialog from './ui/Dialog.svelte';
	import Kbd from './ui/Kbd.svelte';

	type Row = { description: string; keys: string[] };

	/** One row per action: shortcuts sharing a description (e.g. ⌘K and /) are listed together. */
	const groups = $derived.by(() => {
		const groups = new SvelteMap<string | undefined, Row[]>();
		for (const shortcut of getShortcuts()) {
			const rows = groups.get(shortcut.group) ?? [];
			const row = rows.find(({ description }) => description === shortcut.description);
			if (row) row.keys.push(shortcut.keys);
			else rows.push({ description: shortcut.description, keys: [shortcut.keys] });
			groups.set(shortcut.group, rows);
		}
		return groups;
	});
</script>

<Dialog bind:open={shortcutsPanel.open} title={t.shortcuts.title} closeLabel={t.common.close}>
	{#each groups as [group, rows] (group)}
		<div>
			{#if group}<h3>{group}</h3>{/if}
			<ul role="list">
				{#each rows as row (row.description)}
					<li>
						<span>{row.description}</span>
						<span class="keys">
							{#each row.keys as spec, index (spec)}
								{#if index > 0}<span class="or">{t.shortcuts.or}</span>{/if}
								<span class="keys">
									{#each shortcutKeys(spec) as key (key)}
										<Kbd>{key}</Kbd>
									{/each}
								</span>
							{/each}
						</span>
					</li>
				{/each}
			</ul>
		</div>
	{/each}
</Dialog>

<style>
	h3 {
		margin: 0 0 0.4rem;
		font-size: 0.9rem;
	}

	ul {
		display: grid;
		gap: 0.4rem;
		margin: 0;
		padding: 0;
		list-style: none;
	}

	li {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.75rem;
	}

	.keys {
		display: flex;
		align-items: center;
		gap: 0.2rem;
	}

	.or {
		margin: 0 0.25rem;
		color: var(--muted);
		font-size: 0.8rem;
	}
</style>
