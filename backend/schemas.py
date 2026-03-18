from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class RequestBase(BaseModel):
    latitude: float
    longitude: float
    need_type: str

class RequestCreate(RequestBase):
    pass

class RequestResponse(RequestBase):
    id: UUID
    created_at: datetime
    is_verified: bool 
    model_config = {"from_attributes": True}

class PrioritizedRequestResponse(RequestBase):
    id: UUID
    created_at: datetime
    is_verified: bool
    dynamic_priority_score: float

    model_config = {"from_attributes": True}
