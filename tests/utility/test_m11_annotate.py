"""Tests for ``app.utility.m11_annotate``.

The annotator overlays findings onto rendered M11 protocol HTML by
finding elements via the ``data-m11-element`` attribute that the
renderer stamps on each element wrapper. These tests verify:

- Markers are injected inside the matching element (so severity can
  be located in context).
- Each marker carries a ``data-m11-finding-index`` pointer back to the
  original findings list.
- Findings whose element has no match in the rendered HTML are not
  silently lost — they're returned via ``unplaced``.
- Severity drives the icon class (error/warning/info each distinct).
"""

from app.utility.m11_annotate import AnnotatedDocument, annotate


def _finding(
    element: str = "Full Title",
    severity: str = "error",
    rule: str = "M11_001",
    message: str = "Required element missing.",
) -> dict:
    return {
        "rule_id": rule,
        "severity": severity,
        "status": "Failed",
        "message": message,
        "expected": "Text",
        "actual": "(no value)",
        "element_name": element,
        "section_number": "",
        "section_title": "Title Page",
    }


class TestAnnotate:
    def test_empty_inputs_return_empty_document(self):
        result = annotate("", [])
        assert isinstance(result, AnnotatedDocument)
        assert result.html == ""
        assert result.unplaced == []
        assert result.placed_count == 0

    def test_empty_html_with_findings_marks_all_unplaced(self):
        findings = [_finding()]
        result = annotate("", findings)
        assert result.unplaced == findings
        assert result.placed_count == 0

    def test_injects_marker_for_matching_element(self):
        html = '<div data-m11-element="Full Title">A Trial</div>'
        result = annotate(html, [_finding()])
        # Marker is a native <details> inside the target div, so it
        # travels with the element if the document is later restyled.
        assert "<details" in result.html
        assert "m11-doc-marker" in result.html
        assert 'data-m11-finding-index="0"' in result.html
        # Expanded body rendered inline — no client JS needed to show it.
        assert "m11-doc-marker-body" in result.html
        assert "M11_001" in result.html
        assert "Required element missing." in result.html
        assert result.placed_count == 1
        assert result.unplaced == []

    def test_unmatched_finding_goes_to_unplaced(self):
        html = '<div data-m11-element="Full Title">A Trial</div>'
        finding = _finding(element="Element Not In Document")
        result = annotate(html, [finding])
        assert "<details" not in result.html
        assert result.unplaced == [finding]
        assert result.placed_count == 0

    def test_finding_with_empty_element_name_goes_to_unplaced(self):
        html = '<div data-m11-element="Full Title">A Trial</div>'
        finding = _finding(element="")
        result = annotate(html, [finding])
        assert result.unplaced == [finding]

    def test_severity_drives_icon_and_colour(self):
        html = (
            '<div data-m11-element="A">a</div>'
            '<div data-m11-element="B">b</div>'
            '<div data-m11-element="C">c</div>'
        )
        findings = [
            _finding(element="A", severity="error"),
            _finding(element="B", severity="warning"),
            _finding(element="C", severity="info"),
        ]
        result = annotate(html, findings)
        # Severity class on the marker span.
        assert "severity-error" in result.html
        assert "severity-warning" in result.html
        assert "severity-info" in result.html
        # Icon + colour class on the nested <i>.
        assert "bi-x-circle-fill" in result.html
        assert "text-danger" in result.html
        assert "bi-exclamation-triangle-fill" in result.html
        assert "text-warning" in result.html
        assert "bi-info-circle" in result.html
        assert "text-secondary" in result.html

    def test_summary_carries_native_tooltip(self):
        html = '<div data-m11-element="Full Title">A Trial</div>'
        finding = _finding(
            rule="M11_001", message="Required element missing."
        )
        result = annotate(html, [finding])
        # ``title=`` on the summary gives users the rule essence on
        # hover without having to expand the <details>.
        assert 'title="M11_001: Required element missing."' in result.html

    def test_multiple_findings_on_same_element_both_annotate(self):
        html = '<div data-m11-element="Full Title">A Trial</div>'
        findings = [
            _finding(rule="M11_001", message="missing"),
            _finding(rule="M11_010", message="normalised"),
        ]
        result = annotate(html, findings)
        # Both markers present, with distinct indices that map back to
        # the original list.
        assert 'data-m11-finding-index="0"' in result.html
        assert 'data-m11-finding-index="1"' in result.html
        assert result.placed_count == 2

    def test_mixed_placed_and_unplaced_tallies_correctly(self):
        html = '<div data-m11-element="Full Title">A Trial</div>'
        findings = [
            _finding(element="Full Title"),
            _finding(element="Missing Element"),
            _finding(element="Full Title", rule="M11_010", severity="warning"),
        ]
        result = annotate(html, findings)
        assert result.placed_count == 2
        assert len(result.unplaced) == 1
        assert result.unplaced[0]["element_name"] == "Missing Element"

    def test_preserves_existing_html_structure(self):
        # Existing tags and attributes should round-trip; we only
        # append markers inside matching targets.
        html = (
            '<table class="ich-m11-title-page-table">'
            '<tr><td>Full Title</td>'
            '<td data-m11-element="Full Title"><p>Emicizumab study</p></td>'
            "</tr></table>"
        )
        result = annotate(html, [_finding()])
        assert 'class="ich-m11-title-page-table"' in result.html
        assert "<p>Emicizumab study</p>" in result.html
        # Marker nested inside the td.
        assert (
            'data-m11-element="Full Title"'
            in result.html.split("m11-doc-marker")[0]
        )

    def test_renders_expected_and_actual_in_body(self):
        html = '<div data-m11-element="Trial Phase">Phase 3</div>'
        finding = _finding(
            element="Trial Phase",
            rule="M11_010",
            severity="warning",
            message="Source value normalised.",
        )
        finding["expected"] = "Phase 3"
        finding["actual"] = "Phase III"
        result = annotate(html, [finding])
        # Expected / actual rows appear inside the <details> body so
        # they're visible when expanded, no JS needed.
        assert "Expected: " in result.html
        assert "Phase 3" in result.html
        assert "Actual: " in result.html
        assert "Phase III" in result.html

    def test_omits_expected_actual_rows_when_empty(self):
        # A finding with no expected/actual (e.g. M11_003) should not
        # render empty "Expected: " rows in the body — just the rule
        # id and message.
        html = '<div data-m11-element="Full Title">A Trial</div>'
        finding = _finding()
        finding["expected"] = None
        finding["actual"] = None
        result = annotate(html, [finding])
        assert "Expected: " not in result.html
        assert "Actual: " not in result.html
