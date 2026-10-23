from app.screen4.service import _build_response


def test_screen4_keeps_human_signoff_pending_and_verifies_quotes():
    script = "EPISODE 1 SCENE 2\nMIRA: I will always protect you.\nThey laugh awkwardly at dinner."
    raw = {
        "erotic_gate": {"status": "Pass", "summary": "No explicit content detected.", "flagged_scenes": []},
        "originality_gate": {"status": "Pass", "summary": "No obvious internal similarity risk found."},
        "completeness_gate": {"status": "Pass", "summary": "Available scene progression appears coherent."},
        "cringe_score": 4.5, "cringe_beats": ["Awkward dinner scene"],
        "humiliation_score": 2.0, "humiliation_beats": [],
        "romance_score": 7.0,
        "romance_moments": [{"episode_scene": "Episode 1, Scene 2", "quote_excerpt": "I will always protect you.", "emotional_punch": "Signals devotion."},
                            {"episode_scene": "Scene 8", "quote_excerpt": "invented quote", "emotional_punch": "Unsupported."}],
    }
    result = _build_response(3, 2, raw, script, "gemini", "test-model", 100, 50, False)
    assert result.overall_gate_status == "Review Required"
    assert result.gates[-1].key == "human_signoff"
    assert result.gates[-1].status == "Review Required"
    assert result.high_romance_meter.top_moments[0].evidence_verified is True
    assert result.high_romance_meter.top_moments[1].evidence_verified is False
    assert result.high_romance_meter.top_moments[1].quote_excerpt == ""


def test_screen4_score_bounds_and_cache_token_reporting():
    raw = {
        "erotic_gate": {"status": "Pass", "summary": "Clean."},
        "originality_gate": {"status": "Pass", "summary": "No obvious issue."},
        "completeness_gate": {"status": "Pass", "summary": "Looks complete."},
        "cringe_score": 5, "humiliation_score": 5, "romance_score": 5,
    }
    result = _build_response(1, 1, raw, "A screenplay.", "gemini", "test-model", 10, 20, True)
    assert result.cache_hit is True
    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert result.overall_gate_status == "Review Required"
