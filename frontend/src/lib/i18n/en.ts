export type ErrorParams = Record<string, unknown>;

export const en = {
	common: {
		confirm: 'Confirm',
		cancel: 'Cancel',
		close: 'Close',
		chooseFile: 'Choose a file',
		chooseFilePrompt: 'Choose file…',
		scrollLeft: 'Scroll left',
		scrollRight: 'Scroll right',
		mantraSubRoles: 'Mantra sub-roles',
		all: 'All',
		maximumPrice: 'Maximum price',
		dismissNotification: 'Dismiss notification',
		updateAvailable: 'Update available:',
		currentVersion: (version: string) => `(you are using ${version})`,
		download: 'Download',
		dismissUpdate: 'Dismiss update notification'
	},
	roles: {
		P: 'Goalkeepers',
		D: 'Defenders',
		C: 'Midfielders',
		A: 'Forwards'
	},
	navigation: {
		home: 'Home',
		playerList: 'Player list',
		strategies: 'Strategies',
		auctions: 'Auctions',
		mainNavigation: 'Main navigation',
		language: 'Language',
		switchToDarkTheme: 'Switch to dark theme',
		switchToLightTheme: 'Switch to light theme',
		darkTheme: 'Dark theme',
		lightTheme: 'Light theme',
		appDescription: 'A local assistant for preparing and following Classic fantacalcio auctions.'
	},
	shortcuts: {
		title: 'Keyboard shortcuts',
		showShortcuts: 'Show keyboard shortcuts',
		general: 'General',
		or: 'or',
		returnKey: 'return',
		enterKey: 'Enter',
		spaceKey: 'Space'
	},
	home: {},
	players: {},
	strategies: {},
	auctions: {},
	auction: {},
	errors: {
		unexpected: 'An unexpected error occurred.',

		auction_not_found: 'Auction not found.',
		participant_not_found: 'Participant not found.',
		player_not_found: 'Player not found.',
		purchase_not_found: 'Purchase not found.',
		strategy_not_found: 'Strategy not found.',
		tier_not_found: 'Tier not found.',

		unsupported_player_file: 'Choose an .xlsx or .csv file.',
		invalid_excel_file: 'The Excel file cannot be read.',
		missing_tutti_sheet: 'The Excel file has no “Tutti” sheet.',
		csv_not_utf8: 'The CSV file must be saved with UTF-8 encoding.',
		missing_player_columns: 'The file must have the columns Id, R, Nome and Squadra.',
		incomplete_player_row: 'Every row of the file must have Id, R, Nome and Squadra filled in.',
		empty_player_list: 'The file does not contain any players.',
		duplicate_player_ids: 'Some players in the file share the same Id.',
		invalid_quotation: 'Quotations must be whole numbers, zero or higher.',
		unsupported_role: ({ role }: ErrorParams) =>
			`The role “${role}” is not valid: use P, D, C or A.`,

		unsupported_tier_file: 'Choose a .csv file.',
		missing_tier_columns: 'The file must have the columns Nome, Fascia, MaxPrezzo% and Note.',
		missing_player_name: 'Every row of the file must have a name in the Nome column.',
		empty_tier_list: 'The file does not contain any players.',
		max_price_not_number: 'The maximum price (MaxPrezzo%) must be a number.',
		invalid_tier_color: 'The Colore column must contain colour codes like #ef4444.',

		strategy_name_required: 'Enter a name for the strategy.',
		strategy_name_taken: ({ name }: ErrorParams) => `A strategy named “${name}” already exists.`,
		strategy_without_players: 'A strategy without players cannot be exported.',
		tier_name_required: 'Enter a name for the tier.',
		tier_name_taken: 'The strategy already has a tier with this name.',
		invalid_tier_order: 'The order must include every tier exactly once.',
		max_price_out_of_range: 'The maximum price must be greater than 0% and at most 100%.',
		max_price_too_precise: 'The maximum price can have only one decimal place.',

		auction_name_required: 'Enter a name for the auction.',
		insufficient_initial_credits: 'The credits are not enough to fill every slot of the squad.',
		negative_roster_slots: 'The number of slots for a role cannot be negative.',
		empty_roster: 'A squad must have at least one slot.',
		participant_name_required: 'Enter a name for every participant.',
		participant_name_taken: 'Two participants cannot have the same name.',
		participants_required: 'The auction needs at least one participant.',
		auction_not_draft: 'The auction has already started.',
		auction_not_live: 'The auction is not in progress.',
		auction_not_completed: 'The auction has not ended yet.',

		player_already_purchased: 'This player has already been bought.',
		player_inactive: 'This player is inactive and cannot be bought.',
		invalid_price: 'The price must be a whole number of at least 1.',
		role_slots_full: 'This participant has no free slots for this role.',
		bid_exceeds_maximum: "The price is higher than the participant's maximum bid.",

		player_fields_required: 'Every player needs an id, a name and a club.'
	}
};

export type Messages = typeof en;
