/**
 * Ruoli Mantra: sotto-posizioni più specifiche del ruolo Classic (es. "centrale" o "terzino"
 * per un difensore), lette dalla colonna opzionale RM del listone ufficiale fantacalcio.it.
 * Qui vengono solo tradotte in sigle più leggibili per la UI: l'app non supporta l'asta Mantra.
 */

/** Sigla ufficiale del file RM -> sigla mostrata nell'interfaccia. */
export const MANTRA_ROLE_LABELS: Record<string, string> = {
	Por: 'Por',
	Dc: 'Dc',
	Dd: 'Td',
	Ds: 'Ts',
	B: 'Br',
	E: 'E',
	M: 'Cdc',
	C: 'Cc',
	W: 'Ala',
	T: 'Coc',
	Pc: 'Pc',
	A: 'Sp'
};

/** Ordine canonico dei codici ufficiali, usato per un ordinamento stabile dei badge/chip. */
const MANTRA_ROLE_ORDER = Object.keys(MANTRA_ROLE_LABELS);

export function mantraRoleLabel(code: string): string {
	return MANTRA_ROLE_LABELS[code] ?? code;
}

export function sortMantraRoles(codes: string[]): string[] {
	return [...codes].sort((first, second) => {
		const firstIndex = MANTRA_ROLE_ORDER.indexOf(first);
		const secondIndex = MANTRA_ROLE_ORDER.indexOf(second);
		return (
			(firstIndex === -1 ? MANTRA_ROLE_ORDER.length : firstIndex) -
			(secondIndex === -1 ? MANTRA_ROLE_ORDER.length : secondIndex)
		);
	});
}
