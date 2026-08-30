"""Understanding — turning a sentence into an intent Atlas can act on.

With an ``ANTHROPIC_API_KEY`` configured, the chat runs on Claude: the model
reads the request in context of the live process catalogue and returns a
structured reading (intent, which process, a title). Without a key — or on
any API failure — it falls back to the deterministic keyword matcher, so the
demo still runs fully offline.

Routing stays deterministic either way. The model only interprets the
sentence; ``routing.resolve`` decides who is accountable, exactly as before.
That split is the point of the product: the agent's decisions are explainable
because they come from the responsibility graph, not from the LLM.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional

from sqlalchemy.orm import Session

from .matching import match_departments, match_processes, matchable_text, suggest_title
from .models import Person, Process

LLM_MODEL = os.environ.get("ATLAS_LLM_MODEL", "claude-opus-5")

INTENTS = ("request", "inbox", "my_requests", "ooo", "about_person", "help")


@dataclass
class Understanding:
    intent: str
    process_id: int | None = None
    confidence: float = 0.0
    person_name: str | None = None
    title: str | None = None
    reply: str | None = None          # the assistant's own words, for help/small talk
    rationale: str = ""
    source: str = "keywords"          # "claude" or "keywords"
    contact_line: str = ""            # "no process fits, but this team covers it"


def llm_ready() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def understand(session: Session, text: str, actor: Person | None = None) -> Understanding:
    text = (text or "").strip()
    if not text:
        return Understanding(intent="help")
    if llm_ready():
        try:
            return _understand_llm(session, text, actor)
        except Exception:
            # Whatever went wrong upstream (auth, rate limit, network, refusal),
            # the person asked a question — answer it with the local matcher.
            pass
    return _understand_keywords(session, text)


# --- Claude ------------------------------------------------------------------

_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic

        # A chat turn should degrade fast, not hang: one retry, short timeout.
        _client = anthropic.Anthropic(timeout=25.0, max_retries=1)
    return _client


def _reading_model():
    from pydantic import BaseModel

    class Reading(BaseModel):
        intent: Literal[
            "request", "inbox", "my_requests", "ooo", "about_person", "help"
        ]
        process_id: Optional[int]
        person_name: Optional[str]
        title: Optional[str]
        reply: Optional[str]
        rationale: str

    return Reading


def _catalogue(session: Session) -> str:
    lines = []
    for p in session.query(Process).order_by(Process.id).all():
        keywords = ", ".join((p.keywords or "").split(",")[:8])
        lines.append(f"- id {p.id}: {p.name} ({p.category}) — {keywords}")
    return "\n".join(lines)


def _people_names(session: Session) -> str:
    return ", ".join(p.name for p in session.query(Person).order_by(Person.name).all())


def _system(session: Session) -> str:
    return (
        "You are Atlas, an internal assistant at an investment firm. People tell "
        "you what they need in plain language; you decide what they mean. You do "
        "NOT decide who handles it — a deterministic responsibility graph does "
        "that — so never invent an assignee.\n\n"
        "Classify the message into exactly one intent:\n"
        "- request: they need something done, approved, fixed, booked or granted "
        "(this includes 'email whoever owns X and ask for Y').\n"
        "- inbox: they ask what is sitting with THEM to action.\n"
        "- my_requests: they ask about requests THEY raised.\n"
        "- ooo: they ask who is out of office / away.\n"
        "- about_person: they ask who a specific person is or what they own.\n"
        "- help: greetings, questions about what you can do, or anything else — "
        "answer briefly in `reply`, in a warm, plain voice, and steer them to "
        "describing what they need.\n\n"
        "For a request, pick the best matching process id from the catalogue "
        "below, or null when nothing genuinely fits (do not force a bad match). "
        "Also write `title`: a short subject line for the request in the "
        "requester's words (e.g. 'Data room access — Project Falcon').\n"
        "For about_person, set `person_name` to the person's full name from the "
        "directory list.\n"
        "Always write `rationale`: one plain sentence explaining your reading, "
        "addressed to the requester ('This reads like an access request for…').\n\n"
        f"Process catalogue:\n{_catalogue(session)}\n\n"
        f"Directory: {_people_names(session)}"
    )


def _understand_llm(session: Session, text: str, actor: Person | None) -> Understanding:
    client = _get_client()
    Reading = _reading_model()
    who = f"(Asked by {actor.name}, {actor.title}.) " if actor else ""
    response = client.messages.parse(
        model=LLM_MODEL,
        max_tokens=1024,
        system=[{
            "type": "text",
            "text": _system(session),
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": who + text}],
        output_format=Reading,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("model refused")
    reading = response.parsed_output
    process_id = reading.process_id
    if process_id is not None and session.get(Process, process_id) is None:
        process_id = None  # the model must not invent catalogue entries
    return Understanding(
        intent=reading.intent,
        process_id=process_id,
        confidence=90.0 if process_id is not None else 0.0,
        person_name=reading.person_name,
        title=reading.title or suggest_title(text, None),
        reply=reading.reply,
        rationale=reading.rationale,
        source="claude",
    )


# --- deterministic fallback --------------------------------------------------

_INBOX_CUES = ("sitting with me", "my inbox", "assigned to me", "my queue", "what do i owe")
_MINE_CUES = ("my requests", "i raised", "i asked for", "status of my")
_OOO_CUES = ("out of office", "who is away", "who's away", "on leave", "on holiday")
_HELP_CUES = ("help", "what can you do", "how do you work", "hello", "hi ", "hey")


def _understand_keywords(session: Session, text: str) -> Understanding:
    lower = f" {text.lower().strip()} "
    if any(cue in lower for cue in _INBOX_CUES):
        return Understanding(intent="inbox", rationale="You asked what's waiting on you.")
    if any(cue in lower for cue in _MINE_CUES):
        return Understanding(intent="my_requests", rationale="You asked about requests you raised.")
    if any(cue in lower for cue in _OOO_CUES):
        return Understanding(intent="ooo", rationale="You asked who is away.")

    for person in session.query(Person).all():
        first = person.name.split()[0].lower()
        if person.name.lower() in lower or (
            f"who is {first}" in lower or f"about {first}" in lower
        ):
            return Understanding(
                intent="about_person", person_name=person.name,
                rationale=f"You asked about {person.name}.",
            )

    if lower.strip() in ("help", "hello", "hi", "hey") or any(
        cue in lower for cue in _HELP_CUES[1:3]
    ):
        return Understanding(intent="help")

    matches = match_processes(session, matchable_text(text), limit=3)
    top = matches[0] if matches and matches[0].confidence >= 25 else None
    contact_line = ""
    if top is None:
        contacts = match_departments(session, text, limit=1)
        contact = contacts[0] if contacts and contacts[0].confidence >= 25 else None
        if contact and contact.person_name:
            contact_line = (
                f"No request type covers this, but it reads like "
                f"{contact.department_name} — {contact.person_name}, "
                f"{contact.person_title}, {contact.reason}."
            )
    return Understanding(
        intent="request",
        process_id=top.process_id if top else None,
        confidence=top.confidence if top else 0.0,
        title=suggest_title(text, top.process_name if top else None),
        rationale=top.why() if top else
        "Nothing in the catalogue matched with usable confidence.",
        contact_line=contact_line,
        source="keywords",
    )
