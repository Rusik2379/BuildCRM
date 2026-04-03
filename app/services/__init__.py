from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Client,
    Driver,
    DriverCashMovement,
    GeneralExpense,
    Order,
    OrderItem,
    Product,
    StockItem,
    Supplier,
    SupplierBalanceMovement,
)


PRICE_ADJUSTMENTS = {
    'small_opt_non_cash': Decimal('0.06'),
    'medium_opt_non_cash': Decimal('0.02'),
    'large_opt_non_cash': Decimal('-0.03'),
}


def to_decimal(value: str | float | int | Decimal | None, default: str = '0') -> Decimal:
    raw = default if value in (None, '') else str(value).replace(',', '.')
    try:
        return Decimal(raw)
    except Exception:
        return Decimal(default)


def normalize_phone(phone: str | None) -> str:
    return ''.join(ch for ch in (phone or '') if ch.isdigit()) or (phone or '').strip()


def find_or_create_client(
    db: Session,
    name: str,
    phone: str = '',
    address: str = '',
    source: str = '',
    category: str = '',
    client_type: str = 'retail',
) -> Client:
    phone_norm = normalize_phone(phone)
    client = None

    if phone_norm:
        client = db.scalar(select(Client).where(Client.phone == phone_norm))

    if not client:
        client = db.scalar(select(Client).where(Client.name == name.strip()))

    if client:
        if address and not client.address:
            client.address = address.strip()
        if source and not client.source:
            client.source = source.strip()
        if category and not client.category:
            client.category = category.strip()
        if client_type == 'wholesale' and client.client_type != 'wholesale':
            client.client_type = 'wholesale'
        return client

    client = Client(
        name=name.strip(),
        phone=phone_norm or phone.strip() or 'без телефона',
        client_type='wholesale' if client_type == 'wholesale' else 'retail',
        address=address.strip() or None,
        source=source.strip() or None,
        category=category.strip() or None,
    )
    db.add(client)
    db.flush()
    return client


def find_or_create_product(db: Session, name: str, category: str = '', unit: str = 'шт') -> Product:
    product = db.scalar(select(Product).where(Product.name == name.strip()))
    if product:
        return product

    product = Product(
        name=name.strip(),
        category=category.strip() or None,
        unit=unit.strip() or 'шт',
    )
    db.add(product)
    db.flush()
    return product


def base_product_price_for_tier(product: Product, tier: str) -> Decimal:
    if tier in {'small_opt', 'small_opt_non_cash'}:
        return Decimal(product.small_opt_price or 0)
    if tier in {'large_opt', 'large_opt_non_cash'}:
        return Decimal(product.large_opt_price or 0)
    if tier == 'medium_opt_non_cash':
        return Decimal(product.retail_price or 0)
    return Decimal(product.retail_price or 0)


def product_price_for_tier(product: Product, tier: str) -> Decimal:
    base_price = base_product_price_for_tier(product, tier)
    adjustment = PRICE_ADJUSTMENTS.get(tier, Decimal('0'))
    adjusted = base_price * (Decimal('1') + adjustment)
    if adjusted < 0:
        adjusted = Decimal('0')
    return adjusted.quantize(Decimal('0.01'))


def normalize_payment_method(payment_method: str) -> str:
    mapping = {
        'cash': 'cash_us',
        'transfer': 'transfer_us',
        'card': 'transfer_us',
        'driver_payment': 'cash_driver',
        'invoice_no_vat': 'invoice_no_vat',
        'cash_us': 'cash_us',
        'transfer_us': 'transfer_us',
        'cash_driver': 'cash_driver',
        'transfer_supplier': 'transfer_supplier',
    }
    return mapping.get((payment_method or '').strip(), 'cash_us')


def recalculate_order(order: Order) -> None:
    purchase = sum((Decimal(item.line_purchase_total or 0) for item in order.items), Decimal('0'))
    sale = sum((Decimal(item.line_sale_total or 0) for item in order.items), Decimal('0'))

    order.total_purchase = purchase
    order.total_revenue = sale + Decimal(order.delivery_cost or 0)
    order.total_profit = order.total_revenue - purchase - Decimal(order.additional_costs or 0)
    if purchase > 0:
        order.markup_percent = ((order.total_profit / purchase) * Decimal('100')).quantize(Decimal('0.01'))
    else:
        order.markup_percent = Decimal('0')


