from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    suppliers = relationship("Supplier", back_populates="city")
    stock_items = relationship("StockItem", back_populates="city")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    city = relationship("City", back_populates="suppliers")
    stock_items = relationship("StockItem", back_populates="supplier")


class StockItem(Base):
    __tablename__ = "stock_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    retail_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    small_wholesale_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    large_wholesale_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="stock_items")
    city = relationship("City", back_populates="stock_items")
    supplier = relationship("Supplier", back_populates="stock_items")
