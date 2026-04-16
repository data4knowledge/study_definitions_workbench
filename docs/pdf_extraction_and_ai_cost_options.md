# PDF Extraction and AI Cost — Deployment Options

Status: exploratory — captures thinking in progress, not a decision.

Two separable deployment concerns surfaced while looking at SDW on fly.io:

1. Docker image size. Docling is the best PDF extractor currently available for the M11 and legacy protocol documents, but its ML model bundle (torch, transformers, easyocr, docling-native models) pushes the image into the multi-GB range.
2. AI cost exposure. With Claude / Gemini wired into `usdm4_protocol`, a user uploading many large protocols could run up significant API charges against the platform account.

Both need to be solved before SDW is comfortable to deploy publicly on fly.

## Image size — options to reduce the docling footprint

### Option A — shrink docling in place

Keep docling, but strip the avoidable weight around it.

- `python:3.12-slim` (or `-bookworm-slim`) as base rather than the default.
- Multi-stage Dockerfile: build wheels in a builder stage, copy only `/usr/local/lib/python3.12/site-packages` into the runtime stage. Leaves build toolchains behind.
- Install `torch` from the CPU-only wheel index (`--index-url https://download.pytorch.org/whl/cpu`). This alone typically saves ~1.5 GB versus the default CUDA-bundled wheel.
- `pip install --no-cache-dir` throughout.
- Do not pre-download docling's models at build time. Let them lazy-download on first use into a persistent fly volume (`/data/docling-models` or similar). First import per machine is slow; subsequent imports are fast.

Expected outcome: multi-GB → ~1–1.5 GB image, with first-run model download hitting the volume.

This is the cheapest option to try and the least disruptive to the rest of the stack. It should be measured before any of the more invasive options are considered.

### Option B — PyMuPDF-only in production

PyMuPDF is already supported by `LoadPDF` and by the `populate_corpus.py` pipeline (207 protocols in the efficacy corpus use it). The extraction quality envelope is known and documented in `usdm4_protocol/CLAUDE.md`:

- Strips superscript formatting inside tables (footnote markers in SoA cells become plain text) — mitigated by the plain-text reference fallback in `cell_references()`.
- Can truncate long multi-page tables (NCT02107703, NCT04677179 are known cases).
- Two-column SoA layouts where cells[0] holds category labels are not handled.

For users importing well-behaved M11 DOCX protocols (the majority of SDW traffic), PyMuPDF-only has essentially no downside because the M11 path doesn't touch docling. For users importing legacy PDF protocols, quality would drop on the known edge cases but basic extraction would still work.

Image size with PyMuPDF-only: a few hundred MB.

### Option C — split into web + worker tiers

Slim UI/web service (no docling), fat worker service (with docling) behind a job queue. Imports become async — the UI submits a job and polls for completion. The web service stays small; only the worker carries the weight, and fly machine sizing matches the workload.

More moving parts (queue, worker orchestration, job state), more fly machines to manage, and the UI needs async import status rendering that doesn't exist today. Worth considering only if Options A and B together are insufficient.

### Recommendation — try A first, measure, revisit

Option A is reversible and measurable in a day. The answer to "is docling-in-production viable" hinges on the post-A image size and the fly volume mount working cleanly.

## AI cost — options to contain exposure

The real risk is a single user uploading many protocols and billing the platform's API key. Levers, ordered from highest-impact to lowest:

### BYOK (bring your own key)

Users supply their own Anthropic / Gemini API keys via SDW account settings. Keys are stored encrypted at rest and injected into `ExtractStudy._init_providers` per-request. Zero platform API cost; users see their own bill.

Wiring touch points:
- User settings schema: `anthropic_api_key`, `gemini_api_key` (both optional, both encrypted).
- Settings UI for key entry.
- Request context carries the current user's keys through to the import job.
- `ClaudeProvider.__init__` needs to accept an explicit API key rather than reading only from `ServiceEnvironment()`. Same for `GeminiProvider`.
- The Option B gate (`claude.available`) already handles the "no key" case cleanly — falls back to simple regex path. BYOK with no key set = simple path only = free.

This is probably the single most effective change. It lets the platform stay free to users while still offering AI extraction to users who opt in.

### Extraction cache on a fly volume

`common/ai/extraction_cache.py` is content-addressed by SHA-256 of `(prompt, system_message, model, temperature)`. Mount a fly volume at `EXTRACTION_CACHE_DIR` and every re-import of the same protocol costs $0 after the first pass. Large win for demo and development usage patterns where the same files get processed repeatedly.

Cost-free to enable; needs a persistent volume which fly already provides.

### Tiered AI usage

Free tier: simple regex + heuristic paths only (already the Option B fallback).
Paid / BYOK tier: AI enabled.

With the Option B fix in place this is a single flag — `use_ai=False` at the pipeline entry point gets the simple path end-to-end.

### Pin to Haiku only in deployment

Sonnet is used today for legacy title page extraction and vision SoA (`ClaudeProvider.SONNET_MODEL`). Haiku is ~5–10× cheaper. Quality on those tasks would drop and should be measured on the efficacy corpus before committing, but a Haiku-only deployment would materially reduce per-import cost on legacy PDFs.

### Per-user rate / usage limits

Enforce at the SDW application layer: N imports/day, M MB/file, K total AI calls/month. Straightforward to add; primarily a safety net behind BYOK.

### Self-hosted small model as a first pass

A Llama/Mistral-class model via Ollama or vLLM for bulk classification tasks (SoA row classification, simple criterion detection), falling back to Claude only for the highest-quality steps. Materially reduces Claude volume but adds a self-hosted inference stack to the deployment. Probably not worth the complexity until BYOK + cache + Haiku-only prove insufficient.

### Recommendation — BYOK + cache is the minimum viable combination

BYOK removes the cost exposure entirely. The extraction cache removes duplicate-work cost on top of BYOK. Everything else (tiering, Haiku-only, rate limits, self-hosted) is a refinement on top of that foundation.

## Open questions

- What does the post-Option-A image size actually come out as? Must measure.
- Is the fly volume performance acceptable for first-import model lazy-download? Usually yes, needs verification.
- What's the user UX for entering and managing API keys? Per-user settings page, or deployment-wide key with per-user quota tracking?
- Is there appetite for per-user billing (track Claude spend per user, show cost in the UI), or is BYOK-only simpler to operate?
