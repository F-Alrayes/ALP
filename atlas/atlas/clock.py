"""The simulated clock.

Every timestamp Atlas reads or writes goes through :func:`now`. Business logic
must never call ``datetime.now()`` itself — this module is the only place in the
codebase allowed to touch the wall clock, and it adds the offset stored in
``settings.clock_offset_seconds`` before handing the value back.

Advancing the offset is what makes the demo possible: the background agent
evaluates its 48h / 24h rules against simulated time, so behaviour that would
take days in production executes in seconds.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .db import get_setting, session_scope, set_setting, write_lock

OFFSET_KEY = "clock_offset_seconds"


def _wall_clock() -> datetime:
    """The one and only wall-clock read in Atlas. Naive UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def get_offset(session: Session) -> timedelta:
    raw = get_setting(session, OFFSET_KEY, "0")
    try:
        return timedelta(seconds=float(raw or 0))
    except (TypeError, ValueError):
        return timedelta(0)


def now(session: Session | None = None) -> datetime:
    """Current simulated time."""
    if session is not None:
        return _wall_clock() + get_offset(session)
    with session_scope() as own:
        return _wall_clock() + get_offset(own)


def advance(hours: float) -> datetime:
    """Push simulated time forward. Returns the new simulated 'now'."""
    with write_lock, session_scope() as session:
        offset = get_offset(session)
        offset += timedelta(hours=hours)
        set_setting(session, OFFSET_KEY, str(int(offset.total_seconds())))
        return _wall_clock() + offset


def reset() -> datetime:
    """Snap simulated time back to the wall clock."""
    with write_lock, session_scope() as session:
        set_setting(session, OFFSET_KEY, "0")
    return _wall_clock()


def offset_hours() -> float:
    with session_scope() as session:
        return round(get_offset(session).total_seconds() / 3600.0, 2)


# --- formatting helpers -----------------------------------------------------


def fmt(dt: datetime | None, with_time: bool = True) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d %b %Y, %H:%M") if with_time else dt.strftime("%d %b %Y")


def humanize_delta(delta: timedelta | None) -> str:
    if delta is None:
        return "—"
    seconds = int(delta.total_seconds())
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{sign}{days}d {hours}h"
    if hours:
        return f"{sign}{hours}h {minutes}m"
    return f"{sign}{minutes}m"


def ago(dt: datetime | None, reference: datetime | None = None) -> str:
    if dt is None:
        return "—"
    reference = reference or now()
    return f"{humanize_delta(reference - dt)} ago"
