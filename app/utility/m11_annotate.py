"""Overlay M11 validation findings onto rendered M11 protocol HTML.

Takes the rendered protocol HTML from ``USDM4M11.render_current()`` /
``to_html()`` and a list of finding dicts, and returns the HTML with
native ``<details>`` markers injected at each element the findings
reference. No JavaScript — the browser handles the expand/collapse
toggle and keyboard interaction.

Depends on the renderer stamping ``data-m11-element="<name>"`` on each
element wrapper (see
``usdm4_protocol/m11/export/m11_export.py::_parse_elements``). If the
stamp is missing the annotator silently degrades to "everything
unplaced" rather than raising.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.utility.soup import get_soup


@dataclass
class AnnotatedDocument:
    """Output of ``annotate()`` — the annotated HTML plus any findings
    that couldn't be located on the rendered protocol (e.g. findings on
    elements not present in the template). Callers should surface the
    unplaced list so nothing gets silently lost."""

    html: str
    unplaced: list[dict] = field(default_factory=list)
    placed_count: int = 0


# Bootstrap-icon classes keyed by finding severity. Matches the
# compare-view cell decorations in studies/list.html so the two views
# have consistent severity vocabulary.
_SEVERITY_ICON = {
    "error": "bi-x-circle-fill",
    "warning": "bi-exclamation-triangle-fill",
    "info": "bi-info-circle",
}
_SEVERITY_TEXT = {
    "error": "text-danger",
    "warning": "text-warning",
    "info": "text-secondary",
}


def annotate(html: str, findings: list[dict]) -> AnnotatedDocument:
    """Inject a ``<details>`` marker into ``html`` for each finding
    whose element can be located.

    Each marker is a ``<details class="m11-doc-marker severity-X">``
    that sits inside the matching ``[data-m11-element]`` node. The
    ``<summary>`` carries the severity icon (click target); the
    expanded body carries the rule id, message, and expected/actual
    values. Native browser behaviour handles the toggle — no
    JavaScript required on the client.

    Findings whose ``element_name`` doesn't match anything in the
    rendered HTML are returned in ``AnnotatedDocument.unplaced`` so
    the caller can display them separately. Never silently drops a
    finding.
    """
    if not html:
        return AnnotatedDocument(html="", unplaced=list(findings))
    soup = get_soup(html)
    if not soup:
        return AnnotatedDocument(html=html, unplaced=list(findings))

    unplaced: list[dict] = []
    placed = 0

    for index, finding in enumerate(findings):
        element_name = (finding or {}).get("element_name") or ""
        if not element_name:
            unplaced.append(finding)
            continue
        target = soup.find(attrs={"data-m11-element": element_name})
        if target is None:
            unplaced.append(finding)
            continue
        target.append(_build_marker(soup, finding, index))
        placed += 1

    return AnnotatedDocument(html=str(soup), unplaced=unplaced, placed_count=placed)


def _build_marker(soup, finding: dict, index: int):
    """Construct a ``<details>`` marker with a severity-keyed summary
    and the finding body inline. Returns a BeautifulSoup tag ready to
    be appended to the target element. No JS reaches this marker — all
    interactivity is native ``<details>`` behaviour."""
    severity = (finding.get("severity") or "info").lower()
    icon_class = _SEVERITY_ICON.get(severity, _SEVERITY_ICON["info"])
    text_class = _SEVERITY_TEXT.get(severity, _SEVERITY_TEXT["info"])

    marker = soup.new_tag(
        "details",
        attrs={
            "class": f"m11-doc-marker severity-{severity}",
            "data-m11-finding-index": str(index),
        },
    )
    summary = soup.new_tag(
        "summary",
        attrs={
            "class": "m11-doc-marker-summary",
            # Native tooltip carries rule id + message so users see
            # the essence without having to click.
            "title": f"{finding.get('rule_id') or ''}: {finding.get('message') or ''}",
        },
    )
    icon = soup.new_tag("i", attrs={"class": f"bi {icon_class} {text_class}"})
    summary.append(icon)
    marker.append(summary)

    # Expanded body: rule id + message + optional expected/actual.
    # Kept compact so the inline expansion doesn't overwhelm the
    # surrounding rendered-protocol content.
    body = soup.new_tag("div", attrs={"class": "m11-doc-marker-body"})
    header = soup.new_tag("div", attrs={"class": "m11-doc-marker-header"})
    rule_code = soup.new_tag("code", attrs={"class": "m11-doc-marker-rule"})
    rule_code.string = finding.get("rule_id") or ""
    header.append(rule_code)
    body.append(header)

    message_div = soup.new_tag("div", attrs={"class": "m11-doc-marker-message"})
    message_div.string = finding.get("message") or ""
    body.append(message_div)

    expected = finding.get("expected")
    if expected:
        exp = soup.new_tag("div", attrs={"class": "m11-doc-marker-meta"})
        label = soup.new_tag("strong")
        label.string = "Expected: "
        exp.append(label)
        exp.append(str(expected))
        body.append(exp)

    actual = finding.get("actual")
    if actual:
        act = soup.new_tag("div", attrs={"class": "m11-doc-marker-meta"})
        label = soup.new_tag("strong")
        label.string = "Actual: "
        act.append(label)
        act.append(str(actual))
        body.append(act)

    marker.append(body)
    return marker
