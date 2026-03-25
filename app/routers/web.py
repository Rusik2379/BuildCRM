from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload
from starlette.status import HTTP_303_SEE_OTHER
from starlette.templating import Jinja2Templates

from app.db import db_dependency
from app.models import (
    Client,
    Driver,
    DriverCashMovement,
    Order,
    OrderItem,
    Product,
    StockItem,
    Supplier,
    SupplierBalanceMovement,
)
from app.services import (
    create_order,
    dashboard_stats,
    driver_adjust_cash,
    find_or_create_product,
    get_client_detail,
    normalize_phone,
    supplier_adjust_balance,
    to_decimal,
)

router = APIRouter()
templates = Jinja2Templates(directory='app/templates')

CLIENT_SOURCES = ['Авито', '2ГИС', 'Сарафанка', 'ВК', 'Telegram', 'Сайт', 'Повторный клиент', 'Другое']
CLIENT_CATEGORIES = ['Частник', 'Бригадир', 'Прораб', 'База', 'Магазин', 'Подрядчик', 'Другое']
CLIENT_TYPES = [('retail', 'Розничный'), ('wholesale', 'Оптовый')]

PRODUCT_CATEGORIES = ['Кирпич', 'Газоблок', 'Цемент', 'Профлист', 'Утеплитель', 'Розница', 'Опт', 'Другое']
UNITS = ['шт', 'м3', 'т', 'кг', 'мешок', 'лист', 'паллета']

ORDER_STATUSES = ['new', 'in_work', 'delivered', 'done', 'canceled']
PAYMENT_METHODS = [
    ('cash', 'Наличкой'),
    ('card', 'По карте'),
    ('driver_payment', 'Оплата водителю'),
    ('supplier_balance', 'Балансом поставщика'),
]
DELIVERY_TYPES = [('pickup', 'Самовывоз'), ('delivery', 'Доставка')]
PRICING_TIERS = [('retail', 'Розница'), ('small_opt', 'Мелкий опт'), ('large_opt', 'Крупный опт')]


@router.get('/')
def root():
    return RedirectResponse('/dashboard', status_code=HTTP_303_SEE_OTHER)


@router.get('/dashboard')
def dashboard(request: Request, db: Session = Depends(db_dependency)):
    stats = dashboard_stats(db)
    source_stats = db.execute(
        select(Client.source, func.count(Client.id))
        .group_by(Client.source)
        .order_by(func.count(Client.id).desc())
    ).all()

    return templates.TemplateResponse(
        request,
        'dashboard.html',
        {
            'stats': stats,
            'source_stats': source_stats,
        },
    )


@router.get('/clients')
def clients_page(
    request: Request,
    search: str = '',
    source: str = '',
    category: str = '',
    client_type: str = '',
    sort_by: str = 'created_at',
    sort_order: str = 'desc',
    db: Session = Depends(db_dependency),
):
    query = select(Client)

    if search:
        pattern = f'%{search.strip()}%'
        query = query.where(
            or_(
                Client.name.ilike(pattern),
                Client.phone.ilike(pattern),
                Client.address.ilike(pattern),
                Client.notes.ilike(pattern),
            )
        )

    if source:
        query = query.where(Client.source == source)

    if category:
        query = query.where(Client.category == category)

    if client_type:
        query = query.where(Client.client_type == client_type)

    sort_map = {
        'name': Client.name,
        'phone': Client.phone,
        'client_type': Client.client_type,
        'source': Client.source,
        'category': Client.category,
        'created_at': Client.created_at,
    }
    sort_column = sort_map.get(sort_by, Client.created_at)
    direction = asc if sort_order == 'asc' else desc

    query = query.order_by(direction(sort_column), desc(Client.id))
    clients = db.scalars(query).all()

    total_clients = db.scalar(select(func.count(Client.id))) or 0
    retail_clients = db.scalar(
        select(func.count(Client.id)).where(Client.client_type == 'retail')
    ) or 0
    wholesale_clients = db.scalar(
        select(func.count(Client.id)).where(Client.client_type == 'wholesale')
    ) or 0

    return templates.TemplateResponse(
        request,
        'clients.html',
        {
            'clients': clients,
            'total_clients': total_clients,
            'retail_clients': retail_clients,
            'wholesale_clients': wholesale_clients,
            'client_sources': CLIENT_SOURCES,
            'client_categories': CLIENT_CATEGORIES,
            'client_types': CLIENT_TYPES,
            'search': search,
            'source': source,
            'category': category,
            'client_type': client_type,
            'sort_by': sort_by,
            'sort_order': sort_order,
        },
    )


