"""The Atlas routing agent, built on Google ADK 2.x.

An ADK ``LlmAgent`` (Gemini) interprets what the requester wrote. It is
grounded in the engine through function tools — the live process catalogue,
the deterministic rapidfuzz ranker, the directory — and it must finish by
calling exactly one *commit tool* (``record_route`` / ``record_intent``),
which is how the structured reading travels back: ADK disables tools when
``output_schema`` is set, so the tool call *is* the output channel. The
committed reading then flows through :func:`atlas.brain._from_reading`,
which validates the process id against the catalogue and attaches the
deterministic ranked alternates that back the "Not this" fallback.

Routing stays deterministic either way: the agent only interprets the
sentence; ``routing.resolve`` still decides who is accountable from the
responsibility graph.

Configuration:
    GOOGLE_API_KEY / GEMINI_API_KEY   enables the agent (Gemini API)
    ATLAS_ADK_MODEL                   model id, default ``gemini-3.5-flash-lite``
"""

from __future__ import annotations

import asyncio
import os
import threading

from sqlalchemy.orm import Session

from ..db import session_scope
from ..matching import match_processes, matchable_text
from ..models import Person, Process

APP_NAME = "atlas"
# gemini-3.5-flash-lite: fast, and its free-tier daily quota is far larger
# than the flagship's 20 requests/day — a chat demo can actually run on it.
ADK_MODEL = os.environ.get("ATLAS_ADK_MODEL", "gemini-3.5-flash-lite")
# Wall-clock ceiling for one whole chat turn through the agent (all model
# calls included). Past it the provider chain answers and says why.
ADK_TURN_TIMEOUT = float(os.environ.get("ATLAS_ADK_TIMEOUT", "30"))

_INSTRUCTION = (
    "You are Atlas, an internal assistant at an investment firm. People tell "
    "you what they need in plain language; you decide what they mean. You do "
    "NOT decide who handles it — a deterministic responsibility graph does "
    "that — so never invent an assignee.\n\n"
    "Work every message the same way:\n"
    "1. If it reads like a request (something to be done, approved, fixed, "
    "booked or granted — everyday asks like booking leave, claiming expenses "
    "or getting equipment are requests too), call `score_processes` with the "
    "message to see how "
    "the deterministic ranker scores the catalogue, and `list_processes` if "
    "you need the full picture. Pick the best process id, or null when "
    "nothing genuinely fits — do not force a bad match.\n"
    "2. Finish by calling exactly ONE commit tool:\n"
    "   - `record_route` for a request — set `confidence` 0-100 (90+ only "
    "for unmistakable matches; under 40 means you should commit null "
    "instead), a short `title` in the requester's words (e.g. 'Data room "
    "access — Project Falcon'), and a one-sentence `rationale` addressed to "
    "the requester ('This reads like an access request for…').\n"
    "   - `record_intent` for everything else: `inbox` (what is sitting "
    "with THEM to action), `my_requests` (requests THEY raised), `ooo` "
    "(who is away), `about_person` (set `person_name` to a full name from "
    "`list_people`), or `help` (greetings / what-can-you-do — put a warm, "
    "brief answer in `reply` and steer them to describing what they need).\n"
    "Never answer with prose alone; the commit tool call is your answer."
)


def adk_ready() -> bool:
    return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))


# --- tools -------------------------------------------------------------------
# Tools open their own database scope: the agent outlives any one request's
# session, and ADK calls them from its own event loop.


def list_processes() -> list[dict]:
    """List the live process catalogue: id, name, category, keywords."""
    with session_scope() as db:
        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "keywords": (p.keywords or "").split(",")[:8],
            }
            for p in db.query(Process).order_by(Process.id).all()
        ]


def score_processes(query: str) -> list[dict]:
    """Score the catalogue against a request with the deterministic ranker.

    Returns the top matches as {process_id, name, confidence 0-100, why}.
    """
    with session_scope() as db:
        return [
            {
                "process_id": m.process_id,
                "name": m.process_name,
                "confidence": m.confidence,
                "why": m.why(),
            }
            for m in match_processes(db, matchable_text(query or ""), limit=5)
        ]


def list_people() -> list[str]:
    """List every full name in the directory."""
    with session_scope() as db:
        return [p.name for p in db.query(Person).order_by(Person.name).all()]


def record_route(
    process_id: int | None, confidence: int, title: str, rationale: str
) -> dict:
    """Commit the final reading of a REQUEST. Call exactly once, last."""
    return {"status": "recorded"}


def record_intent(
    intent: str,
    rationale: str,
    person_name: str | None = None,
    reply: str | None = None,
) -> dict:
    """Commit a non-request reading (inbox / my_requests / ooo /
    about_person / help). Call exactly once, last."""
    return {"status": "recorded"}