def create_order(
    db: Session,
    *,
    kind: str,
    client_name: str,
    client_phone: str,
    client_address: str,
    client_source: str,
    client_category: str,
    product_ids: list[str],
    quantities: list[str],
    sale_prices: list[str],
    pricing_tier: str,
    status: str,
    payment_method: str,
    delivery_type: str,
    delivery_cost: str,
    additional_costs: str,
    notes: str,
    supplier_id: str,
    driver_id: str,
    use_supplier_balance: bool,
    document_issued: bool = False,
    document_name: str = '',
) -> Order:
    normalized_payment_method = normalize_payment_method(payment_method)
    client = find_or_create_client(
        db,
        client_name,
        client_phone,
        client_address,
        source=client_source,
        category=client_category,
        client_type='wholesale' if kind == 'wholesale' else 'retail',
    )

    order = Order(
        kind=kind,
        status=status,
        payment_method=normalized_payment_method,
        delivery_type=delivery_type,
        delivery_cost=to_decimal(delivery_cost),
        additional_costs=to_decimal(additional_costs),
        notes=notes.strip() or None,
        client=client,
        supplier_id=int(supplier_id) if supplier_id else None,
        driver_id=int(driver_id) if driver_id else None,
        use_supplier_balance=bool(use_supplier_balance),
        client_source_snapshot=client_source.strip() or client.source,
        document_issued=bool(document_issued),
        document_name=document_name.strip() or None,
    )
    db.add(order)
    db.flush()

    created_items = 0

    for index, product_id in enumerate(product_ids):
        pid = str(product_id or '').strip()
        if not pid:
            continue

        product = db.get(Product, int(pid))
        if not product:
            continue

        qty_raw = quantities[index] if index < len(quantities) else '1'
        sale_raw = sale_prices[index] if index < len(sale_prices) else ''

        qty = to_decimal(qty_raw, '1')
        if qty <= 0:
            continue

        purchase_price = Decimal(product.purchase_price or 0)
        fallback_sale = product_price_for_tier(product, pricing_tier)
        sale_price = to_decimal(sale_raw, str(fallback_sale))
        if sale_price < 0:
            sale_price = Decimal('0')

        item = OrderItem(
            order=order,
            product=product,
            quantity=qty,
            pricing_tier=pricing_tier,
            purchase_price=purchase_price,
            sale_price=sale_price,
            line_purchase_total=qty * purchase_price,
            line_sale_total=qty * sale_price,
        )
        db.add(item)
        created_items += 1

    if created_items == 0:
        raise ValueError('Нужно добавить хотя бы один товар')

    db.flush()
    recalculate_order(order)

    if order.use_supplier_balance and order.supplier_id:
        supplier = db.get(Supplier, order.supplier_id)
        if supplier:
            delta = -(Decimal(order.total_purchase or 0))
            supplier.balance = Decimal(supplier.balance or 0) + delta
            db.add(
                SupplierBalanceMovement(
                    supplier=supplier,
                    amount=delta,
                    reason=f'Списание по заказу #{order.id}',
                )
            )

    if order.payment_method == 'cash_driver' and order.driver_id:
        driver = db.get(Driver, order.driver_id)
        if driver:
            delta = Decimal(order.total_revenue or 0)
            driver.cash_on_hand = Decimal(driver.cash_on_hand or 0) + delta
            db.add(
                DriverCashMovement(
                    driver=driver,
                    amount=delta,
                    reason=f'Оплата по заказу #{order.id}',
                )
            )

    db.commit()
    db.refresh(order)
    return order


def supplier_adjust_balance(db: Session, supplier_id: int, amount: str, reason: str = '') -> None:
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        return

    delta = to_decimal(amount)
    supplier.balance = Decimal(supplier.balance or 0) + delta
    db.add(
        SupplierBalanceMovement(
            supplier=supplier,
            amount=delta,
            reason=reason.strip() or None,
        )
    )
    db.commit()


def driver_adjust_cash(db: Session, driver_id: int, amount: str, reason: str = '') -> None:
    driver = db.get(Driver, driver_id)
    if not driver:
        return

    delta = to_decimal(amount)
    driver.cash_on_hand = Decimal(driver.cash_on_hand or 0) + delta
    db.add(
        DriverCashMovement(
            driver=driver,
            amount=delta,
            reason=reason.strip() or None,
        )
    )
    db.commit()


def dashboard_stats(db: Session) -> dict:
    total_clients = db.scalar(select(func.count(Client.id))) or 0
    total_products = db.scalar(select(func.count(Product.id))) or 0
    total_stock = db.scalar(select(func.coalesce(func.sum(StockItem.quantity), 0))) or 0
    total_suppliers = db.scalar(select(func.count(Supplier.id))) or 0
    total_drivers = db.scalar(select(func.count(Driver.id))) or 0
    retail_orders = db.scalar(select(func.count(Order.id)).where(Order.kind == 'retail')) or 0
    wholesale_orders = db.scalar(select(func.count(Order.id)).where(Order.kind == 'wholesale')) or 0
    revenue = db.scalar(select(func.coalesce(func.sum(Order.total_revenue), 0))) or 0
    profit = db.scalar(select(func.coalesce(func.sum(Order.total_profit), 0))) or 0
    general_expenses = db.scalar(select(func.coalesce(func.sum(GeneralExpense.amount), 0))) or 0

    return {
        'total_clients': total_clients,
        'total_products': total_products,
        'total_stock': float(total_stock),
        'total_suppliers': total_suppliers,
        'total_drivers': total_drivers,
        'retail_orders': retail_orders,
        'wholesale_orders': wholesale_orders,
        'revenue': float(revenue),
        'profit': float(profit),
        'general_expenses': float(general_expenses),
    }


def get_client_detail(db: Session, client_id: int):
    return db.scalar(
        select(Client)
        .options(
            joinedload(Client.orders)
            .joinedload(Order.items)
            .joinedload(OrderItem.product),
            joinedload(Client.orders).joinedload(Order.driver),
            joinedload(Client.orders).joinedload(Order.supplier),
        )
        .where(Client.id == client_id)
    )
