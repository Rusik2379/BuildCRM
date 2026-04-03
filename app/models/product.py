from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="шт")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_wholesale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    stock_items = relationship("StockItem", back_populates="product")
    requests = relationship("ClientRequest", back_populates="product")
