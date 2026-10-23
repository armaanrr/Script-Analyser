from types import SimpleNamespace

from app.screen5.service import _build_response


def screenplay(text="MAYA: I know the truth.\nShe opens the door."):
    return SimpleNamespace(version_no=2)


def test_screen5_verifies_rewrite_evidence_and_marks_unverified():
    source = "MAYA: I know the truth.\nShe opens the door."
    raw = {
        "total_episodes_detected": 1,
        "episodes": [{
            "episode_number": 1,
            "episode_title": "The Door",
            "scene_range": "Scenes 1-3",
            "opening_hook": "Maya discovers a secret.",
            "hook_rating": "Strong",
            "conflict_progression": "The discovery raises the stakes.",
            "emotional_shift": "Fear becomes resolve.",
            "ending_cliffhanger": "Who is behind the door?",
            "cliffhanger_rating": "Moderate",
            "continuity_payoffs": "The secret is introduced for later payoff.",
            "rewrite_task": {
                "priority": "High",
                "issue_evidence": "The line needs a clearer consequence.",
                "evidence_excerpt": "MAYA: I know the truth.",
                "proposed_action": "Show what Maya risks by revealing it.",
                "success_criteria": "The audience understands the immediate cost.",
                "owner": "Writer",
                "status": "Open",
            },
        }],
        "review_notes": [],
    }
    result = _build_response(5, screenplay(), raw, source, "gemini", "test-model", 120, 80, False)
    assert result.total_episodes_detected == 1
    assert result.episodes[0].rewrite_task.evidence_verified is True
    assert result.input_tokens == 120


def test_screen5_flags_unverified_evidence_and_cache_uses_zero_tokens():
    source = "A short screenplay line."
    raw = {
        "total_episodes_detected": 1,
        "episodes": [{
            "episode_number": 1,
            "episode_title": "Episode One",
            "rewrite_task": {
                "priority": "Unknown",
                "evidence_excerpt": "A quote that is not in the screenplay.",
                "issue_evidence": "Potential issue.",
                "proposed_action": "Review the scene.",
                "success_criteria": "Clarify the beat.",
            },
        }],
    }
    result = _build_response(5, screenplay(), raw, source, "gemini", "test-model", 0, 0, True)
    task = result.episodes[0].rewrite_task
    assert task.priority == "Medium"
    assert task.evidence_verified is False
    assert task.evidence_excerpt == ""
    assert result.cache_hit is True
    assert result.input_tokens == 0 and result.output_tokens == 0
    assert result.review_notes
