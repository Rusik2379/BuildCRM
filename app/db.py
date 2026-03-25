from __future__ import annotations

import os
from typing import Generator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()


def build_engine(database_url: str | None = None):
    url = database_url or os.getenv('DATABASE_URL', 'sqlite:///./buildcrm_ready.db')
    kwargs: dict = {}
    if url.startswith('sqlite'):
        kwargs['connect_args'] = {'check_same_thread': False}
    return create_engine(url, future=True, **kwargs)


def build_session_factory(database_url: str | None = None):
    engine = build_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return engine, SessionLocal


def init_db(engine) -> None:
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def db_dependency(request: Request) -> Generator[Session, None, None]:
    db = request.app.state.SessionLocal()
    try:
        yield db
    finally:
        db.close()
