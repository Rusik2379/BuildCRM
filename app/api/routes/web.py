from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.options import (
    DEFAULT_CLIENT_CATEGORIES,
    DEFAULT_PRODUCT_CATEGORIES,
    DEFAULT_SOURCES,
    DEFAULT_UNITS,
)
from app.models.client import Client
from app.models.client_request import PaymentMethod, RequestKind, RequestStatus
from app.models.product import Product
from app.models.stock import StockItem
from app.services.client_service import ClientService
from app.services.product_service import ProductService
from app.services.request_service import RequestService
from app.services.stats_service import StatsService
from app.services.stock_service import StockService

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)

STATUS_LABELS = {
    RequestStatus.new.value: "Новый",
    RequestStatus.in_progress.value: "В работе",
    RequestStatus.done.value: "Завершён",
}
PAYMENT_LABELS = {
    PaymentMethod.cash.value: "Наличкой",
    PaymentMethod.card.value: "По карте",
    PaymentMethod.driver.value: "Оплата водителю",
    PaymentMethod.supplier_balance.value: "Балансом поставщика",
}
KIND_LABELS = {
    RequestKind.retail.value: "Розничные заказы",
    RequestKind.wholesale.value: "Оптовые заявки",
}


@router.get("/")
def home():
    return RedirectResponse(url="/clients-page", status_code=302)


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db_session)):
    stats = StatsService.get_dashboard_stats(db)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"stats": stats, "page_title": "Панель", "active_page": "dashboard"},
    )


@router.get("/clients-page")
def clients_page(
    request: Request,
    search: str | None = Query(default=None),
    source: str = Query(default="all"),
    category: str = Query(default="all"),
    db: Session = Depends(get_db_session),
):
    clients = ClientService.list_clients(db, search=search, source=source, category=category)
    total_clients = db.query(Client).count()
    all_sources = list(dict.fromkeys(DEFAULT_SOURCES + ClientService.get_sources(db)))
    all_categories = list(dict.fromkeys(DEFAULT_CLIENT_CATEGORIES + ClientService.get_categories(db)))
    source_stats = [
        {"name": item, "count": db.query(func.count(Client.id)).filter(Client.source == item).scalar() or 0}
        for item in all_sources
        if item
    ]
    return templates.TemplateResponse(
        request,
        "clients.html",
        {
            "clients": clients,
            "search": search or "",
            "current_source": source,
            "current_category": category,
            "sources": all_sources,
            "categories": all_categories,
            "source_stats": [item for item in source_stats if item["count"] > 0],
            "stats": {
                "total": total_clients,
                "visible": len(clients),
                "with_phone": sum(1 for c in clients if c.phone),
            },
            "page_title": "Клиенты",
            "active_page": "clients",
        },
    )


@router.get("/clients/{client_id}")
def client_detail_page(client_id: int, request: Request, db: Session = Depends(get_db_session)):
    client = db.query(Client).filter(Client.id == client_id).first()
    orders = RequestService.list_by_client(db, client_id) if client else []
    revenue = 0
    return templates.TemplateResponse(
        request,
        "client_detail.html",
        {
            "client": client,
            "orders": orders,
            "order_stats": {
                "total": len(orders),
                "retail": sum(1 for order in orders if order.kind == RequestKind.retail),
                "wholesale": sum(1 for order in orders if order.kind == RequestKind.wholesale),
                "last_order": orders[0].created_at.strftime('%d.%m.%Y') if orders else '—',
                "revenue": revenue,
            },
            "status_labels": STATUS_LABELS,
            "payment_labels": PAYMENT_LABELS,
            "kind_labels": KIND_LABELS,
            "page_title": client.name if client else "Клиент",
            "active_page": "clients",
        },
    )


@router.post("/clients-page")
def create_client_page(
    name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(""),
    source: str = Form(""),
    category: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db_session),
):
    ClientService.create_client(
        db,
        name=name,
        phone=phone,
        address=address or None,
        source=source or None,
        category=category or None,
        notes=notes or None,
    )
    return RedirectResponse(url="/clients-page", status_code=303)


@router.get("/products-page")
def products_page(
    request: Request,
    search: str | None = Query(default=None),
    category: str = Query(default="all"),
    wholesale: str = Query(default="all"),
    db: Session = Depends(get_db_session),
):
    products = ProductService.list_products(db, search=search, category=category, wholesale=wholesale)
    categories = list(dict.fromkeys(DEFAULT_PRODUCT_CATEGORIES + ProductService.get_categories(db)))
    total_products = db.query(Product).count()
    return templates.TemplateResponse(
        request,
        "products.html",
        {
            "products": products,
            "search": search or "",
            "categories": categories,
            "units": DEFAULT_UNITS,
            "current_category": category,
            "current_wholesale": wholesale,
            "stats": {
                "total": total_products,
                "visible": len(products),
                "wholesale": sum(1 for p in products if p.is_wholesale),
            },
            "page_title": "Номенклатура",
            "active_page": "products",
        },
    )


@router.post("/products-page")
def create_product_page(
    name: str = Form(...),
    category: str = Form(""),
    unit: str = Form("шт"),
    description: str = Form(""),
    is_wholesale: str | None = Form(default=None),
    db: Session = Depends(get_db_session),
):
    ProductService.create_product(
        db,
        name=name,
        category=category or None,
        unit=unit,
        description=description or None,
        is_wholesale=bool(is_wholesale),
    )
    return RedirectResponse(url="/products-page", status_code=303)


