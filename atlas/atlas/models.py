"""SQLAlchemy models — the responsibility graph and the request lifecycle."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)

    people: Mapped[list["Person"]] = relationship(back_populates="department")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Department {self.name}>"


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(160))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"))
    email: Mapped[str] = mapped_column(String(160))
    is_ooo: Mapped[bool] = mapped_column(Boolean, default=False)
    ooo_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    department: Mapped[Department | None] = relationship(back_populates="people")
    manager: Mapped["Person | None"] = relationship(remote_side="Person.id", backref="reports")

    @property
    def initials(self) -> str:
        parts = [p for p in self.name.split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Person {self.name}>"


class Process(Base):
    __tablename__ = "processes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), default="General")
    keywords: Mapped[str] = mapped_column(Text, default="")

    responsibilities: Mapped[list["Responsibility"]] = relationship(
        back_populates="process", cascade="all, delete-orphan"
    )

    @property
    def keyword_list(self) -> list[str]:
        return [k.strip().lower() for k in (self.keywords or "").split(",") if k.strip()]

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Process {self.name}>"


class Responsibility(Base):
    """An edge in the responsibility graph: person --role--> process."""

    __tablename__ = "responsibilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    process_id: Mapped[int] = mapped_column(ForeignKey("processes.id"))
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    # one of: owner, approver, delegate, backup
    role: Mapped[str] = mapped_column(String(20))

    process: Mapped[Process] = relationship(back_populates="responsibilities")
    person: Mapped[Person] = relationship()

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Responsibility {self.role} p{self.process_id} -> {self.person_id}>"


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    process_id: Mapped[int | None] = mapped_column(ForeignKey("processes.id"), nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"), nullable=True)
    original_assignee_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(240))
    body: Mapped[str] = mapped_column(Text, default="")
    # one of: pending, acknowledged, in_progress, completed, escalated
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    last_action_at: Mapped[datetime] = mapped_column(DateTime)
    chase_count: Mapped[int] = mapped_column(Integer, default=0)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    requester: Mapped[Person] = relationship(foreign_keys=[requester_id])
    assignee: Mapped[Person | None] = relationship(foreign_keys=[assignee_id])
    original_assignee: Mapped[Person | None] = relationship(foreign_keys=[original_assignee_id])
    process: Mapped[Process | None] = relationship()

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Request #{self.id} {self.status}>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"), nullable=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    # one of: dispatch, chase, escalation, reroute, status_update
    type: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    read: Mapped[bool] = mapped_column(Boolean, default=False)

    request: Mapped[Request] = relationship()
    sender: Mapped[Person | None] = relationship(foreign_keys=[sender_id])
    recipient: Mapped[Person] = relationship(foreign_keys=[recipient_id])


class Event(Base):
    """Full audit trail. Powers the per-request timeline and the Agent Log."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int | None] = mapped_column(ForeignKey("requests.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(40), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime)

    request: Mapped[Request | None] = relationship()


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