@router.post('/clients')
def create_client(
    name: str = Form(...),
    phone: str = Form(...),
    client_type: str = Form('retail'),
    address: str = Form(''),
    source: str = Form(''),
    category: str = Form(''),
    notes: str = Form(''),
    db: Session = Depends(db_dependency),
):
    normalized_phone = normalize_phone(phone)

    duplicate = None
    if normalized_phone:
        duplicate = db.scalar(select(Client).where(Client.phone == normalized_phone).limit(1))

    if not duplicate:
        duplicate = db.scalar(select(Client).where(Client.name == name.strip()).limit(1))

    if duplicate:
        if client_type == 'wholesale' and duplicate.client_type != 'wholesale':
            duplicate.client_type = 'wholesale'
        if address and not duplicate.address:
            duplicate.address = address.strip()
        if source and not duplicate.source:
            duplicate.source = source
        if category and not duplicate.category:
            duplicate.category = category
        if notes and not duplicate.notes:
            duplicate.notes = notes.strip()
        db.commit()
        return RedirectResponse(f'/clients/{duplicate.id}', status_code=HTTP_303_SEE_OTHER)

    client = Client(
        name=name.strip(),
        phone=normalized_phone or phone.strip(),
        client_type='wholesale' if client_type == 'wholesale' else 'retail',
        address=address.strip() or None,
        source=source or None,
        category=category or None,
        notes=notes.strip() or None,
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return RedirectResponse(f'/clients/{client.id}', status_code=HTTP_303_SEE_OTHER)


@router.post('/clients/{client_id}/edit')
def edit_client(
    client_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    client_type: str = Form('retail'),
    address: str = Form(''),
    source: str = Form(''),
    category: str = Form(''),
    notes: str = Form(''),
    db: Session = Depends(db_dependency),
):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail='Клиент не найден')

    normalized_phone = normalize_phone(phone)
    duplicate = db.scalar(
        select(Client)
        .where(Client.phone == normalized_phone, Client.id != client_id)
        .limit(1)
    )
    if duplicate:
        raise HTTPException(status_code=400, detail='Клиент с таким телефоном уже существует')

    client.name = name.strip()
    client.phone = normalized_phone or phone.strip()
    client.client_type = 'wholesale' if client_type == 'wholesale' else 'retail'
    client.address = address.strip() or None
    client.source = source or None
    client.category = category or None
    client.notes = notes.strip() or None

    db.commit()
    return RedirectResponse(f'/clients/{client_id}', status_code=HTTP_303_SEE_OTHER)


