from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Client(Base):
    __tablename__ = 'clients'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    orders: Mapped[list['Order']] = relationship(back_populates='client', cascade='all, delete-orphan')


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default='шт')
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    retail_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    small_opt_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    large_opt_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    is_wholesale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    stock_items: Mapped[list['StockItem']] = relationship(back_populates='product', cascade='all, delete-orphan')
    order_items: Mapped[list['OrderItem']] = relationship(back_populates='product')


class Supplier(Base):
    __tablename__ = 'suppliers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    stock_items: Mapped[list['StockItem']] = relationship(back_populates='supplier')
    orders: Mapped[list['Order']] = relationship(back_populates='supplier')
    movements: Mapped[list['SupplierBalanceMovement']] = relationship(back_populates='supplier', cascade='all, delete-orphan')


class SupplierBalanceMovement(Base):
    __tablename__ = 'supplier_balance_movements'

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey('suppliers.id'), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    supplier: Mapped['Supplier'] = relationship(back_populates='movements')


class Driver(Base):
    __tablename__ = 'drivers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vehicle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cash_on_hand_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    orders: Mapped[list['Order']] = relationship(back_populates='driver')
    movements: Mapped[list['DriverCashMovement']] = relationship(back_populates='driver', cascade='all, delete-orphan')


class DriverCashMovement(Base):
    __tablename__ = 'driver_cash_movements'

    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey('drivers.id'), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    driver: Mapped['Driver'] = relationship(back_populates='movements')


class StockItem(Base):
    __tablename__ = 'stock_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    warehouse_name: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey('suppliers.id'), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product: Mapped['Product'] = relationship(back_populates='stock_items')
    supplier: Mapped['Supplier | None'] = relationship(back_populates='stock_items')


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # retail / wholesale
    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id'), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='new')
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, default='cash')
    delivery_type: Mapped[str] = mapped_column(String(50), nullable=False, default='pickup')
    delivery_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    additional_costs: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey('suppliers.id'), nullable=True)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey('drivers.id'), nullable=True)
    use_supplier_balance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_purchase: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    client: Mapped['Client'] = relationship(back_populates='orders')
    supplier: Mapped['Supplier | None'] = relationship(back_populates='orders')
    driver: Mapped['Driver | None'] = relationship(back_populates='orders')
    items: Mapped[list['OrderItem']] = relationship(back_populates='order', cascade='all, delete-orphan')


class OrderItem(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    pricing_tier: Mapped[str] = mapped_column(String(30), nullable=False, default='retail')
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    line_purchase_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    line_sale_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    line_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    order: Mapped['Order'] = relationship(back_populates='items')
    product: Mapped['Product'] = relationship(back_populates='order_items')
