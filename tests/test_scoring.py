from app.schemas import DimensionRating
from app.scoring import DIMENSIONS, compute_score


def ratings(value=8.0, skip=None):
    return [DimensionRating(dimension_key=k, rating=None if k == skip else value, rationale="x", evidence_basis="x")
            for k, _, _ in DIMENSIONS]


def test_weights_total_100():
    assert sum(w for _, _, w in DIMENSIONS) == 100


def test_complete_when_traction_verified():
    s = compute_score(ratings(10), traction_verified=True)
    assert s.status == "complete" and s.total == 100


def test_provisional_without_traction():
    s = compute_score(ratings(8), traction_verified=False)
    assert s.status == "provisional" and s.total == 80


def test_missing_rating_is_incomplete_not_zero():
    s = compute_score(ratings(8, skip="originality"), traction_verified=True)
    assert s.status == "incomplete" and s.total is None and s.points_so_far == 56.0


def test_out_of_range_rejected():
    r = ratings(8)
    r[0].rating = 14
    assert compute_score(r, True).status == "incomplete"
