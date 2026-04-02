from sqlalchemy import Boolean, Column, String, Float, DateTime, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
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
    is_verified = Column(Boolean, default=False)
    
    # İlişkiler
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey('app_users.id'), nullable=True)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey('clusters.id'), nullable=True)
    
    # Relationships
    created_by = relationship("User", back_populates="disaster_requests")
    cluster = relationship("Cluster", back_populates="disaster_requests")


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
    is_noise_cluster = Column(Integer, default=0)
    status = Column(Enum(ClusterStatus), default=ClusterStatus.active, nullable=False)
    generated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    
    # İlişkiler
    assigned_team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'), nullable=True)
    
    # Relationships
    assigned_team = relationship("Team", back_populates="assigned_clusters")
    disaster_requests = relationship("DisasterRequest", back_populates="cluster")



class User(Base):
    __tablename__ = "app_users"  # Supabase auth.users ile çakışmaması için

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    tc_identity_no = Column(String(11), unique=True, nullable=False, index=True)
    phone = Column(String(11), nullable=False)
    role = Column(String, nullable=False)  # citizen, volunteer, coordinator, admin
    expertise_area = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    city = Column(String, nullable=False)
    district = Column(String, nullable=False)
    profile_photo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    
    # İlişkiler
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'), nullable=True)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    disaster_requests = relationship("DisasterRequest", back_populates="created_by")


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    
    # Relationships
    members = relationship("User", back_populates="team")
    assigned_clusters = relationship("Cluster", back_populates="assigned_team")
