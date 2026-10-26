from app.screen5.service import MAX_EPISODE_SECONDS, _segment_screenplay


def test_segments_follow_producer_selected_episode_count():
    script = "\n".join(
        [
            "INT. HOUSE - DAY",
            "Scene one body",
            "EXT. ROAD - DAY",
            "Scene two body",
            "INT. OFFICE - DAY",
            "Scene three body",
            "EXT. GARDEN - DAY",
            "Scene four body",
        ]
    )

    segments = _segment_screenplay(script, selected_count=2)

    assert len(segments) == 2
    assert all(segment["episode_number"] == index for index, segment in enumerate(segments, start=1))
    assert "Scene one body" in segments[0]["text"]
    assert "Scene four body" in segments[1]["text"]


def test_scripts_without_scene_headings_are_still_split_to_selected_count():
    script = "\n".join(f"Paragraph {index} has several words for a story beat." for index in range(1, 10))

    segments = _segment_screenplay(script, selected_count=3)

    assert len(segments) == 3
    combined = "\n".join(segment["text"] for segment in segments)
    for index in range(1, 10):
        assert f"Paragraph {index}" in combined


def test_three_minute_runtime_threshold_is_180_seconds():
    script_at_limit = " ".join(["word"] * 450)
    script_over_limit = " ".join(["word"] * 451)

    at_limit = _segment_screenplay(script_at_limit, selected_count=1)[0]
    over_limit = _segment_screenplay(script_over_limit, selected_count=1)[0]

    assert MAX_EPISODE_SECONDS == 180
    assert at_limit["estimated_runtime_seconds"] == 180
    assert at_limit["exceeds_max_runtime"] is False
    assert over_limit["estimated_runtime_seconds"] == 181
    assert over_limit["exceeds_max_runtime"] is True
