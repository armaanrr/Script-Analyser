from types import SimpleNamespace
from app.screen7.service import _build_response


def screenplay(version_no=2):
    return SimpleNamespace(version_no=version_no)


def sample():
    return {
        "audience_segments": [{"segment_type": "Primary", "target_group": "Adult melodrama viewers",
            "motivations": "Emotional suspense", "viewing_context": "Short mobile sessions",
            "appeal_barriers": "Slow opening", "confidence": "High"}],
        "women_development_lens": {"empowerment_beat": "The lead makes a consequential choice",
            "family_resonance": "Generational tension", "relationship_depth": "Trust develops slowly",
            "development_recommendations": ["Show the choice's consequences"]},
        "family_suitability_summary": "Family conflict is central.",
        "emotional_journey": [{"phase": "Opening", "dominant_emotions": ["Curiosity"], "narrative_payoff": "A secret is introduced."}],
        "title_evaluation": {"working_title": "The Hidden Promise", "memorability_score": 8.5,
            "genre_cultural_fit": "Signals melodrama", "strengths": ["Clear emotional promise"],
            "alternative_suggestions": ["A Promise in Shadow"]},
        "world_building": {"setting_distinctiveness": "Contrasting households", "social_rules_and_friction": "Class tension",
            "world_consistency": "Mostly consistent", "evidence_excerpt": "MAYA enters the family home."},
        "review_notes": []
    }


def test_screen7_verifies_world_evidence_and_preserves_fields():
    source = "Scene 1: MAYA enters the family home. Scene 2: They argue."
    result = _build_response(7, screenplay(), sample(), source, "gemini", "test-model", 700, 180, False)
    assert result.project_id == 7
    assert result.title_evaluation.memorability_score == 8.5
    assert result.audience_segments[0].confidence == "High"
    assert result.world_building.evidence_verified is True
    assert result.input_tokens == 700


def test_screen7_removes_unverified_excerpt_and_cache_reports_zero_tokens():
    raw = sample()
    raw["world_building"]["evidence_excerpt"] = "This quote is not in the script"
    result = _build_response(3, screenplay(1), raw, "Only different source text.", "gemini", "test-model", 0, 0, True)
    assert result.world_building.evidence_excerpt == ""
    assert result.world_building.evidence_verified is False
    assert result.cache_hit is True
    assert result.input_tokens == 0 and result.output_tokens == 0
    assert result.review_notes


def test_screen7_clamps_invalid_title_score_and_confidence():
    raw = sample()
    raw["title_evaluation"]["memorability_score"] = 17
    raw["audience_segments"][0]["confidence"] = "certain"
    result = _build_response(2, screenplay(), raw, "MAYA enters the family home.", "gemini", "test-model", 10, 5, False)
    assert result.title_evaluation.memorability_score == 10
    assert result.audience_segments[0].confidence == "Medium"
