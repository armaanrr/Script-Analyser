# Screen 1: Stage 1 Concept Submission & Approval

## Run
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add GEMINI_API_KEY; keep .env out of git
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --reload # open http://localhost:8000
pytest                        # scoring tests
```

## What it does
- Intake form for the concept (no screenplay needed). Concept-only guard rejects pasted scripts.
- One LLM call returns structured JSON: originality, comparables, taxonomy, audience lens, micro-drama, six 0-10 ratings.
- The backend calculates points (30/20/15/20/10/5 = 100). Missing rating = "Incomplete", never zero.
- Traction metrics come only from the knowledge base. Now: "Unavailable". Score is labelled "Provisional" until real data exists.
- Decisions (approve / revise / hold / reject) are append-only, with reviewer, role, rationale, timestamp, concept version.
- Each edit creates a new concept version. Analyses are cached per version + provider + model + prompt version.

## Switching later
- OpenAI: set LLM_PROVIDER=openai, OPENAI_API_KEY, OPENAI_MODEL. Only app/llm/ is involved.
- Knowledge base: implement `KnowledgeBase` in app/knowledge_base.py (reference_titles, traction_for).

## Proposed / configurable (needs your approval)
- Provisional status while traction is unverified.
- Decision roles (DECISION_ROLES=owner,producer).
- No score bands or auto-approve thresholds, as the blueprint defines none.

## Must replace before real use
- `current_user` in app/routes.py trusts client headers. Wire it to your real login and access-request flow.
