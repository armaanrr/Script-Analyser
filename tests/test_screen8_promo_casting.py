from types import SimpleNamespace
from app.screen8.service import _build_response, _literal_choice


def screenplay(version_no=3):
    return SimpleNamespace(version_no=version_no)


def sample():
    return {
        "promo_scenes": [{"scene_ref": "Scene 2", "context": "A secret is revealed", "emotional_punch": "Shock", "intended_use": "Teaser", "spoiler_risk": "Low"}],
        "verbatim_dialogues": [
            {"quote": "I will find the truth.", "speaker": "Rajjo", "scene_ref": "Scene 2", "context": "She makes a promise", "emotional_punch": "Resolve", "spoiler_risk": "Low"},
            {"quote": "A fabricated line.", "speaker": "Azlaan", "scene_ref": "Scene 4", "context": "Unknown", "emotional_punch": "Unknown", "spoiler_risk": "Low"}
        ],
        "season_strategy": {"recommendation": "Season 2 Viable", "resolved_arcs": ["A secret is revealed"], "open_threads": ["A rival remains"], "sequel_engine": "The rival returns", "ending_payoff_rationale": "The main promise is fulfilled."},
        "casting_context": {"confirmed_genre": "Melodrama", "content_positioning": "Romantic suspense", "role_brief": "Emotionally layered lead", "language_demands": "Hindi", "audience_expectation": "High emotional stakes"},
        "candidates": [{"candidate_name": "Candidate A", "target_role": "Rajjo", "role_fit_analysis": "Strong dramatic range", "positioning_fit_analysis": "Producer review needed", "trade_offs_and_alternatives": "Availability must be confirmed", "confidence_level": "Certain", "review_prompt": "Review screen test and availability."}],
        "review_notes": []
    }


def test_screen8_verifies_quotes_and_normalizes_confidence():
    result = _build_response(5, screenplay(), sample(), "Scene 2: I will find the truth.", "gemini", "test-model", 500, 120, False, {})
    assert result.project_id == 5
    assert len(result.verbatim_dialogues) == 1
    assert result.verbatim_dialogues[0].quote == "I will find the truth."
    assert result.candidates[0].confidence_level == "Review Required"
    assert result.input_tokens == 500
    assert any("could not be verified" in note for note in result.review_notes)


def test_screen8_cached_usage_is_zero_and_saved_decision_is_restored():
    saved = SimpleNamespace(decision="Shortlist", rationale="Screen test approved", decided_by="Producer")
    result = _build_response(5, screenplay(), sample(), "Scene 2: I will find the truth.", "gemini", "test-model", 0, 0, True, {"Candidate A": saved})
    assert result.cache_hit is True
    assert result.input_tokens == 0 and result.output_tokens == 0
    assert result.candidates[0].current_decision == "Shortlist"
    assert result.candidates[0].decision_rationale == "Screen test approved"


def test_screen8_choice_rejects_unrecognized_values():
    assert _literal_choice("Very High", {"Low", "Medium", "High"}, "Medium") == "Medium"
