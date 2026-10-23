from app.screen3.service import DIMENSIONS_SPEC, _build_response


def test_screen3_weights_total_100_and_are_fixed():
    assert len(DIMENSIONS_SPEC) == 16
    assert sum(weight for _, _, weight in DIMENSIONS_SPEC) == 100


def test_scorecard_calculates_points_and_verifies_quotes():
    script = "SCENE 1: INT. ROOM - DAY\nMIRA: I will tell everyone the truth.\n"
    raw = {
        "scores": [
            {"key": "concept_originality", "rating": 8, "excerpt": "I will tell everyone the truth.",
             "location": "Scene 1", "rationale": "Clear conflict."},
            {"key": "story_structure", "rating": 7, "excerpt": "This quote is not in the screenplay.",
             "location": "Scene 9", "rationale": "Structure seems clear."},
        ],
        "overall_summary": "A test summary",
    }
    result = _build_response(1, 2, raw, script, "gemini", "test-model", 100, 30, False)
    by_key = {d.key: d for d in result.dimensions}
    assert by_key["concept_originality"].calculated_points == 9.6
    assert by_key["concept_originality"].is_complete is True
    assert by_key["story_structure"].evidence_excerpt == ""
    assert by_key["story_structure"].is_complete is False
    assert result.is_complete is False
    assert result.input_tokens == 100


def test_cached_scorecard_reports_zero_new_tokens():
    script = "A line in the screenplay."
    raw = {"scores": [{"key": "concept_originality", "rating": 5,
                       "excerpt": "A line in the screenplay.", "location": "Scene 1", "rationale": "Evidence."}]}
    result = _build_response(1, 1, raw, script, "gemini", "test-model", 300, 50, True)
    assert result.cache_hit is True
    assert result.input_tokens == 0
    assert result.output_tokens == 0
