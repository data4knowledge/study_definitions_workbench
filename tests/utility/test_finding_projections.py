"""Unit tests for ``app.utility.finding_projections``.

Focused on ``project_usdm_core_summary`` because the per-row
projections are exercised via the router-level tests already.  The
summary projector is exercised in isolation here so its defensive
fallbacks (``None`` input, partial fields, non-CORE objects) are
covered without standing up a full validation run.
"""

from types import SimpleNamespace

from app.utility.finding_projections import project_usdm_core_summary


def _finding(error_count: int = 0):
    """Build a minimal CORE finding stand-in.

    Only the fields the summary projector reads (``errors``) are
    populated — the projector duck-types and ignores the rest.
    """
    return SimpleNamespace(errors=[{} for _ in range(error_count)])


def _result(**overrides):
    """Build a CORE-shaped result via ``SimpleNamespace`` so the
    projector's ``hasattr(result, "rules_executed")`` check passes
    without us having to import the real dataclass."""
    base = {
        "rules_executed": 0,
        "rules_skipped": 0,
        "ct_packages_available": 0,
        "ct_packages_loaded": [],
        "execution_errors": [],
        "findings": [],
        "file_path": "",
        "version": "4-0",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class TestProjectUsdmCoreSummary:
    def test_none_input_returns_empty(self):
        assert project_usdm_core_summary(None) == {}

    def test_non_core_object_returns_empty(self):
        # A rules-engine result object has ``to_dict`` but no
        # ``rules_executed`` attribute — the duck-type check should
        # short-circuit and return an empty dict so the template's
        # ``{% if summary %}`` guard skips the CORE-only header.
        rules_like = SimpleNamespace(to_dict=lambda: [])
        assert project_usdm_core_summary(rules_like) == {}

    def test_happy_path_full_summary(self):
        result = _result(
            rules_executed=120,
            rules_skipped=3,
            ct_packages_available=42,
            ct_packages_loaded=["sdtmct-2024-03", "adamct-2024-03"],
            execution_errors=[{"rule": "X"}, {"rule": "Y"}],
            findings=[_finding(2), _finding(5)],
            file_path="/tmp/study.json",
            version="4-0",
        )
        summary = project_usdm_core_summary(result)
        assert summary == {
            "engine": "core",
            "version": "4-0",
            "file_path": "/tmp/study.json",
            "rules_executed": 120,
            "rules_skipped": 3,
            "finding_count": 7,
            "rule_count": 2,
            "execution_error_count": 2,
            "ct_packages_available": 42,
            "ct_packages_loaded": ["sdtmct-2024-03", "adamct-2024-03"],
            "ct_packages_loaded_count": 2,
        }

    def test_empty_run_collapses_to_zeros(self):
        # A run with no findings, no execution errors, no CT packages
        # loaded should still produce a populated dict (so the header
        # card renders) — just with zero counts.
        summary = project_usdm_core_summary(_result(rules_executed=10))
        assert summary["finding_count"] == 0
        assert summary["rule_count"] == 0
        assert summary["execution_error_count"] == 0
        assert summary["ct_packages_loaded"] == []
        assert summary["ct_packages_loaded_count"] == 0
        assert summary["rules_executed"] == 10

    def test_missing_optional_fields_default_safely(self):
        # ``ct_packages_loaded=None`` mimics a partially-initialised
        # result object; the projector should coerce to ``[]`` rather
        # than blow up.
        result = _result(ct_packages_loaded=None, execution_errors=None)
        summary = project_usdm_core_summary(result)
        assert summary["ct_packages_loaded"] == []
        assert summary["ct_packages_loaded_count"] == 0
        assert summary["execution_error_count"] == 0

    def test_finding_count_aggregates_per_finding_errors(self):
        # ``finding_count`` is the *total error count across findings*,
        # not the count of findings — mirrors
        # ``CoreValidationResult.finding_count``. ``rule_count`` is the
        # number of distinct findings (one per rule).
        result = _result(findings=[_finding(0), _finding(4), _finding(1)])
        summary = project_usdm_core_summary(result)
        assert summary["finding_count"] == 5
        assert summary["rule_count"] == 3
