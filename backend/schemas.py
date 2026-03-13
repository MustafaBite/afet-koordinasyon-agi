from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class AfetzedeTalepBase(BaseModel):
    latitude: float
    longitude: float
    need_type: str

class AfetzedeTalepCreate(AfetzedeTalepBase):
    pass

class AfetzedeTalepResponse(AfetzedeTalepBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}

class OncelikliTalepResponse(AfetzedeTalepBase):
    id: UUID
    created_at: datetime
    oncelik_puani: int

    model_config = {"from_attributes": True}