@router.get("/stock-page")
def stock_page(
    request: Request,
    search: str | None = Query(default=None),
    city: str = Query(default="all"),
    supplier: str = Query(default="all"),
    category: str = Query(default="all"),
    price_mode: str = Query(default="retail"),
    db: Session = Depends(get_db_session),
):
    items = StockService.list_stock(db, search=search, city=city, supplier=supplier, category=category)
    return templates.TemplateResponse(
        request,
        "stock.html",
        {
            "items": items,
            "search": search or "",
            "cities": StockService.get_cities(db),
            "suppliers": StockService.get_suppliers(db),
            "categories": list(dict.fromkeys(DEFAULT_PRODUCT_CATEGORIES + ProductService.get_categories(db))),
            "current_city": city,
            "current_supplier": supplier,
            "current_category": category,
            "price_mode": price_mode,
            "products": ProductService.list_products(db),
            "stats": {
                "total": db.query(StockItem).count(),
                "visible": len(items),
                "qty_sum": float(sum(float(item.quantity or 0) for item in items)),
            },
            "page_title": "Склад",
            "active_page": "stock",
        },
    )


@router.post("/stock-page")
def create_stock_page(
    product_id: int = Form(...),
    city_choice: str = Form(""),
    city_name: str = Form(""),
    supplier_choice: str = Form(""),
    supplier_name: str = Form(""),
    quantity: float = Form(0),
    purchase_price: float = Form(0),
    retail_price: float = Form(0),
    small_wholesale_price: float = Form(0),
    large_wholesale_price: float = Form(0),
    notes: str = Form(""),
    db: Session = Depends(get_db_session),
):
    resolved_city = (city_name or "").strip() or (city_choice or "").strip() or None
    resolved_supplier = (supplier_name or "").strip() or (supplier_choice or "").strip() or None
    StockService.create_stock_item(
        db,
        product_id=product_id,
        city_name=resolved_city,
        supplier_name=resolved_supplier,
        quantity=quantity,
        purchase_price=purchase_price,
        retail_price=retail_price,
        small_wholesale_price=small_wholesale_price,
        large_wholesale_price=large_wholesale_price,
        notes=notes or None,
    )
    return RedirectResponse(url="/stock-page", status_code=303)


@router.get("/requests-page")
def requests_page(
    request: Request,
    status: str = Query(default="all"),
    kind: str = Query(default=RequestKind.retail.value),
    db: Session = Depends(get_db_session),
):
    current_kind = kind if kind in {RequestKind.retail.value, RequestKind.wholesale.value} else RequestKind.retail.value
    orders = RequestService.list_requests(db, status=status, kind=current_kind)
    all_requests = RequestService.list_requests(db)
    kind_requests = RequestService.list_requests(db, kind=current_kind)
    return templates.TemplateResponse(
        request,
        "requests.html",
        {
            "requests": orders,
            "stats": {
                "total": len(kind_requests),
                "new": sum(1 for r in kind_requests if r.status == RequestStatus.new),
                "in_progress": sum(1 for r in kind_requests if r.status == RequestStatus.in_progress),
                "done": sum(1 for r in kind_requests if r.status == RequestStatus.done),
                "retail_total": sum(1 for r in all_requests if r.kind == RequestKind.retail),
                "wholesale_total": sum(1 for r in all_requests if r.kind == RequestKind.wholesale),
            },
            "current_status": status,
            "current_kind": current_kind,
            "statuses": [status.value for status in RequestStatus],
            "status_labels": STATUS_LABELS,
            "payment_labels": PAYMENT_LABELS,
            "kind_labels": KIND_LABELS,
            "page_title": KIND_LABELS[current_kind],
            "active_page": f"requests_{current_kind}",
        },
    )


@router.post("/requests-page")
def create_request_page(
    client_query: str = Form(...),
    product_query: str = Form(""),
    title: str = Form(...),
    description: str = Form(""),
    status: RequestStatus = Form(RequestStatus.new),
    kind: RequestKind = Form(RequestKind.retail),
    payment_method: PaymentMethod | None = Form(default=None),
    db: Session = Depends(get_db_session),
):
    client = ClientService.get_or_create_by_query(db, client_query)
    product = ProductService.get_or_create_by_name(db, product_query) if product_query.strip() else None
    RequestService.create_request(
        db,
        client_id=client.id,
        product_id=product.id if product else None,
        title=title,
        description=description or None,
        status=status,
        kind=kind,
        payment_method=payment_method,
    )
    return RedirectResponse(url=f"/requests-page?kind={kind.value}", status_code=303)


@router.get("/lookup/clients")
def lookup_clients(q: str = Query(default=""), db: Session = Depends(get_db_session)):
    items = ClientService.list_clients(db, search=q)[:8]
    return JSONResponse([
        {"id": item.id, "label": f"{item.name} — {item.phone}", "name": item.name, "phone": item.phone}
        for item in items
    ])


@router.get("/lookup/products")
def lookup_products(q: str = Query(default=""), db: Session = Depends(get_db_session)):
    items = ProductService.list_products(db, search=q)[:8]
    return JSONResponse([
        {"id": item.id, "label": f"{item.name} ({item.category or 'Без категории'})", "name": item.name}
        for item in items
    ])
