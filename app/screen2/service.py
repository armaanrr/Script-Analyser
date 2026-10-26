import hashlib
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.llm import get_provider
from app.config import settings
from app.screen2 import classification, compare, parser, models


class Screen2ServiceError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message


async def run_screen2_analysis(
    db: Session,
    concept_id: int,
    title: str,
    filename: str,
    raw_text: str,
    expected_episodes: int | None,
    scene_marking: str,
    scene_allocation: str,
    target_scenes_per_episode: int,
    user_name: str
) -> dict:
    # 1. Normalize raw screenplay text & parse structure
    norm_text = parser.normalize_text(raw_text)
    text_hash = parser.sha256(norm_text)
    parsed_structure = parser.parse_screenplay(norm_text, expected=expected_episodes)
    parse_status = parser.parse_status(parsed_structure)

    # If the producer confirms that scene headings are absent, create balanced
    # provisional text sections for review. This does not alter raw_text or
    # claim that these are verified dramatic scene boundaries.
    scene_marking = scene_marking if scene_marking in ("marked", "unmarked") else "unmarked"
    target_count = max(1, min(int(target_scenes_per_episode or 3), 100))
    if scene_marking == "unmarked" and int(parsed_structure.get("scene_count", 0)) == 0:
        lines = norm_text.split("\\n")
        for ep in parsed_structure.get("episodes", []):
            start, end = int(ep["start_line"]), int(ep["end_line"])
            # Exclude the inferred episode label line when present.
            body_start = start + 1 if str(ep.get("title", "")).startswith("Full screenplay (inferred") else start
            body_lines = list(range(body_start, end + 1))
            body_lines = [n for n in body_lines if lines[n - 1].strip()]
            if not body_lines:
                continue
            count = target_count if scene_allocation == "fixed" else min(3, max(1, len(body_lines)))
            count = min(count, len(body_lines))
            chunks = []
            for idx in range(count):
                a = idx * len(body_lines) // count
                b = (idx + 1) * len(body_lines) // count
                chunk_lines = body_lines[a:b]
                if not chunk_lines:
                    continue
                chunks.append({
                    "id": f"{ep['id']}-S{len(chunks) + 1:02d}",
                    "heading": f"Provisional text section {len(chunks) + 1} (review required)",
                    "start_line": chunk_lines[0],
                    "end_line": chunk_lines[-1],
                    "provisional": True,
                })
            ep["scenes"] = chunks
            ep["scene_count"] = len(chunks)
            ep["scene_boundaries_provisional"] = True
        parsed_structure["scene_count"] = sum(int(ep.get("scene_count", 0)) for ep in parsed_structure.get("episodes", []))
        parsed_structure.setdefault("warnings", []).append({
            "code": "scene_boundaries_provisional",
            "episode_id": None,
            "message": "No scene headings were detected. The screenplay text has been divided into provisional text sections for review; these are not verified dramatic scene boundaries."
        })

    # Store the producer's structural intent alongside the deterministic parse.
    # Target scenes are guidance, not a hard truncation limit: all extracted scenes remain in the episode.
    structure_settings = {
        "mode": "episodes",
        "scene_marking": scene_marking,
        "episode_count": expected_episodes or parsed_structure.get("detected_count", 1) or 1,
        "scene_allocation": scene_allocation if scene_allocation in ("auto", "fixed") else "auto",
        "target_scenes_per_episode": max(1, min(int(target_scenes_per_episode or 3), 100)),
        "max_episode_duration_seconds": 180,
        "user_confirmed": bool(expected_episodes),
    }
    parsed_structure["structure_settings"] = structure_settings
    if structure_settings["scene_allocation"] == "fixed":
        expected_scene_total = structure_settings["episode_count"] * structure_settings["target_scenes_per_episode"]
        actual_scene_total = int(parsed_structure.get("scene_count", 0))
        if actual_scene_total != expected_scene_total:
            parsed_structure.setdefault("warnings", []).append({
                "code": "scene_target_mismatch",
                "episode_id": None,
                "message": f"The target is {structure_settings['target_scenes_per_episode']} scenes per episode ({expected_scene_total} total for {structure_settings['episode_count']} episode(s)), but {actual_scene_total} scenes were extracted. All scenes are retained; review the target or episode count."
            })

    detected_eps = parsed_structure["detected_count"] if parsed_structure["detected_count"] > 0 else (expected_episodes or 1)

    # 2. Extract script-declared genre from header lines if available
    declared = parser.build_declared(
        genre_raw=parsed_structure.get("header_fields", {}).get("genre"),
        subgenre_raw=parsed_structure.get("header_fields", {}).get("subgenre"),
        source="script_header"
    )

    # 3. Auto-increment screenplay version_no to prevent SQLite unique constraint errors
    max_ver = db.scalar(
        select(func.max(models.Screenplay.version_no)).where(models.Screenplay.concept_id == concept_id)
    )
    next_version = (max_ver or 0) + 1

    # 4. Store Screenplay record
    screenplay_rec = models.Screenplay(
        concept_id=concept_id,
        version_no=next_version,
        title=title,
        filename=filename,
        source_type="upload",
        text_sha256=text_hash,
        raw_text=norm_text,
        expected_episodes=expected_episodes,
        parse=parsed_structure,
        parse_status=parse_status,
        declared=declared,
        uploaded_by=user_name
    )
    db.add(screenplay_rec)
    db.flush()

    # 5. Build a deterministic prompt and cache key. Re-uploading the same screenplay
    # with the same provider/model/prompt version reuses the prior classification.
    if parsed_structure.get("episodes"):
        script_for_ai = parser.marked_text(norm_text, parsed_structure)
    else:
        script_for_ai = norm_text[:100000]

    user_prompt = classification.build_user_prompt(script_for_ai, detected_eps)
    provider_name = "openai" if settings.llm_provider == "openai" else "gemini"
    provider_model = (settings.openai_model if provider_name == "openai" else settings.gemini_model)
    cache_material = "|".join((
        provider_name,
        provider_model or "default-model",
        classification.PROMPT_VERSION,
        user_prompt,
        str(structure_settings),
    ))
    cache_key = hashlib.sha256(cache_material.encode("utf-8")).hexdigest()
    cached_run = db.scalar(
        select(models.ModuleRun)
        .where(
            models.ModuleRun.module == classification.MODULE,
            models.ModuleRun.cache_key == cache_key,
            models.ModuleRun.status == "ok",
        )
        .order_by(models.ModuleRun.created_at.desc())
        .limit(1)
    )

    cache_hit = cached_run is not None and bool(cached_run.result)
    if cache_hit:
        ai_data = dict(cached_run.result)
        module_run = models.ModuleRun(
            screenplay_id=screenplay_rec.id,
            module=classification.MODULE,
            cache_key=cache_key,
            provider=provider_name,
            model=provider_model or "default-model",
            prompt_version=classification.PROMPT_VERSION,
            status="ok",
            result=ai_data,
            input_tokens=0,
            output_tokens=0,
            created_by=user_name,
        )
        db.add(module_run)
    else:
        try:
            # Instantiate the API client only on a cache miss. This supports Gemini now
            # and OpenAI later via LLM_PROVIDER without changing this screen.
            provider = get_provider()
            from app.screen2.classification import GenreAssessment
            llm_result = provider.generate_json(
                classification.SYSTEM,
                user_prompt,
                GenreAssessment,
            )
            ai_data = llm_result.parsed.model_dump()
            module_run = models.ModuleRun(
                screenplay_id=screenplay_rec.id,
                module=classification.MODULE,
                cache_key=cache_key,
                provider=provider.name,
                model=provider.model,
                prompt_version=classification.PROMPT_VERSION,
                status="ok",
                result=ai_data,
                input_tokens=llm_result.input_tokens,
                output_tokens=llm_result.output_tokens,
                created_by=user_name,
            )
            db.add(module_run)
        except Exception as e:
            module_run = models.ModuleRun(
                screenplay_id=screenplay_rec.id,
                module=classification.MODULE,
                cache_key=cache_key,
                provider=provider_name,
                model=provider_model or "default-model",
                prompt_version=classification.PROMPT_VERSION,
                status="failed",
                error=str(e),
                created_by=user_name,
            )
            db.add(module_run)
            db.commit()
            raise Screen2ServiceError(500, f"AI classification failed: {str(e)}")

    # 7. Verify evidence quotes against source text
    if "evidence" in ai_data and isinstance(ai_data["evidence"], list):
        ai_data["evidence"] = compare.verify_evidence(ai_data["evidence"], parsed_structure, norm_text)

    # 8. Compare declared vs AI detected classification
    comp_result = compare.compare_classification(ai_data, declared)

    # 9. Persist the screenplay and its module-run record (cached or fresh).
    db.commit()

    # Dynamic status from structural parsing
    status_label = "Complete" if parse_status in ("ok", "complete") else parse_status.replace("_", " ").title()

    # Derive full screenplay score dynamically if present from AI evaluation; otherwise None until Screen 03 ratings compute it
    score_value = ai_data.get("full_score") or ai_data.get("score")

    return {
        "screenplay_id": screenplay_rec.id,
        "title": title,
        "status": status_label,
        "full_score": float(score_value) if score_value is not None else None,
        "ai_primary_genre": ai_data.get("primary_genre", ""),
        "ai_secondary_genre_elements": ai_data.get("secondary_genre_elements", []),
        "ai_subgenre": ai_data.get("subgenre", ""),
        "confidence": str(ai_data.get("confidence", "")).capitalize(),
        "ambiguity_note": ai_data.get("ambiguity_note"),
        "genre_match": comp_result["overall"].replace("_", " ").title(),
        "declared_genre": (declared or {}).get("primary"),
        "declared_subgenre": (declared or {}).get("subgenre"),
        "detected_episodes": detected_eps,
        "expected_episodes": expected_episodes,
        "episode_structure_settings": structure_settings,
        "word_count": parsed_structure.get("word_count", 0),
        "scene_count": parsed_structure.get("scene_count", 0),
        "parse_status": parse_status,
        "parse_warnings": parsed_structure.get("warnings", []),
        "story_engine": ai_data.get("story_engine", ""),
        "central_conflict": ai_data.get("central_conflict", ""),
        "relationship_dynamics": ai_data.get("relationship_dynamics", ""),
        "tone": ai_data.get("tone", ""),
        "narrative_patterns": ai_data.get("narrative_patterns", []),
        "alternative_classifications": ai_data.get("alternative_classifications", []),
        "evidence": ai_data.get("evidence", []),
        "provider": provider_name,
        "model": provider_model or "default-model",
        "cache_hit": cache_hit,
        "input_tokens": 0 if cache_hit else module_run.input_tokens,
        "output_tokens": 0 if cache_hit else module_run.output_tokens
    }