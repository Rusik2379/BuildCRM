from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.request import ClientRequestCreate, ClientRequestRead
from app.services.request_service import RequestService

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=list[ClientRequestRead])
def list_requests(
    status: str | None = Query(default=None),
    kind: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
):
    return RequestService.list_requests(db, status=status, kind=kind)


@router.post("", response_model=ClientRequestRead)
def create_request(payload: ClientRequestCreate, db: Session = Depends(get_db_session)):
    return RequestService.create_request(db, **payload.model_dump())
