

from sqlalchemy import Column, String, Float, DateTime, Integer, Enum

from sqlalchemy.dialects.postgresql import UUID
from database import Base
import datetime
import uuid
import enum


class RequestStatus(str, enum.Enum):
    pending = "pending"
    assigned = "assigned"
    resolved = "resolved"


class ClusterStatus(str, enum.Enum):
    active = "active"
    resolved = "resolved"


class DisasterRequest(Base):
    __tablename__ = "disaster_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    need_type = Column(String, nullable=False)
    person_count = Column(Integer, default=1, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    
class ReliefVehicle(Base):
    __tablename__ = "relief_vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = Column(Float)
    longitude = Column(Float)
    vehicle_type = Column(String)
    capacity = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    tent_count = Column(Integer,default=0)
    food_count = Column(Integer,default=0)
    water_count = Column(Integer,default=0)
    medical_count = Column(Integer, default=0)
    blanket_count = Column(Integer, default=0)


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    need_type = Column(String, nullable=False)
    cluster_name = Column(String, nullable=False)
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    district = Column(String, nullable=True)
    neighborhood = Column(String, nullable=True)
    street = Column(String, nullable=True)
    full_address = Column(String, nullable=True)
    request_count = Column(Integer, nullable=False)
    total_persons_affected = Column(Integer, nullable=False)
    average_priority_score = Column(Float, nullable=False)
    priority_level = Column(String, nullable=False)
    pending_count = Column(Integer, default=0)
    assigned_count = Column(Integer, default=0)
    resolved_count = Column(Integer, default=0)
    is_noise_cluster = Column(Integer, default=0)  # 0/1 bool
    status = Column(Enum(ClusterStatus), default=ClusterStatus.active, nullable=False)
    generated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
