from app.screen10.routes import _simple_pdf, router
from app.screen10.schemas import DecisionRequest, ChecklistRequest, OverrideRequest
from pydantic import ValidationError


def test_screen10_router_is_registered_with_expected_routes():
    paths = {route.path for route in router.routes}
    assert "/api/screen10/projects" in paths
    assert "/api/screen10/dashboard/{concept_id}" in paths
    assert "/api/screen10/decision/{concept_id}" in paths
    assert "/api/screen10/export/{concept_id}.json" in paths
    assert "/api/screen10/export/{concept_id}.pdf" in paths


def test_minimal_pdf_export_is_a_valid_pdf_payload():
    payload = _simple_pdf(["Rocket Reels review", "Human approval record"])
    assert payload.startswith(b"%PDF-1.4")
    assert b"%%EOF" in payload


def test_decision_requires_reason_and_known_role():
    req = DecisionRequest(decision_type="concept", decision="approve_to_screenplay",
                          rationale="Approved based on the reviewed concept evidence.",
                          reviewer_name="Producer", reviewer_role="producer")
    assert req.decision_type == "concept"
    try:
        DecisionRequest(decision_type="concept", decision="approve_to_screenplay",
                        rationale="ok", reviewer_name="Producer", reviewer_role="producer")
        assert False, "Short rationale should be rejected"
    except ValidationError:
        pass


def test_checklist_and_override_payload_shapes():
    checklist = ChecklistRequest(reviewer_name="Reviewer", reviewer_role="producer",
                                 items={"scorecard_reviewed": True, "gates_resolved": False})
    assert checklist.items["gates_resolved"] is False
    override = OverrideRequest(field_key="episode_hooks", original_value="6", adjusted_value="7",
                               rationale="Human review found additional supporting evidence.",
                               reviewer_name="Reviewer", reviewer_role="producer")
    assert override.original_value == "6"
    assert override.adjusted_value == "7"
