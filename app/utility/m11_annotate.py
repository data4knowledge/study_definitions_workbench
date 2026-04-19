"""Overlay M11 validation findings onto rendered M11 protocol HTML.

Takes the rendered protocol HTML from ``USDM4M11.render_current()`` /
``to_html()`` and a list of finding dicts, and returns the HTML with
severity markers injected at each element the findings reference.
Each marker carries a ``data-m11-finding-index`` so client-side JS can
map a marker click back to the finding for the side-panel reveal.

Depends on the renderer stamping ``data-m11-element="<name>"`` on each
element wrapper. That happens in
``usdm4_protocol/m11/export/m11_export.py::_parse_elements`` — if
anything breaks the stamp, this annotator silently degrades to
"everything unplaced" rather than raising.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.utility.soup import get_soup


@dataclass
class AnnotatedDocument:
    """Output of ``annotate()`` — the annotated HTML plus any findings
    that couldn't be located on the rendered protocol (e.g. findings on
    elements not present in the template, or orphaned sentinel
    findings). Callers should surface the unplaced list so nothing gets
    silently lost."""

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
    """Inject severity markers into ``html`` for each finding that can
    be located.

    Markers are added as small ``<span>`` badges inside the matching
    ``[data-m11-element]`` node, not before or after — staying inside
    means they travel with the element if the document is restyled or
    moved. Each marker carries ``data-m11-finding-index`` as a 0-based
    pointer into the original ``findings`` list so client-side JS can
    retrieve the full finding for the side panel without needing the
    whole finding inline in the DOM.

    Findings whose ``element_name`` doesn't match anything in the
    rendered HTML are returned in ``AnnotatedDocument.unplaced`` so the
    caller can display them separately. Never silently drops a finding.
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
        # Use find (first match) because the renderer stamps the parent
        # container — usually a div/td with a single element replacement.
        # Multiple matches shouldn't happen for a well-formed template;
        # if they do, we annotate the first to avoid duplicate markers
        # and leave the others alone.
        target = soup.find(attrs={"data-m11-element": element_name})
        if target is None:
            unplaced.append(finding)
            continue
        target.append(_build_marker(soup, finding, index))
        placed += 1

    return AnnotatedDocument(html=str(soup), unplaced=unplaced, placed_count=placed)


def _build_marker(soup, finding: dict, index: int):
    """Construct a single marker tag that carries enough classes for
    CSS styling and enough data for JS to retrieve the finding. Returns
    a BeautifulSoup tag ready to be appended to the target element.
    """
    severity = (finding.get("severity") or "info").lower()
    icon_class = _SEVERITY_ICON.get(severity, _SEVERITY_ICON["info"])
    text_class = _SEVERITY_TEXT.get(severity, _SEVERITY_TEXT["info"])

    marker = soup.new_tag(
        "span",
        attrs={
            "class": f"m11-doc-marker severity-{severity}",
            "role": "button",
            "tabindex": "0",
            "data-m11-finding-index": str(index),
            # Native tooltip as a fallback if the side-panel JS fails
            # to initialise — at least the user still sees the rule id.
            "title": f"{finding.get('rule_id') or ''}: {finding.get('message') or ''}",
        },
    )
    icon = soup.new_tag("i", attrs={"class": f"bi {icon_class} {text_class}"})
    marker.append(icon)
    return marker
