from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def list_clients(db: Session = Depends(get_db_session)):
    return db.query(Client).order_by(Client.id.desc()).all()


@router.post("", response_model=ClientRead)
def create_client(payload: ClientCreate, db: Session = Depends(get_db_session)):
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client
