from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.client import ClientCreate, ClientRead
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def list_clients(search: str | None = Query(default=None), db: Session = Depends(get_db_session)):
    return ClientService.list_clients(db, search=search)


@router.post("", response_model=ClientRead)
def create_client(payload: ClientCreate, db: Session = Depends(get_db_session)):
    return ClientService.create_client(db, **payload.model_dump())
