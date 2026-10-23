from types import SimpleNamespace
from app.screen9.service import _choice, _int, _estimate, _assemble


def test_screen9_normalizes_invalid_model_values_and_shooting_estimate():
    assert _choice("Very High", {"High", "Medium", "Low"}, "Medium") == "Medium"
    assert _int("not-a-number") == 0
    estimate = _estimate(9, 3, 2)
    assert estimate.total_scenes == 9
    assert estimate.unique_locations_count == 3
    assert estimate.total_estimated_shooting_days >= estimate.base_days
    assert "Base (9 scenes" in estimate.visible_formula


def test_screen9_assembly_restores_saved_task_state_and_reports_cache_usage():
    from app.screen9.schemas import Screen9ProductionResponse

    class FakeDB:
        def scalars(self, query):
            return SimpleNamespace(all=lambda: [SimpleNamespace(
                task_key="TASK-01", priority="High", target_scenes="Scene 4",
                issue_identified="Repeated exposition", proposed_rewrite="Combine two beats",
                expected_impact="Faster pace", owner="Director", status="In Progress")])
        def add(self, item):
            raise AssertionError("Cached response should not add a new task")
        def commit(self):
            pass

    script = SimpleNamespace(version_no=2)
    raw = {
        "complexity_stats": {"total_scenes": 9, "interior_scenes": 5, "exterior_scenes": 4,
            "day_scenes": 6, "night_scenes": 3, "high_complexity_scenes": 2,
            "medium_complexity_scenes": 3, "low_complexity_scenes": 4},
        "cast_breakdown": [], "location_breakdown": [],
        "rewrite_plan": [{"task_id": "TASK-01", "priority": "Low", "target_scenes": "Scene 4",
            "issue_identified": "New version text", "proposed_rewrite": "New proposal", "expected_impact": "Impact", "owner": "Writer"}],
        "version_comparison": {"comparison_summary": "Previous draft unavailable"}, "review_notes": []
    }
    result = _assemble(7, script, raw, FakeDB(), "gemini", "test-model", 0, 0, True)
    assert isinstance(result, Screen9ProductionResponse)
    assert result.cache_hit is True
    assert result.input_tokens == 0 and result.output_tokens == 0
    assert result.rewrite_plan[0].status == "In Progress"
    assert result.rewrite_plan[0].owner == "Director"
    assert result.rewrite_plan[0].priority == "High"
