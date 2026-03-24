from datetime import datetime

from pydantic import BaseModel

from app.models.task import TaskStatus


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.new
    due_date: datetime | None = None
    project_id: int
    assignee_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdateStatus(BaseModel):
    status: TaskStatus


class TaskRead(TaskBase):
    id: int

    model_config = {"from_attributes": True}
