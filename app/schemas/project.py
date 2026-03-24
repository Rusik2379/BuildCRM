from pydantic import BaseModel

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    title: str
    object_address: str
    description: str | None = None
    budget: float | None = None
    status: ProjectStatus = ProjectStatus.new
    client_id: int
    manager_id: int | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int

    model_config = {"from_attributes": True}
