import uuid
import enum
from typing import Optional
from sqlalchemy import String, Boolean, ForeignKey, Float, Text, Enum as SQLEnum, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geography

from app.db.base import Base

class UserRole(str, enum.Enum):
    customer = "customer"
    mechanic = "mechanic"
    admin = "admin"

class RequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    completed = "completed"
    cancelled = "cancelled"

class NotificationType(str, enum.Enum):
    new_repair_request = "new_repair_request"
    request_accepted = "request_accepted"
    request_rejected = "request_rejected"
    status_changed = "status_changed"
    new_message = "new_message"
    repair_completed = "repair_completed"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.customer)
    full_name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    vehicles = relationship("Vehicle", back_populates="customer", cascade="all, delete-orphan")
    mechanic_profile = relationship("MechanicProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    repair_requests = relationship("RepairRequest", foreign_keys="[RepairRequest.customer_id]", back_populates="customer")
    messages = relationship("Message", back_populates="sender")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    reviews_given = relationship("Review", foreign_keys="[Review.customer_id]", back_populates="customer")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    make: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)

    customer = relationship("User", back_populates="vehicles")
    repair_requests = relationship("RepairRequest", back_populates="vehicle")

class MechanicProfile(Base):
    __tablename__ = "mechanic_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    shop_name: Mapped[str] = mapped_column(String)
    location = mapped_column(Geography(geometry_type='POINT', srid=4326))
    address: Mapped[str] = mapped_column(String)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)

    user = relationship("User", back_populates="mechanic_profile")
    mechanic_services = relationship("MechanicService", back_populates="mechanic", cascade="all, delete-orphan")
    repair_requests = relationship("RepairRequest", foreign_keys="[RepairRequest.mechanic_id]", back_populates="mechanic")
    reviews_received = relationship("Review", foreign_keys="[Review.mechanic_id]", back_populates="mechanic")

class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True)
    category: Mapped[str] = mapped_column(String)

    mechanic_services = relationship("MechanicService", back_populates="service", cascade="all, delete-orphan")

class MechanicService(Base):
    __tablename__ = "mechanic_services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mechanic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mechanic_profiles.id", ondelete="CASCADE"))
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"))
    base_price: Mapped[float] = mapped_column(Float)

    mechanic = relationship("MechanicProfile", back_populates="mechanic_services")
    service = relationship("Service", back_populates="mechanic_services")

class RepairRequest(Base):
    __tablename__ = "repair_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    mechanic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mechanic_profiles.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[RequestStatus] = mapped_column(SQLEnum(RequestStatus), default=RequestStatus.pending)
    description: Mapped[str] = mapped_column(Text)
    customer_location = mapped_column(Geography(geometry_type='POINT', srid=4326))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("User", foreign_keys=[customer_id], back_populates="repair_requests")
    vehicle = relationship("Vehicle", back_populates="repair_requests")
    mechanic = relationship("MechanicProfile", foreign_keys=[mechanic_id], back_populates="repair_requests")
    ai_diagnosis = relationship("AIDiagnosis", back_populates="repair_request", uselist=False, cascade="all, delete-orphan")
    images = relationship("RequestImage", back_populates="repair_request", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="repair_request", cascade="all, delete-orphan")
    review = relationship("Review", back_populates="repair_request", uselist=False, cascade="all, delete-orphan")

class AIDiagnosis(Base):
    __tablename__ = "ai_diagnoses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repair_requests.id", ondelete="CASCADE"), unique=True)
    possible_faults = mapped_column(JSONB)
    urgency: Mapped[str] = mapped_column(String)
    ai_summary: Mapped[str] = mapped_column(Text)

    repair_request = relationship("RepairRequest", back_populates="ai_diagnosis")

class RequestImage(Base):
    __tablename__ = "request_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repair_requests.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(String)

    repair_request = relationship("RepairRequest", back_populates="images")

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repair_requests.id", ondelete="CASCADE"))
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    repair_request = relationship("RepairRequest", back_populates="messages")
    sender = relationship("User", back_populates="messages")

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repair_requests.id", ondelete="CASCADE"), unique=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    mechanic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mechanic_profiles.id", ondelete="CASCADE"))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text)

    repair_request = relationship("RepairRequest", back_populates="review")
    customer = relationship("User", foreign_keys=[customer_id], back_populates="reviews_given")
    mechanic = relationship("MechanicProfile", foreign_keys=[mechanic_id], back_populates="reviews_received")

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType, name="notificationtype"), index=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    reference_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="notifications")