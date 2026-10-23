"""Deterministic screenplay extraction with smart scene-based episode auto-chunking.

Pure Python, no external dependencies. Produces stable IDs (E03 for episodes,
E03-S02 for scenes) with line and character ranges, so every later finding can
point at exact source evidence.
"""
import hashlib
import re

EP_HEAD = re.compile(
    r"^(?:EPISODE|EP)(?![A-Za-z])\.?\s*[:#\-–—]?\s*(\d{1,3})(?!\d)[\s:.\-–—]*(.*)$",
    re.I,
)
SCENE_HEAD = re.compile(
    r"^(?:\d+[A-Z]?[.)]?\s+)?(?:(?:INT|EXT|INT/EXT|I/E)\b[./\s]|SCENE\s*\d+)",
    re.I,
)
HEADER_FIELD = re.compile(r"^(genre|sub[\s-]?genre)\s*[:\-–]\s*(.+)$", re.I)
MIN_EPISODE_WORDS = 30


def normalize_text(text: str) -> str:
    return text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_screenplay(text: str, expected: int | None = None) -> dict:
    """`text` must already be normalised (normalize_text); offsets refer to this exact string."""
    lines = text.split("\n")
    starts, pos = [], 0
    for ln in lines:
        starts.append(pos)
        pos += len(ln) + 1

    heads = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if 0 < len(s) <= 80:
            m = EP_HEAD.match(s)
            if m and len(m.group(2)) <= 60:
                heads.append((i, int(m.group(1)), m.group(2).strip(" :.-–—")))

    # Track whether we auto-chunked or inferred episodes
    auto_chunked = False
    inferred_single_episode = False

    # -------------------------------------------------------------------------
    # SMART FALLBACK: If no explicit "EPISODE" headers exist in the text
    # -------------------------------------------------------------------------
    if not heads and text.strip():
        # Find all scene line locations across the raw screenplay
        scene_lines = []
        for i, ln in enumerate(lines):
            s = ln.strip()
            if s and len(s) <= 120 and SCENE_HEAD.match(s):
                scene_lines.append(i)

        if scene_lines and expected and expected > 1:
            total_scenes = len(scene_lines)
            scenes_per_ep = max(1, round(total_scenes / expected))

            for ep_idx in range(expected):
                start_scene_i = ep_idx * scenes_per_ep
                if start_scene_i >= total_scenes:
                    break
                line_idx = scene_lines[start_scene_i]
                ep_num = ep_idx + 1
                heads.append(
                    (line_idx, ep_num, f"Episode {ep_num} (Auto-Chunked)")
                )
            auto_chunked = True
        else:
            # Fallback for standalone / single-episode scripts
            heads = [
                (0, 1, "Full screenplay (inferred; no episode heading found)")
            ]
            inferred_single_episode = True

    warnings, episodes, seen = [], [], {}
    for k, (i, num, title) in enumerate(heads):
        last = heads[k + 1][0] - 1 if k + 1 < len(heads) else len(lines) - 1
        while last > i and not lines[last].strip():
            last -= 1
        seen[num] = seen.get(num, 0) + 1
        ep_id = f"E{num:02d}" + (
            "" if seen[num] == 1 else chr(96 + seen[num])
        )  # E05, E05b (duplicate)
        c0, c1 = starts[i], starts[last] + len(lines[last])
        words = len(text[c0:c1].split())

        scenes = []
        # Examine lines within the episode range for scene headings
        search_start = i if (auto_chunked or inferred_single_episode) else i + 1
        for j in range(search_start, last + 1):
            s = lines[j].strip()
            if s and len(s) <= 120 and SCENE_HEAD.match(s):
                if scenes:
                    scenes[-1]["end_line"] = j
                scenes.append(
                    {
                        "id": f"{ep_id}-S{len(scenes) + 1:02d}",
                        "heading": s[:100],
                        "start_line": j + 1,
                        "end_line": last + 1,
                    }
                )
        ep = {
            "id": ep_id,
            "number": num,
            "title": title,
            "start_line": i + 1,
            "end_line": last + 1,
            "char_start": c0,
            "char_end": c1,
            "word_count": words,
            "scenes": scenes,
            "scene_count": len(scenes),
            "readable": words >= MIN_EPISODE_WORDS,
        }
        episodes.append(ep)
        if not ep["readable"]:
            warnings.append(
                {
                    "code": "unreadable_episode",
                    "episode_id": ep_id,
                    "message": f"{ep_id} has only {words} words; it may be empty or failed to extract.",
                }
            )

    if inferred_single_episode:
        warnings.append(
            {
                "code": "episode_heading_not_found",
                "episode_id": "E01",
                "message": "No explicit episode heading was found. The full screenplay is treated as one inferred episode.",
            }
        )

    nums = [n for _, n, _ in heads]
    uniq = sorted(set(nums))
    if uniq:
        target = (
            range(1, expected + 1)
            if expected
            else range(uniq[0], uniq[-1] + 1)
        )
        missing = [n for n in target if n not in set(uniq)]
    else:
        missing = []

    # If auto-chunked or matches expected, clear false missing warnings
    if auto_chunked and len(uniq) == expected:
        missing = []

    if missing:
        warnings.append(
            {
                "code": "missing_episodes",
                "episode_id": None,
                "message": "Episodes not detected: "
                + ", ".join(map(str, missing))
                + ".",
            }
        )
    dups = sorted(n for n, c in seen.items() if c > 1)
    if dups:
        warnings.append(
            {
                "code": "duplicate_episodes",
                "episode_id": None,
                "message": "Episode numbers appear more than once: "
                + ", ".join(map(str, dups))
                + ".",
            }
        )

    front = lines[: heads[0][0]] if heads else lines[:100]
    fields = {}
    for ln in front[:120]:
        m = HEADER_FIELD.match(ln.strip())
        if m:
            kind = (
                "subgenre" if m.group(1).lower().startswith("sub") else "genre"
            )
            fields.setdefault(kind, m.group(2).strip())

    return {
        "episodes": episodes,
        "detected_count": len(uniq),
        "expected_count": expected,
        "missing_episodes": missing,
        "scene_count": sum(e["scene_count"] for e in episodes),
        "word_count": sum(e["word_count"] for e in episodes),
        "warnings": warnings,
        "header_fields": fields,
    }


