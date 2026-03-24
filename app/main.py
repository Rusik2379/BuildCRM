from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.clients import router as clients_router
from app.api.routes.projects import router as projects_router
from app.api.routes.stats import router as stats_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings
from app.core.db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(stats_router)


@app.get("/")
def root():
    return {"message": f"{settings.app_name} API is running"}
