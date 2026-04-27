"""Unit tests for ``app.utility.finding_projections``.

Focused on the two summary projectors
(:func:`project_usdm_core_summary` and
:func:`project_usdm_rules_summary`) because the per-row projections
are exercised via the router-level tests already.  The summary
projectors are exercised in isolation here so their defensive
fallbacks (``None`` input, partial fields, wrong-engine objects) are
covered without standing up a full validation run.
"""

from types import SimpleNamespace

from app.utility.finding_projections import (
    project_usdm_core_summary,
    project_usdm_rules_summary,
)


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


# ---- d4k rules engine summary -----------------------------------------


def _outcome(status: str, error_count: int = 0):
    """Build a minimal ``RuleOutcome`` stand-in.

    The projector reads ``status.value`` and ``error_count`` — wraps
    the status in a tiny namespace that mimics the real
    ``RuleStatus`` enum's ``.value`` attribute access.
    """
    return SimpleNamespace(
        status=SimpleNamespace(value=status),
        error_count=error_count,
    )


def _rules_result(outcomes_by_id=None, finding_count=0):
    """Build a ``RulesValidationResults``-shaped namespace.

    The projector duck-types — it needs ``outcomes`` (dict),
    ``count()`` (callable), and ``finding_count`` (int property).
    """
    outcomes = outcomes_by_id or {}
    return SimpleNamespace(
        outcomes=outcomes,
        count=lambda: len(outcomes),
        finding_count=finding_count,
    )


class TestProjectUsdmRulesSummary:
    def test_none_input_returns_empty(self):
        assert project_usdm_rules_summary(None) == {}

    def test_non_rules_object_returns_empty(self):
        # A CORE result has ``rules_executed`` but no ``outcomes`` /
        # ``count()`` — duck-type check should reject it so the
        # template's ``engine`` discriminator stays clean.
        core_like = SimpleNamespace(rules_executed=10, findings=[])
        assert project_usdm_rules_summary(core_like) == {}

    def test_happy_path_full_summary(self):
        result = _rules_result(
            outcomes_by_id={
                "R001": _outcome("Success"),
                "R002": _outcome("Success"),
                "R003": _outcome("Failure", error_count=4),
                "R004": _outcome("Failure", error_count=1),
                "R005": _outcome("Exception"),
                "R006": _outcome("Not Implemented"),
                "R007": _outcome("Not Implemented"),
            },
            finding_count=5,
        )
        summary = project_usdm_rules_summary(result)
        assert summary == {
            "engine": "d4k",
            "version": "",
            "file_path": "",
            "rules_executed": 7,
            "rules_skipped": 0,
            "finding_count": 5,
            "rule_count": 2,  # two Failure outcomes with errors
            "success_count": 2,
            "failure_count": 2,
            "exception_count": 1,
            "not_implemented_count": 2,
        }

    def test_empty_run(self):
        # No outcomes at all — projection should still return a
        # populated dict (so the header card renders) with all counts
        # zeroed.
        summary = project_usdm_rules_summary(_rules_result())
        assert summary["engine"] == "d4k"
        assert summary["rules_executed"] == 0
        assert summary["finding_count"] == 0
        assert summary["failure_count"] == 0
        assert summary["exception_count"] == 0
        assert summary["not_implemented_count"] == 0

    def test_rule_count_excludes_failures_with_no_errors(self):
        # ``rule_count`` is "rules that produced findings" — a Failure
        # with ``error_count=0`` is a degenerate outcome and shouldn't
        # be counted as a finding-producing rule.
        result = _rules_result(
            outcomes_by_id={
                "R001": _outcome("Failure", error_count=0),
                "R002": _outcome("Failure", error_count=2),
            },
            finding_count=2,
        )
        summary = project_usdm_rules_summary(result)
        assert summary["failure_count"] == 2
        assert summary["rule_count"] == 1

    def test_unknown_status_is_ignored(self):
        # An outcome with a status outside the four known buckets
        # shouldn't blow up the projection — it just doesn't increment
        # any of the per-status counters.
        result = _rules_result(
            outcomes_by_id={
                "R001": _outcome("Mystery"),
                "R002": _outcome("Success"),
            }
        )
        summary = project_usdm_rules_summary(result)
        assert summary["rules_executed"] == 2
        assert summary["success_count"] == 1
        assert (
            summary["failure_count"]
            == summary["exception_count"]
            == summary["not_implemented_count"]
            == 0
        )
