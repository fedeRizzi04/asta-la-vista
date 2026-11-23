<script lang="ts">
	import { SvelteMap } from 'svelte/reactivity';
	import { getShortcuts, shortcutKeys, shortcutsPanel, type Shortcut } from '$lib/shortcuts.svelte';
	import Dialog from './ui/Dialog.svelte';
	import Kbd from './ui/Kbd.svelte';

	const groups = $derived.by(() => {
		const groups = new SvelteMap<string | undefined, Shortcut[]>();
		for (const shortcut of getShortcuts()) {
			const group = groups.get(shortcut.group);
			if (group) group.push(shortcut);
			else groups.set(shortcut.group, [shortcut]);
		}
		return groups;
	});
</script>

<Dialog bind:open={shortcutsPanel.open} title="Scorciatoie da tastiera" closeLabel="Chiudi">
	{#each groups as [group, shortcuts] (group)}
		<div>
			{#if group}<h3>{group}</h3>{/if}
			<ul role="list">
				{#each shortcuts as shortcut (shortcut.keys)}
					<li>
						<span>{shortcut.description}</span>
						<span class="keys">
							{#each shortcutKeys(shortcut.keys) as key (key)}
								<Kbd>{key}</Kbd>
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
		gap: 0.2rem;
	}
</style>