@router.get('/clients/{client_id}')
def client_detail(request: Request, client_id: int, db: Session = Depends(db_dependency)):
    client = get_client_detail(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail='Клиент не найден')

    orders = sorted(
        client.orders,
        key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    retail_count = len([o for o in orders if o.kind == 'retail'])
    wholesale_count = len([o for o in orders if o.kind == 'wholesale'])
    total_revenue = sum((Decimal(o.total_revenue or 0) for o in orders), Decimal('0'))
    total_profit = sum((Decimal(o.total_profit or 0) for o in orders), Decimal('0'))

    return templates.TemplateResponse(
        request,
        'client_detail.html',
        {
            'client': client,
            'orders': orders,
            'retail_count': retail_count,
            'wholesale_count': wholesale_count,
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'client_sources': CLIENT_SOURCES,
            'client_categories': CLIENT_CATEGORIES,
            'client_types': CLIENT_TYPES,
        },
    )


@router.get('/products')
def products_page(request: Request, search: str = '', category: str = '', db: Session = Depends(db_dependency)):
    query = select(Product).order_by(Product.created_at.desc())

    if search:
        pattern = f'%{search}%'
        query = query.where(
            (Product.name.ilike(pattern)) | (Product.description.ilike(pattern))
        )

    if category:
        query = query.where(Product.category == category)

    products = db.scalars(query).all()

    return templates.TemplateResponse(
        request,
        'products.html',
        {
            'products': products,
            'search': search,
            'category': category,
            'product_categories': PRODUCT_CATEGORIES,
            'units': UNITS,
        },
    )


@router.post('/products')
def create_product(
    name: str = Form(...),
    category: str = Form(''),
    unit: str = Form('шт'),
    description: str = Form(''),
    purchase_price: str = Form('0'),
    retail_price: str = Form('0'),
    small_opt_price: str = Form('0'),
    large_opt_price: str = Form('0'),
    is_wholesale: bool = Form(False),
    db: Session = Depends(db_dependency),
):
    product = find_or_create_product(db, name, category, unit)
    product.description = description.strip() or None
    product.purchase_price = to_decimal(purchase_price)
    product.retail_price = to_decimal(retail_price)
    product.small_opt_price = to_decimal(small_opt_price)
    product.large_opt_price = to_decimal(large_opt_price)
    product.is_wholesale = bool(is_wholesale)
    db.commit()

    return RedirectResponse('/products', status_code=HTTP_303_SEE_OTHER)


@router.get('/stock')
def stock_page(request: Request, search: str = '', warehouse: str = '', db: Session = Depends(db_dependency)):
    query = (
        select(StockItem)
        .options(joinedload(StockItem.product), joinedload(StockItem.supplier))
        .order_by(StockItem.updated_at.desc())
    )

    if warehouse:
        query = query.where(StockItem.warehouse_name == warehouse)

    stock_items = db.scalars(query).all()

    if search:
        search_lower = search.lower()
        stock_items = [
            item for item in stock_items
            if search_lower in item.product.name.lower()
            or search_lower in (item.city or '').lower()
            or search_lower in item.warehouse_name.lower()
        ]

    warehouses = sorted(
        {item.warehouse_name for item in db.scalars(select(StockItem)).all() if item.warehouse_name}
    )
    suppliers = db.scalars(select(Supplier).order_by(Supplier.name)).all()
    products = db.scalars(select(Product).order_by(Product.name)).all()

    return templates.TemplateResponse(
        request,
        'stock.html',
        {
            'stock_items': stock_items,
            'warehouses': warehouses,
            'warehouse': warehouse,
            'search': search,
            'suppliers': suppliers,
            'products': products,
        },
    )


@router.post('/stock')
def create_stock_item(
    product_id: int = Form(...),
    warehouse_name: str = Form(...),
    city: str = Form(''),
    supplier_id: str = Form(''),
    quantity: str = Form('0'),
    notes: str = Form(''),
    db: Session = Depends(db_dependency),
):
    item = StockItem(
        product_id=product_id,
        warehouse_name=warehouse_name.strip(),
        city=city.strip() or None,
        supplier_id=int(supplier_id) if supplier_id else None,
        quantity=to_decimal(quantity),
        notes=notes.strip() or None,
    )
    db.add(item)
    db.commit()

    return RedirectResponse('/stock', status_code=HTTP_303_SEE_OTHER)


@router.get('/suppliers')
def suppliers_page(request: Request, db: Session = Depends(db_dependency)):
    suppliers = db.scalars(select(Supplier).order_by(Supplier.name)).all()
    movements = db.scalars(
        select(SupplierBalanceMovement)
        .options(joinedload(SupplierBalanceMovement.supplier))
        .order_by(SupplierBalanceMovement.created_at.desc())
        .limit(20)
    ).all()

    return templates.TemplateResponse(
        request,
        'suppliers.html',
        {'suppliers': suppliers, 'movements': movements},
    )


@router.post('/suppliers')
def create_supplier(
    name: str = Form(...),
    city: str = Form(''),
    phone: str = Form(''),
    balance: str = Form('0'),
    notes: str = Form(''),
    db: Session = Depends(db_dependency),
):
    supplier = Supplier(
        name=name.strip(),
        city=city.strip() or None,
        phone=phone.strip() or None,
        balance=to_decimal(balance),
        notes=notes.strip() or None,
    )
    db.add(supplier)
    db.commit()

    return RedirectResponse('/suppliers', status_code=HTTP_303_SEE_OTHER)


@router.post('/suppliers/{supplier_id}/balance')
def supplier_balance(
    supplier_id: int,
    amount: str = Form(...),
    reason: str = Form(''),
    db: Session = Depends(db_dependency),
):
    supplier_adjust_balance(db, supplier_id, amount, reason)
    return RedirectResponse('/suppliers', status_code=HTTP_303_SEE_OTHER)


@router.get('/drivers')
def drivers_page(request: Request, db: Session = Depends(db_dependency)):
    drivers = db.scalars(select(Driver).order_by(Driver.name)).all()
    movements = db.scalars(
        select(DriverCashMovement)
        .options(joinedload(DriverCashMovement.driver))
        .order_by(DriverCashMovement.created_at.desc())
        .limit(20)
    ).all()

    return templates.TemplateResponse(
        request,
        'drivers.html',
        {'drivers': drivers, 'movements': movements},
    )


@router.post('/drivers')
def create_driver(
    name: str = Form(...),
    phone: str = Form(''),
    vehicle: str = Form(''),
    notes: str = Form(''),
    db: Session = Depends(db_dependency),
):
    driver = Driver(
        name=name.strip(),
        phone=phone.strip() or None,
        vehicle=vehicle.strip() or None,
        notes=notes.strip() or None,
    )
    db.add(driver)
    db.commit()

    return RedirectResponse('/drivers', status_code=HTTP_303_SEE_OTHER)


@router.post('/drivers/{driver_id}/cash')
def driver_cash(
    driver_id: int,
    amount: str = Form(...),
    reason: str = Form(''),
    db: Session = Depends(db_dependency),
):
    driver_adjust_cash(db, driver_id, amount, reason)
    return RedirectResponse('/drivers', status_code=HTTP_303_SEE_OTHER)


@router.get('/orders/{kind}')
def orders_page(request: Request, kind: str, status: str = '', db: Session = Depends(db_dependency)):
    query = (
        select(Order)
        .options(
            joinedload(Order.client),
            joinedload(Order.driver),
            joinedload(Order.supplier),
            joinedload(Order.items).joinedload(OrderItem.product),
        )
        .where(Order.kind == kind)
        .order_by(Order.created_at.desc())
    )

    if status:
        query = query.where(Order.status == status)

    orders = db.scalars(query).unique().all()
    drivers = db.scalars(select(Driver).order_by(Driver.name)).all()
    suppliers = db.scalars(select(Supplier).order_by(Supplier.name)).all()

    return templates.TemplateResponse(
        request,
        'orders.html',
        {
            'kind': kind,
            'orders': orders,
            'status': status,
            'order_statuses': ORDER_STATUSES,
            'payment_methods': PAYMENT_METHODS,
            'delivery_types': DELIVERY_TYPES,
            'pricing_tiers': PRICING_TIERS,
            'product_categories': PRODUCT_CATEGORIES,
            'units': UNITS,
            'client_sources': CLIENT_SOURCES,
            'client_categories': CLIENT_CATEGORIES,
            'drivers': drivers,
            'suppliers': suppliers,
        },
    )


@router.post('/orders/{kind}')
def create_order_route(
    kind: str,
    client_name: str = Form(...),
    client_phone: str = Form(''),
    client_address: str = Form(''),
    client_source: str = Form(''),
    client_category: str = Form(''),
    product_name: str = Form(...),
    product_category: str = Form(''),
    product_unit: str = Form('шт'),
    quantity: str = Form('1'),
    pricing_tier: str = Form('retail'),
    status: str = Form('new'),
    payment_method: str = Form('cash'),
    delivery_type: str = Form('pickup'),
    delivery_cost: str = Form('0'),
    additional_costs: str = Form('0'),
    supplier_id: str = Form(''),
    driver_id: str = Form(''),
    use_supplier_balance: bool = Form(False),
    notes: str = Form(''),
    db: Session = Depends(db_dependency),
):
    create_order(
        db,
        kind=kind,
        client_name=client_name,
        client_phone=client_phone,
        client_address=client_address,
        client_source=client_source,
        client_category=client_category,
        product_name=product_name,
        product_category=product_category,
        product_unit=product_unit,
        quantity=quantity,
        pricing_tier=pricing_tier,
        status=status,
        payment_method=payment_method,
        delivery_type=delivery_type,
        delivery_cost=delivery_cost,
        additional_costs=additional_costs,
        notes=notes,
        supplier_id=supplier_id,
        driver_id=driver_id,
        use_supplier_balance=use_supplier_balance,
    )
    return RedirectResponse(f'/orders/{kind}', status_code=HTTP_303_SEE_OTHER)


@router.get('/finances')
def finances_page(request: Request, db: Session = Depends(db_dependency)):
    stats = dashboard_stats(db)
    totals = db.execute(
        select(
            Order.kind,
            func.coalesce(func.sum(Order.total_revenue), 0),
            func.coalesce(func.sum(Order.total_purchase), 0),
            func.coalesce(func.sum(Order.total_profit), 0),
            func.count(Order.id),
        ).group_by(Order.kind)
    ).all()

    latest_orders = db.scalars(
        select(Order)
        .options(joinedload(Order.client))
        .order_by(Order.created_at.desc())
        .limit(12)
    ).all()

    return templates.TemplateResponse(
        request,
        'finances.html',
        {
            'stats': stats,
            'totals': totals,
            'latest_orders': latest_orders,
        },
    )


@router.get('/documents')
def documents_page(request: Request):
    docs = [
        'Счёт на оплату',
        'Накладная',
        'Акт',
        'Договор',
        'Путевой лист',
        'Коммерческое предложение',
    ]
    return templates.TemplateResponse(
        request,
        'documents.html',
        {'docs': docs},
    )