"""Concept-stage scoring (100 points). The BACKEND does all arithmetic.

The model supplies 0-10 ratings; it never supplies points or totals.
This is a separate model from the 16-dimension full-screenplay score (Screen 3).
"""
from .schemas import DimensionRating, DimensionScore, ScoreResult

# key, label, weight  (from blueprint v2.1, Screen 01)
DIMENSIONS = [
    ("originality", "Originality & differentiation", 30),
    ("comparables", "Comparable titles & verified traction", 20),
    ("taxonomy", "Concept categories & genre clarity", 15),
    ("women_24_45_development", "Development potential for women 24-45", 20),
    ("audience_id", "Audience identification", 10),
    ("micro_drama_engine", "Micro-drama engine", 5),
]
assert sum(w for _, _, w in DIMENSIONS) == 100


def compute_score(ratings: list[DimensionRating], traction_verified: bool) -> ScoreResult:
    by_key: dict[str, DimensionRating] = {}
    for r in ratings:
        by_key.setdefault(r.dimension_key, r)   # first rating per dimension wins

    rows: list[DimensionScore] = []
    for key, label, weight in DIMENSIONS:
        r = by_key.get(key)
        if r is None or r.rating is None:
            rows.append(DimensionScore(key=key, label=label, weight=weight, rating=None,
                                       points=None, status="incomplete",
                                       note="No rating: insufficient evidence."))
            continue
        if not 0 <= r.rating <= 10:
            rows.append(DimensionScore(key=key, label=label, weight=weight, rating=None,
                                       points=None, status="incomplete",
                                       note=f"Rejected out-of-range rating ({r.rating})."))
            continue
        points = round(r.rating / 10 * weight, 1)
        provisional = key == "comparables" and not traction_verified
        rows.append(DimensionScore(
            key=key, label=label, weight=weight, rating=r.rating, points=points,
            status="provisional" if provisional else "rated",
            note="Comparison quality only; verified traction data not connected." if provisional else None))

    so_far = round(sum(d.points or 0 for d in rows), 1)
    missing = [d.label for d in rows if d.status == "incomplete"]
    if missing:
        return ScoreResult(dimensions=rows, total=None, points_so_far=so_far, status="incomplete",
                           status_reason="Incomplete, not zero: " + "; ".join(missing))
    if any(d.status == "provisional" for d in rows):
        return ScoreResult(dimensions=rows, total=so_far, points_so_far=so_far, status="provisional",
                           status_reason="Provisional: verified traction data is unavailable, so the "
                                         "comparables dimension is scored on comparison quality only.")
    return ScoreResult(dimensions=rows, total=so_far, points_so_far=so_far, status="complete",
                       status_reason="All six dimensions rated with verified inputs.")
