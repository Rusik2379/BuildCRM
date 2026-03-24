from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models.client import Client
from app.models.client_request import PaymentMethod, RequestStatus
from app.models.product import Product
from app.services.client_service import ClientService
from app.services.product_service import ProductService
from app.services.request_service import RequestService
from app.services.stats_service import StatsService

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
    db: Session = Depends(get_db_session),
):
    clients = ClientService.list_clients(db, search=search)
    total_clients = db.query(Client).count()
    return templates.TemplateResponse(
        request,
        "clients.html",
        {
            "clients": clients,
            "search": search or "",
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
    orders = [item for item in RequestService.list_requests(db) if item.client_id == client_id]
    return templates.TemplateResponse(
        request,
        "client_detail.html",
        {
            "client": client,
            "orders": orders,
            "status_labels": STATUS_LABELS,
            "payment_labels": PAYMENT_LABELS,
            "page_title": client.name if client else "Клиент",
            "active_page": "clients",
        },
    )


@router.post("/clients-page")
def create_client_page(
    name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db_session),
):
    ClientService.create_client(
        db,
        name=name,
        phone=phone,
        address=address or None,
        notes=notes or None,
    )
    return RedirectResponse(url="/clients-page", status_code=303)


@router.get("/products-page")
def products_page(
    request: Request,
    search: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
):
    products = ProductService.list_products(db, search=search)
    total_products = db.query(Product).count()
    return templates.TemplateResponse(
        request,
        "products.html",
        {
            "products": products,
            "search": search or "",
            "stats": {
                "total": total_products,
                "visible": len(products),
                "with_price": sum(1 for p in products if float(p.price or 0) > 0),
            },
            "page_title": "Номенклатура",
            "active_page": "products",
        },
    )


@router.post("/products-page")
def create_product_page(
    name: str = Form(...),
    unit: str = Form("шт"),
    price: float = Form(0),
    notes: str = Form(""),
    db: Session = Depends(get_db_session),
):
    ProductService.create_product(
        db,
        name=name,
        unit=unit,
        price=price,
        notes=notes or None,
    )
    return RedirectResponse(url="/products-page", status_code=303)


@router.get("/requests-page")
def requests_page(
    request: Request,
    status: str = Query(default="all"),
    db: Session = Depends(get_db_session),
):
    orders = RequestService.list_requests(db, status=status)
    return templates.TemplateResponse(
        request,
        "requests.html",
        {
            "requests": orders,
            "stats": {
                "total": len(RequestService.list_requests(db)),
                "new": sum(1 for r in RequestService.list_requests(db) if r.status == RequestStatus.new),
                "in_progress": sum(1 for r in RequestService.list_requests(db) if r.status == RequestStatus.in_progress),
                "done": sum(1 for r in RequestService.list_requests(db) if r.status == RequestStatus.done),
            },
            "current_status": status,
            "statuses": [status.value for status in RequestStatus],
            "status_labels": STATUS_LABELS,
            "payment_labels": PAYMENT_LABELS,
            "page_title": "Заказы",
            "active_page": "requests",
        },
    )


@router.post("/requests-page")
def create_request_page(
    client_query: str = Form(...),
    product_query: str = Form(""),
    title: str = Form(...),
    description: str = Form(""),
    status: RequestStatus = Form(RequestStatus.new),
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
        payment_method=payment_method,
    )
    return RedirectResponse(url="/requests-page", status_code=303)


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
        {"id": item.id, "label": f"{item.name} · {item.unit}", "name": item.name}
        for item in items
    ])
