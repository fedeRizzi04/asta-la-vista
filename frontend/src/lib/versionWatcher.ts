import { getVersion, type AppVersion } from './system';

/**
 * The server waits for GitHub only briefly: when GitHub is slow, or the app started offline, the
 * first answer has no update information and the check goes on in the background. These timings
 * make sure a release found later still reaches the page.
 */
// Long enough for the server's background check (up to ~5 seconds) to have finished.
export const RETRY_DELAY_MS = 8_000;
export const RECHECK_INTERVAL_MS = 15 * 60_000;
// Coming back to the tab often should not mean a request every time.
const MIN_GAP_MS = 60_000;

/** Fetch the version now and keep it fresh; returns a function that stops watching. */
export function watchVersion(onVersion: (version: AppVersion) => void): () => void {
	let lastRequestAt = 0;
	let retryTimer: ReturnType<typeof setTimeout> | undefined;
	let stopped = false;

	function refresh(isRetry = false): void {
		lastRequestAt = Date.now();
		clearTimeout(retryTimer);
		getVersion()
			.then((version) => {
				// A request still in flight when watching stops must not report or schedule anything.
				if (stopped) return;
				onVersion(version);
				// No answer from GitHub yet: ask once more, when the server should have one.
				if (version.latest_version === null && !isRetry) {
					retryTimer = setTimeout(() => refresh(true), RETRY_DELAY_MS);
				}
			})
			.catch(() => {
				// The version is informative only: a failure must not disturb the page.
			});
	}

	function refreshIfVisibleAndStale(): void {
		if (document.visibilityState === 'visible' && Date.now() - lastRequestAt >= MIN_GAP_MS) {
			refresh();
		}
	}

	const onOnline = (): void => refresh();
	refresh();
	const interval = setInterval(refreshIfVisibleAndStale, RECHECK_INTERVAL_MS);
	document.addEventListener('visibilitychange', refreshIfVisibleAndStale);
	window.addEventListener('online', onOnline);

	return () => {
		stopped = true;
		clearTimeout(retryTimer);
		clearInterval(interval);
		document.removeEventListener('visibilitychange', refreshIfVisibleAndStale);
		window.removeEventListener('online', onOnline);
	};
}
