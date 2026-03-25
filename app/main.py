from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import build_session_factory, init_db
from app.routers.web import router as web_router


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(title='BuildCRM Ready', version='1.0.0')
    engine, SessionLocal = build_session_factory(database_url)
    init_db(engine)
    app.state.engine = engine
    app.state.SessionLocal = SessionLocal
    app.mount('/static', StaticFiles(directory='app/static'), name='static')
    app.include_router(web_router)
    return app


app = create_app()
