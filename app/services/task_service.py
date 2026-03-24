from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus


class TaskService:
    @staticmethod
    def get_today_tasks(db: Session):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        return (
            db.query(Task)
            .filter(Task.due_date >= today, Task.due_date < tomorrow)
            .order_by(Task.due_date.asc())
            .all()
        )

    @staticmethod
    def update_status(db: Session, task_id: int, status: TaskStatus) -> Task | None:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        task.status = status
        db.commit()
        db.refresh(task)
        return task
