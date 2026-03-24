from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401
from app.api.routes.auth import router as auth_router
from app.api.routes.clients import router as clients_router
from app.api.routes.products import router as products_router
from app.api.routes.projects import router as projects_router
from app.api.routes.requests import router as requests_router
from app.api.routes.stats import router as stats_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.web import router as web_router
from app.core.config import settings
from app.core.db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(web_router)
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(products_router)
app.include_router(projects_router)
app.include_router(requests_router)
app.include_router(tasks_router)
app.include_router(stats_router)
