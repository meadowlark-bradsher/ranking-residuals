"""Synthetic calibration rig for the HodgeRank rankability certificate.

A deterministic, known-answer data source for the instrument in ``hodge.py``.
The rig manufactures comparison data with *controlled* Hodge structure so the
certificate can be validated against ground truth before any LLM judge is
involved.

``hodge.py`` is IMPORTED, never reimplemented (spec 6). Nothing in this package
defines a coboundary operator, a projector, or a decomposition.
"""

__all__ = [
    "config",
    "pool",
    "flows",
    "graph",
    "oracle",
    "provenance",
    "fit",
    "emit",
    "sweep",
    "report",
]
