#!/usr/bin/env python3
"""Populate a running single-user Study Definitions Workbench via HTTP.

No browser, no Playwright. Each file is POSTed straight to its import
endpoint (the same multipart ``files`` field the web form submits), then
the script polls ``/import/status/data`` until the background import
finishes.

Why poll: ``execute_import`` runs the actual parse in a background thread
(see ``app/imports/import_manager.py``), so the POST returns "upload
successful" the instant the file is saved — not when the import
completes. The DB status flips to ``Success`` / ``Failed`` / ``Exception``
when the thread is done; that's what we wait on.

Single-user only: ``protect_endpoint`` auto-provisions the session when
``SINGLE_USER`` is set, so no login is needed. Against a multi-user
server every request redirects to /login and the uploads are rejected.

Assumes a fresh/empty import history (an "init"): completion is matched
by filename, so a pre-existing row for the same filename would be read
as this run's result.

Usage (from the repo root):

    python -m scripts.site_populate_http
    python -m scripts.site_populate_http --url http://localhost:8000
    python -m scripts.site_populate_http --timeout 240
"""

import argparse
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (POST endpoint, file path relative to repo root), in load order.
FILES = [
    ("/import/m11", "tests/test_files/m11/WA42380/WA42380.docx"),
    ("/import/m11", "tests/test_files/m11/ASP8062/ASP8062.docx"),
    ("/import/m11", "tests/test_files/m11/RadVax/RadVax.docx"),
    ("/import/m11", "tests/test_files/m11/LZZT/LZZT.docx"),
    ("/import/fhir?version=prism3", "tests/test_files/fhir_v3/from/IGBJ_fhir_m11.json"),
    ("/import/fhir?version=prism3", "tests/test_files/fhir_v3/from/WA42380_fhir_m11.json"),
    ("/import/fhir?version=prism3", "tests/test_files/fhir_v3/from/ASP8062_fhir_m11.json"),
    ("/import/fhir?version=prism3", "tests/test_files/fhir_v3/from/DEUCRALIP_fhir_m11.json"),
    ("/import/xl", "tests/test_files/excel/pilot.xlsx"),
]

TERMINAL_OK = "Success"
TERMINAL = {"Success", "Failed", "Exception"}

_ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
# Only matches <td> cells with plain text (no nested tags): the first four
# columns are Type, Imported At, File Name, Status. The Errors / Validation
# columns hold anchors and are skipped.
_CELL_RE = re.compile(r"<td>([^<]*)</td>")


def _multipart_body(filename, content):
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    body = b"".join(
        [
            b"--",
            boundary.encode(),
            b"\r\n",
            b'Content-Disposition: form-data; name="files"; filename="',
            filename.encode(),
            b'"\r\n',
            b"Content-Type: ",
            ctype.encode(),
            b"\r\n\r\n",
            content,
            b"\r\n",
            b"--",
            boundary.encode(),
            b"--\r\n",
        ]
    )
    return boundary, body


def post_file(base_url, endpoint, filepath):
    """POST one file. Returns on acceptance, raises on rejection."""
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as handle:
        content = handle.read()
    boundary, body = _multipart_body(filename, content)
    req = urllib.request.Request(
        base_url + endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", "replace")
    if "alert-success" not in html:
        hint = ""
        if "login" in html.lower() or "register" in html.lower():
            hint = " (server looks like it's NOT in single-user mode — uploads need SINGLE_USER set)"
        raise RuntimeError(f"upload rejected{hint}")
    return filename


def latest_status(base_url, filename):
    """Status of the most recent import row for ``filename`` (or None)."""
    url = base_url + "/import/status/data?page=1&size=500"
    with urllib.request.urlopen(url, timeout=30) as resp:
        html = resp.read().decode("utf-8", "replace")
    status = None
    for row in _ROW_RE.findall(html):
        cells = _CELL_RE.findall(row)  # [type, created, filename, status]
        if len(cells) >= 4 and cells[2].strip() == filename:
            status = cells[3].strip()  # rows are ascending; keep the last match
    return status


def wait_for_completion(base_url, filename, timeout, poll=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = latest_status(base_url, filename)
        if status in TERMINAL:
            return status
        time.sleep(poll)
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--url",
        default=os.environ.get("SDW_URL", "http://localhost:8000"),
        help="Base URL of the running site (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Per-file import timeout in seconds (default: 180)",
    )
    args = parser.parse_args(argv)
    base = args.url.rstrip("/")

    print(f"Populating {base} ({len(FILES)} files)\n")
    failures = []
    for endpoint, rel in FILES:
        path = os.path.join(REPO_ROOT, rel)
        name = os.path.basename(path)
        if not os.path.exists(path):
            print(f"  SKIP   {name} — file not found ({rel})")
            failures.append(name)
            continue
        print(f"  POST   {name} -> {endpoint} ... ", end="", flush=True)
        try:
            post_file(base, endpoint, path)
        except urllib.error.URLError as exc:
            print(f"FAILED ({exc.reason}); is the server up at {base}?")
            failures.append(name)
            continue
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(f"FAILED ({exc})")
            failures.append(name)
            continue

        status = wait_for_completion(base, name, args.timeout)
        if status == TERMINAL_OK:
            print("Success")
        elif status is None:
            print(f"TIMEOUT after {args.timeout}s")
            failures.append(name)
        else:
            print(status)
            failures.append(name)

    print()
    if failures:
        print(f"Finished with {len(failures)} problem(s): {', '.join(failures)}")
        return 1
    print(f"Done. {len(FILES)} files imported successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
