<script lang="ts">
	import { resolve } from '$app/paths';
</script>

<svelte:head>
	<title>Home | Asta la Vista</title>
</svelte:head>

<section class="page-heading">
	<p class="eyebrow">Assistente per l'asta</p>
	<h1>Tutto quello che serve, mentre l'asta è in corso.</h1>
	<p>
		Gestisci il listone, prepara le tue fasce e controlla crediti, slot e rose senza perdere di
		vista le chiamate.
	</p>
</section>

<section class="feature-grid" aria-label="Sezioni principali">
	<a class="feature-card" href={resolve('/listone')}>
		<span>01</span>
		<h2>Listone</h2>
		<p>Importa i calciatori e tieni aggiornati ruolo, squadra e disponibilità.</p>
	</a>
	<a class="feature-card" href={resolve('/strategie')}>
		<span>02</span>
		<h2>Strategie</h2>
		<p>Organizza i calciatori in fasce riutilizzabili, separate per ruolo.</p>
	</a>
	<a class="feature-card" href={resolve('/aste')}>
		<span>03</span>
		<h2>Aste</h2>
		<p>Crea un'asta e segui in tempo reale acquisti, crediti e slot rimasti.</p>
	</a>
</section>
