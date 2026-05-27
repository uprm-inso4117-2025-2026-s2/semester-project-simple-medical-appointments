from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

class AppointmentStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class SlotStatus(enum.Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    EXPIRED = "EXPIRED"


class UserRole(enum.Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments_as_patient = db.relationship(
        "Appointment", foreign_keys="Appointment.patient_id", back_populates="patient"
    )
    appointments_as_provider = db.relationship(
        "Appointment", foreign_keys="Appointment.provider_id", back_populates="provider"
    )
    time_slots = db.relationship("TimeSlot", back_populates="provider")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role.value,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat(),
        }


class TimeSlot(db.Model):
    __tablename__ = "time_slots"

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(SlotStatus), nullable=False, default=SlotStatus.AVAILABLE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    provider = db.relationship("User", back_populates="time_slots")
    appointment = db.relationship("Appointment", back_populates="time_slot", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status.value,
        }


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey("time_slots.id"), nullable=False)
    status = db.Column(
        db.Enum(AppointmentStatus),
        nullable=False,
        default=AppointmentStatus.ACTIVE,
    )
    cancellation_reason = db.Column(db.Text, nullable=True)
    cancelled_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship("User", foreign_keys=[patient_id], back_populates="appointments_as_patient")
    provider = db.relationship("User", foreign_keys=[provider_id], back_populates="appointments_as_provider")
    time_slot = db.relationship("TimeSlot", back_populates="appointment")
    cancelled_by = db.relationship("User", foreign_keys=[cancelled_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient.full_name if self.patient else None,
            "provider_id": self.provider_id,
            "provider_name": self.provider.full_name if self.provider else None,
            "time_slot": self.time_slot.to_dict() if self.time_slot else None,
            "status": self.status.value,
            "cancellation_reason": self.cancellation_reason,
            "cancelled_by": self.cancelled_by.full_name if self.cancelled_by else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# models/ — define your database models (tables) here.
# Each model typically maps to one database table.
#
# Example using Flask-SQLAlchemy (install it first: pip install flask-sqlalchemy):
#
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()
#
# class Appointment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     patient_name = db.Column(db.String(100), nullable=False)
#     date = db.Column(db.DateTime, nullable=False)
#
# After creating models, import db and call db.init_app(app) in app/__init__.py,
# and run db.create_all() inside an app context to create the tables.

# This is the single shared database connection for the whole project.
# Every model file imports `db` from here: from . import db
