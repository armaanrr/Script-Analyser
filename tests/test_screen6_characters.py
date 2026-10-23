from types import SimpleNamespace

from app.screen6.service import _build_response


def screenplay(version_no=3):
    return SimpleNamespace(version_no=version_no)


def test_screen6_verifies_quotes_and_preserves_character_fields():
    source = "MAYA: I know the truth.\nRAJ: Then tell them."
    raw = {
        "character_profiles": [{
            "name": "Maya", "role": "Protagonist", "goals_external": "Reveal the truth",
            "internal_need": "Trust herself", "fear_and_stakes": "Losing her family",
            "character_arc": "Moves from fear to agency", "agency_level": "High",
            "evidence_excerpt": "MAYA: I know the truth.",
        }],
        "relationships": [{"characters": "Maya & Raj", "relationship_type": "Allies",
            "power_balance": "Raj initially leads; Maya takes control", "key_conflict": "Whether to reveal the truth",
            "evidence_excerpt": "RAJ: Then tell them."}],
        "emotional_beats": [{"episode_scene": "Scene 4", "emotion_type": "Resolve",
            "quote_excerpt": "MAYA: I know the truth.", "impact_rationale": "She chooses disclosure."}],
        "consistency_checks": [],
        "casting_requirements": [{"character_name": "Maya", "age_range": "Not specified by script",
            "language_performance": "Natural conversational delivery", "key_traits": ["guarded", "resilient"]}],
        "review_notes": [],
    }
    result = _build_response(12, screenplay(), raw, source, "gemini", "test-model", 500, 120, False)
    assert result.project_id == 12
    assert result.character_profiles[0].evidence_verified is True
    assert result.relationships[0].evidence_verified is True
    assert result.emotional_beats[0].evidence_verified is True
    assert result.character_profiles[0].agency_level == "High"
    assert result.input_tokens == 500


def test_screen6_unverified_quotes_are_removed_and_cache_reports_zero_tokens():
    raw = {
        "character_profiles": [{"name": "Maya", "agency_level": "Very High", "evidence_excerpt": "Not in script"}],
        "relationships": [], "emotional_beats": [], "consistency_checks": [], "casting_requirements": [],
    }
    result = _build_response(4, screenplay(1), raw, "The source contains another line.", "gemini", "test-model", 0, 0, True)
    assert result.character_profiles[0].evidence_excerpt == ""
    assert result.character_profiles[0].evidence_verified is False
    assert result.character_profiles[0].agency_level == "Medium"
    assert result.cache_hit is True
    assert result.input_tokens == 0 and result.output_tokens == 0
    assert result.review_notes
