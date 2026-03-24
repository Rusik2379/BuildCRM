from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskUpdateStatus
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db_session)):
    return db.query(Task).order_by(Task.id.desc()).all()


@router.post("", response_model=TaskRead)
def create_task(payload: TaskCreate, db: Session = Depends(get_db_session)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/status", response_model=TaskRead)
def update_task_status(task_id: int, payload: TaskUpdateStatus, db: Session = Depends(get_db_session)):
    task = TaskService.update_status(db, task_id=task_id, status=payload.status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