def parse_status(parse: dict) -> str:
    if parse["detected_count"] == 0:
        return "failed"
    # Ignore purely informational warnings so status evaluates as 'ok' / 'complete'
    critical_warnings = [
        w for w in parse.get("warnings", [])
        if w.get("code") in ("missing_episodes", "unreadable_episode", "duplicate_episodes")
    ]
    return "partial" if critical_warnings else "ok"


def split_genre(raw: str | None) -> tuple[str | None, str | None]:
    parts = [
        p.strip()
        for p in re.split(r"\s*[/,&+|]\s*", raw or "")
        if p.strip()
    ]
    if not parts:
        return None, None
    return parts[0], (" / ".join(parts[1:]) or None)


def build_declared(
    genre_raw: str | None, subgenre_raw: str | None, source: str
) -> dict | None:
    primary, secondary = split_genre(genre_raw)
    sub = (subgenre_raw or "").strip() or None
    if not (primary or sub):
        return None
    return {
        "primary": primary,
        "secondary": secondary,
        "subgenre": sub,
        "source": source,
    }


def marked_text(text: str, parse: dict) -> str:
    """Episode bodies with [E03-S02] markers, for the AI."""
    lines = text.split("\n")
    out = []
    for ep in parse["episodes"]:
        out.append(f"=== [{ep['id']}] EPISODE {ep['number']} {ep['title']} ===")
        scene_at = {s["start_line"]: s["id"] for s in ep["scenes"]}
        first_content_line = ep["start_line"]
        for ln in range(first_content_line, ep["end_line"] + 1):
            if ln in scene_at:
                out.append(f"[{scene_at[ln]}]")
            out.append(lines[ln - 1])
    return "\n".join(out)


def episode_text(text: str, ep: dict) -> str:
    return text[ep["char_start"] : ep["char_end"]]