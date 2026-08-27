"""SQLite engine + session plumbing.

The Streamlit script thread and the background agent thread both touch the same
file, so the engine is configured for cross-thread use with WAL journaling and a
generous busy timeout. Every unit of work gets its own short-lived session.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from . import config
from .models import Base, Setting

_engine: Engine | None = None
_session_factory: sessionmaker | None = None
_engine_lock = threading.Lock()

# Serialises writers. SQLite handles this itself, but taking the lock in-process
# keeps the demo free of "database is locked" hiccups when the agent thread and
# a user click land at the same moment.
write_lock = threading.RLock()


def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is not None:
        return _engine
    with _engine_lock:
        if _engine is None:
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            engine = create_engine(
                config.DB_URL,
                future=True,
                connect_args={"check_same_thread": False, "timeout": 30},
            )

            @event.listens_for(engine, "connect")
            def _set_sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover
                cur = dbapi_connection.cursor()
                cur.execute("PRAGMA journal_mode=WAL")
                cur.execute("PRAGMA synchronous=NORMAL")
                cur.execute("PRAGMA foreign_keys=ON")
                cur.close()

            _engine = engine
            _session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return _engine


def get_session() -> Session:
    get_engine()
    assert _session_factory is not None
    return _session_factory()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Read/write session that commits on success and always closes."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all() -> None:
    Base.metadata.create_all(get_engine())


def drop_all() -> None:
    Base.metadata.drop_all(get_engine())


def schema_is_current() -> bool:
    """True when the file on disk matches the models this code expects.

    ``create_all`` creates missing tables but never alters existing ones, so a
    database written before a column was added stays silently short of it and
    the first query blows up. Comparing the columns is enough here: the data is
    seeded demo data, so a mismatch is fixed by reseeding rather than migrating.
    """
    from sqlalchemy import inspect

    inspector = inspect(get_engine())
    existing = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing:
            continue
        on_disk = {c["name"] for c in inspector.get_columns(table.name)}
        if not {c.name for c in table.columns} <= on_disk:
            return False
    return True


def database_is_seeded() -> bool:
    """True when the schema is current and carries the seeded demo firm."""
    from sqlalchemy import inspect

    engine = get_engine()
    inspector = inspect(engine)
    if "people" not in inspector.get_table_names():
        return False
    if not schema_is_current():
        return False
    with session_scope() as session:
        return session.scalar(select(Setting).where(Setting.key == "seeded_at")) is not None


# --- settings helpers -------------------------------------------------------


def get_setting(session: Session, key: str, default: str | None = None) -> str | None:
    row = session.get(Setting, key)
    return row.value if row is not None else default


def set_setting(session: Session, key: str, value: str) -> None:
    row = session.get(Setting, key)
    if row is None:
        session.add(Setting(key=key, value=str(value)))
    else:
        row.value = str(value)
