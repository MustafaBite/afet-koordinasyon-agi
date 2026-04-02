from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from models import RequestStatus, ClusterStatus


class RequestCreate(BaseModel):
    latitude: float
    longitude: float
    need_type: str
    person_count: int = Field(default=1, ge=1)
    description: str | None = None


class RequestResponse(RequestCreate):
    id: UUID
    status: RequestStatus
    created_at: datetime
    is_verified: bool
    model_config = {"from_attributes": True}


class PrioritizedRequestResponse(RequestResponse):
    dynamic_priority_score: float


class StatusUpdate(BaseModel):
    status: RequestStatus


class ClusterLocation(BaseModel):
    district: str | None = None
    neighborhood: str | None = None
    street: str | None = None
    full_address: str | None = None


class StatusSummary(BaseModel):
    pending: int
    assigned: int
    resolved: int


class TaskPackageResponse(BaseModel):
    cluster_id: UUID
    need_type: str
    cluster_name: str
    center_latitude: float
    center_longitude: float
    location: ClusterLocation
    request_count: int
    total_persons_affected: int
    average_priority_score: float
    priority_level: str
    status_summary: StatusSummary
    is_noise_cluster: bool
    status: ClusterStatus
    generated_at: datetime

    model_config = {"from_attributes": True}


class AssignVehicleRequest(BaseModel):
    vehicle_id: UUID
    cluster_id: UUID


class VehicleCreate(BaseModel):
    latitude: float
    longitude: float
    vehicle_type: str
    capacity: str


class VehicleUpdate(BaseModel):
    tent_count: int
    food_count: int
    water_count: int
    medical_count: int
    blanket_count: int



# Authentication Schemas

class UserRegister(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    tc_identity_no: str
    phone: str
    role: str
    expertise_area: str | None = None
    organization: str | None = None
    city: str
    district: str
    profile_photo_url: str | None = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    tc_identity_no: str
    phone: str
    role: str
    expertise_area: str | None
    organization: str | None
    city: str
    district: str
    profile_photo_url: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
