import type { Messages } from './en';

export const it: Messages = {
	common: {
		confirm: 'Conferma',
		cancel: 'Annulla',
		close: 'Chiudi',
		chooseFile: 'Scegli un file',
		chooseFilePrompt: 'Scegli file…',
		scrollLeft: 'Scorri a sinistra',
		scrollRight: 'Scorri a destra',
		mantraSubRoles: 'Sotto-ruoli Mantra',
		all: 'Tutti',
		maximumPrice: 'Prezzo massimo',
		dismissNotification: 'Chiudi notifica',
		updateAvailable: 'È disponibile',
		currentVersion: (version) => `(stai usando la ${version})`,
		download: 'Scarica',
		dismissUpdate: 'Nascondi avviso di aggiornamento'
	},
	roles: {
		P: 'Portieri',
		D: 'Difensori',
		C: 'Centrocampisti',
		A: 'Attaccanti'
	},
	navigation: {
		home: 'Home',
		playerList: 'Listone',
		strategies: 'Strategie',
		auctions: 'Aste',
		mainNavigation: 'Navigazione principale',
		language: 'Lingua',
		switchToDarkTheme: 'Attiva tema scuro',
		switchToLightTheme: 'Attiva tema chiaro',
		darkTheme: 'Tema scuro',
		lightTheme: 'Tema chiaro',
		appDescription: 'Assistente locale per preparare e seguire le aste Classic del fantacalcio.'
	},
	shortcuts: {
		title: 'Scorciatoie da tastiera',
		showShortcuts: 'Mostra le scorciatoie',
		general: 'Generali',
		or: 'o',
		returnKey: 'invio',
		enterKey: 'Invio',
		spaceKey: 'Spazio'
	},
	home: {},
	players: {},
	strategies: {},
	auctions: {},
	auction: {},
	errors: {
		unexpected: 'Si è verificato un errore inatteso.',

		auction_not_found: 'Asta non trovata.',
		participant_not_found: 'Partecipante non trovato.',
		player_not_found: 'Calciatore non trovato.',
		purchase_not_found: 'Acquisto non trovato.',
		strategy_not_found: 'Strategia non trovata.',
		tier_not_found: 'Fascia non trovata.',

		unsupported_player_file: 'Scegli un file .xlsx o .csv.',
		invalid_excel_file: 'Impossibile leggere il file Excel.',
		missing_tutti_sheet: 'Nel file Excel manca il foglio “Tutti”.',
		csv_not_utf8: 'Il file CSV deve essere salvato con la codifica UTF-8.',
		missing_player_columns: 'Il file deve avere le colonne Id, R, Nome e Squadra.',
		incomplete_player_row: 'Ogni riga del file deve avere Id, R, Nome e Squadra compilati.',
		empty_player_list: 'Il file non contiene calciatori.',
		duplicate_player_ids: 'Alcuni calciatori del file hanno lo stesso Id.',
		invalid_quotation: 'Le quotazioni devono essere numeri interi, da zero in su.',
		unsupported_role: ({ role }) => `Il ruolo “${role}” non è valido: usa P, D, C o A.`,

		unsupported_tier_file: 'Scegli un file .csv.',
		missing_tier_columns: 'Il file deve avere le colonne Nome, Fascia, MaxPrezzo% e Note.',
		missing_player_name: 'Ogni riga del file deve avere un nome nella colonna Nome.',
		empty_tier_list: 'Il file non contiene calciatori.',
		max_price_not_number: 'Il prezzo massimo (MaxPrezzo%) deve essere un numero.',
		invalid_tier_color: 'La colonna Colore deve contenere codici colore come #ef4444.',

		strategy_name_required: 'Inserisci un nome per la strategia.',
		strategy_name_taken: ({ name }) => `Esiste già una strategia di nome “${name}”.`,
		strategy_without_players: 'Una strategia senza calciatori non può essere esportata.',
		tier_name_required: 'Inserisci un nome per la fascia.',
		tier_name_taken: 'La strategia ha già una fascia con questo nome.',
		invalid_tier_order: "L'ordine deve comprendere ogni fascia una sola volta.",
		max_price_out_of_range: 'Il prezzo massimo deve essere maggiore di 0% e non superare il 100%.',
		max_price_too_precise: 'Il prezzo massimo può avere un solo decimale.',

		auction_name_required: "Inserisci un nome per l'asta.",
		insufficient_initial_credits: 'I crediti non bastano a riempire tutti i posti della rosa.',
		negative_roster_slots: 'Il numero di posti per un ruolo non può essere negativo.',
		empty_roster: 'Una rosa deve avere almeno un posto.',
		participant_name_required: 'Inserisci un nome per ogni partecipante.',
		participant_name_taken: 'Due partecipanti non possono avere lo stesso nome.',
		participants_required: "L'asta deve avere almeno un partecipante.",
		auction_not_draft: "L'asta è già iniziata.",
		auction_not_live: "L'asta non è in corso.",
		auction_not_completed: "L'asta non è ancora terminata.",

		player_already_purchased: 'Questo calciatore è già stato acquistato.',
		player_inactive: 'Questo calciatore è inattivo e non può essere acquistato.',
		invalid_price: 'Il prezzo deve essere un numero intero, almeno 1.',
		role_slots_full: 'Il partecipante non ha più posti liberi per questo ruolo.',
		bid_exceeds_maximum: 'Il prezzo supera la puntata massima del partecipante.',

		player_fields_required: 'Ogni calciatore deve avere id, nome e squadra.'
	}
};
