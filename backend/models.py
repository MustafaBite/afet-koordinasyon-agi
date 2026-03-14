from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import datetime
import uuid

class DisasterRequest(Base):
    __tablename__ = "disaster_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = Column(Float)
    longitude = Column(Float)
    need_type = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
