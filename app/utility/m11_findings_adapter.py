"""Retired adapter — intentionally left empty.

The original content translated the new ``usdm4_protocol.validation.m11``
``Results`` shape into a legacy finding-dict shape consumed by the
workbench templates and exports.  Task #35 retired the legacy shape:
every caller now imports :func:`app.utility.finding_projections.project_m11_result`
instead and reads the canonical row shape directly.

This file is kept as a breadcrumb so ``git log`` shows when the
adapter was removed.  It should be deleted from the working tree in
the same commit that lands this retirement.
"""
