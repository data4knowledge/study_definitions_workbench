// Intentionally empty.
//
// Findings downloads moved server-side; the results page now posts a
// plain HTML form to /validate/download/{csv,json,md,xlsx}. This file
// is kept only to avoid 404s from any stale <script src="…"> that may
// be cached in a long-running browser session. Safe to delete once
// you've confirmed no page references it.
