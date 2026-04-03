from datetime import datetime

from pydantic import BaseModel

from app.models.client_request import PaymentMethod, RequestKind, RequestStatus


class ClientRequestBase(BaseModel):
    title: str
    description: str | None = None
    status: RequestStatus = RequestStatus.new
    kind: RequestKind = RequestKind.retail
    client_id: int
    product_id: int | None = None
    payment_method: PaymentMethod | None = None


class ClientRequestCreate(ClientRequestBase):
    pass


class ClientRequestRead(ClientRequestBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
