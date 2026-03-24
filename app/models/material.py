from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class MaterialItem(Base):
    __tablename__ = "material_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="шт")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    planned_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
