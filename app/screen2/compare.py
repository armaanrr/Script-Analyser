"""Heuristic comparison of declared vs AI classification, and quote verification. Pure Python.

The comparison is deliberately simple and deterministic. It only suggests Match / Partial /
Difference; a human confirms the final labels."""
import re
import unicodedata

from .parser import episode_text

SYNONYMS = {"romantic": "romance", "comedic": "comedy", "thrilling": "thriller", "dramatic": "drama",
            "familial": "family", "vengeance": "revenge"}
GENERIC = {"and", "the", "of", "a", "drama", "series", "show", "story"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = re.sub(r"[\u2018\u2019\u201c\u201d\"'`]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,…-–—")


def _tokens(s: str) -> set[str]:
    raw = [SYNONYMS.get(t, t) for t in re.findall(r"[a-z0-9\u0900-\u097f]+", norm(s))]
    specific = {t for t in raw if t not in GENERIC}
    return specific or set(raw)


def field_status(ai_value: str | None, declared: str | None, ai_alternatives: list[str] | None = None) -> dict:
    if not (declared or "").strip():
        return {"status": "not_specified", "note": "Not specified in the script or metadata."}
    ta, td = _tokens(ai_value or ""), _tokens(declared)
    if not ta or not td:
        return {"status": "difference", "note": None}
    if ta == td:
        return {"status": "match", "note": None}
    if td <= ta or ta <= td:
        return {"status": "partial", "note": "One label contains the other."}
    if len(ta & td) / len(ta | td) >= 0.34:
        return {"status": "partial", "note": "Labels overlap."}
    for alt in ai_alternatives or []:
        if td <= _tokens(alt):
            return {"status": "partial", "note": "Declared label matches an AI-detected secondary element."}
    return {"status": "difference", "note": None}


def compare_classification(ai: dict, declared: dict | None) -> dict:
    """ai: classification dict (primary_genre, subgenre, secondary_genre_elements)."""
    if not declared:
        return {"overall": "not_specified", "primary": None, "subgenre": None}
    alts = ai.get("secondary_genre_elements") or []
    prim = field_status(ai.get("primary_genre"), declared.get("primary"), alts)
    sub = field_status(ai.get("subgenre"), declared.get("subgenre"), alts)
    specified = [x["status"] for x in (prim, sub) if x["status"] != "not_specified"]
    if not specified:
        overall = "not_specified"
    elif all(s == "match" for s in specified):
        overall = "match"
    elif all(s == "difference" for s in specified):
        overall = "difference"
    else:
        overall = "partial"
    return {"overall": overall, "primary": prim, "subgenre": sub}


def verify_evidence(items: list[dict], parse: dict, text: str) -> list[dict]:
    """Every quote must exist verbatim in the cited episode. Unverified items are kept but flagged."""
    eps = {e["id"]: e for e in parse["episodes"]}
    out = []
    for it in items:
        it = dict(it)
        ep = eps.get(it.get("episode_id"))
        quote = norm(it.get("quote", ""))
        note = None
        if ep is None:
            note = "Episode id not found in the extracted screenplay."
        elif not quote:
            note = "No quote supplied."
        elif quote not in norm(episode_text(text, ep)):
            note = "Quote not found verbatim in that episode."
        if ep is not None and it.get("scene_id") and it["scene_id"] not in {s["id"] for s in ep["scenes"]}:
            it["scene_id"] = None
            note = note or "Scene id not found; reference limited to the episode."
            it["verified"] = quote != "" and quote in norm(episode_text(text, ep))
        else:
            it["verified"] = note is None
        it["verify_note"] = note
        out.append(it)
    return out
