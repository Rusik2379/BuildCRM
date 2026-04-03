from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from fastapi import Request
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()


def _load_env_file() -> None:
    env_path = Path('.env')
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_file()


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


def _ensure_runtime_columns(engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if 'orders' in tables:
        columns = {col['name'] for col in inspector.get_columns('orders')}
        needed_columns = {
            'client_source_snapshot': "ALTER TABLE orders ADD COLUMN client_source_snapshot VARCHAR(100)",
            'document_issued': "ALTER TABLE orders ADD COLUMN document_issued BOOLEAN DEFAULT 0",
            'document_name': "ALTER TABLE orders ADD COLUMN document_name VARCHAR(120)",
            'markup_percent': "ALTER TABLE orders ADD COLUMN markup_percent NUMERIC(8, 2) DEFAULT 0",
        }
        with engine.begin() as conn:
            for col_name, statement in needed_columns.items():
                if col_name not in columns:
                    conn.execute(text(statement))


def init_db(engine) -> None:
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _ensure_runtime_columns(engine)


def db_dependency(request: Request) -> Generator[Session, None, None]:
    db = request.app.state.SessionLocal()
    try:
        yield db
    finally:
        db.close()
