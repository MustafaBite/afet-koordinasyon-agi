from sqlalchemy import Boolean, Column, String, Float, DateTime, Integer
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
    is_verified = Column(Boolean, default=False)

class ReliefVehicle(Base):
    __tablename__ = "relief_vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = Column(Float)
    longitude = Column(Float)
    vehicle_type = Column(String)
    capacity = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    tent_count = Column(Integer, default=0)
    food_count = Column(Integer, default=0)
    water_count = Column(Integer, default=0)
    medical_count = Column(Integer, default=0)
    blanket_count = Column(Integer, default=0)
