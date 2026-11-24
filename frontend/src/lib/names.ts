/** The longest name that is never cut: it stays whole while what is next to it gives way. */
const SHORT_NAME_LENGTH = 8;

/**
 * The class that keeps a name readable next to `.name-line` or `.name-lines` (see `app.css`): a
 * long name keeps a minimum width, a short one keeps all of its width, so it is never padded.
 */
export function nameFit(name: string): 'name-min' | 'name-keep' {
	return name.length > SHORT_NAME_LENGTH ? 'name-min' : 'name-keep';
}
