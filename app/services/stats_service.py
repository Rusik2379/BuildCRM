from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.project import Project
from app.models.task import Task


class StatsService:
    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        return {
            "clients": db.query(func.count(Client.id)).scalar() or 0,
            "projects": db.query(func.count(Project.id)).scalar() or 0,
            "tasks": db.query(func.count(Task.id)).scalar() or 0,
        }