# --- agent & runner ----------------------------------------------------------

_runner = None
_lock = threading.Lock()
_sessions: set[str] = set()


def build_agent():
    """Construct the ADK agent (no network happens here)."""
    from google.adk.agents import LlmAgent
    from google.adk.models.google_llm import Gemini
    from google.genai import types

    # Cap the client's own retries: when Gemini is down or out of quota a
    # chat turn should fail fast and surface the reason, not sit in backoff.
    model = Gemini(
        model=ADK_MODEL,
        retry_options=types.HttpRetryOptions(initial_delay=1, attempts=2),
    )
    return LlmAgent(
        name="atlas_router",
        model=model,
        description="Reads a request and commits a routing decision.",
        instruction=_INSTRUCTION,
        tools=[list_processes, score_processes, list_people,
               record_route, record_intent],
    )


def _get_runner():
    global _runner
    with _lock:
        if _runner is None:
            from google.adk.runners import InMemoryRunner

            _runner = InMemoryRunner(agent=build_agent(), app_name=APP_NAME)
    return _runner


def _run_async(coro):
    """Run a coroutine whether or not this thread already owns a loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # A live loop on this thread (rare under Streamlit): use a fresh one
    # on a worker thread so we never re-enter the running loop.
    result: dict = {}

    def _target():
        result["value"] = asyncio.run(coro)

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=60)
    return result.get("value")


def _ensure_session(runner, user_id: str, session_id: str) -> None:
    if session_id in _sessions:
        return
    existing = _run_async(
        runner.session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
    )
    if existing is None:
        _run_async(
            runner.session_service.create_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )
        )
    _sessions.add(session_id)


def adk_understand(session: Session, text: str, actor: Person | None):
    """Run one chat turn through the ADK agent; return an Understanding.

    Returns None when the agent produced nothing usable — the caller's
    provider chain then falls through to the next engine.
    """
    from google.genai import types

    from ..brain import INTENTS, _from_reading, _reading_model

    runner = _get_runner()
    user_id = f"person-{actor.id}" if actor else "person-0"
    session_id = f"chat-{user_id}"
    _ensure_session(runner, user_id, session_id)

    who = f"(Asked by {actor.name}, {actor.title}.) " if actor else ""
    message = types.Content(role="user", parts=[types.Part(text=who + text)])

    from google.adk.agents.run_config import RunConfig

    committed: dict | None = None
    prose: list[str] = []

    # Two hard ceilings per turn: max_llm_calls stops a looping agent, and a
    # wall-clock deadline stops a hanging or crawling API — either way the
    # chat turn ends and the caller surfaces the reason instead of spinning.
    def _drive() -> None:
        nonlocal committed
        for event in runner.run(
            user_id=user_id, session_id=session_id, new_message=message,
            run_config=RunConfig(max_llm_calls=8),
        ):
            for call in event.get_function_calls() or []:
                if call.name in ("record_route", "record_intent"):
                    committed = {"tool": call.name, **dict(call.args or {})}
            if event.is_final_response() and event.content and event.content.parts:
                prose.extend(
                    part.text for part in event.content.parts
                    if getattr(part, "text", None)
                )

    failure: list[BaseException] = []

    def _target() -> None:
        try:
            _drive()
        except BaseException as exc:  # carried to the caller's thread
            failure.append(exc)

    worker = threading.Thread(target=_target, daemon=True)
    worker.start()
    worker.join(timeout=ADK_TURN_TIMEOUT)
    if worker.is_alive():
        raise TimeoutError(
            f"Gemini turn timed out after {ADK_TURN_TIMEOUT:.0f}s ({ADK_MODEL})"
        )
    if failure:
        raise failure[0]

    Reading = _reading_model()
    if committed is None:
        if not prose:
            return None
        # The model answered in words despite the brief — surface them.
        reading = Reading(
            intent="help", process_id=None, confidence=0, person_name=None,
            title=None, reply=" ".join(prose).strip(), rationale="",
        )
        return _from_reading(session, text, reading, source="gemini (adk)")

    if committed["tool"] == "record_route":
        raw_id = committed.get("process_id")
        reading = Reading(
            intent="request",
            process_id=int(raw_id) if raw_id is not None else None,
            confidence=int(committed.get("confidence") or 0),
            person_name=None,
            title=committed.get("title"),
            reply=None,
            rationale=committed.get("rationale") or "",
        )
    else:
        intent = committed.get("intent")
        reading = Reading(
            intent=intent if intent in INTENTS else "help",
            process_id=None,
            confidence=0,
            person_name=committed.get("person_name"),
            title=None,
            reply=committed.get("reply"),
            rationale=committed.get("rationale") or "",
        )
    return _from_reading(session, text, reading, source="gemini (adk)")
