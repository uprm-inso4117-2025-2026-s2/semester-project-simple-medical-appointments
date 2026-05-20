"""
Seed script to populate the database with test appointments.

Run with: python seed.py
"""

from datetime import datetime, timedelta
from app import create_app
from app.models import db, User, UserRole, TimeSlot, Appointment, AppointmentStatus, SlotStatus

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    
    print("Creating users...")
    
    admin = User(
        email="admin@clinic.com",
        password_hash="password123",  
        role=UserRole.ADMIN,
        full_name="System Administrator"
    )
    
    dr_morales = User(
        email="dr.morales@clinic.com",
        password_hash="password123",
        role=UserRole.DOCTOR,
        full_name="Dr. Juan Morales"
    )
    
    dr_rivera = User(
        email="dr.rivera@clinic.com",
        password_hash="password123",
        role=UserRole.DOCTOR,
        full_name="Dr. Carmen Rivera"
    )
    
    patient1 = User(
        email="pepe.fulano@mail.com",
        password_hash="password123",
        role=UserRole.PATIENT,
        full_name="Pepe Fulano"
    )
    
    patient2 = User(
        email="juan.carolina@mail.com",
        password_hash="password123",
        role=UserRole.PATIENT,
        full_name="Juan Carolina"
    )
    
    patient3 = User(
        email="pedro.piedra@mail.com",
        password_hash="password123",
        role=UserRole.PATIENT,
        full_name="Pedro Piedra"
    )
    
    db.session.add_all([admin, dr_morales, dr_rivera, patient1, patient2, patient3])
    db.session.commit()
    
    print("Creating time slots...")
    
    # Create time slots for next week
    base_date = datetime.now() + timedelta(days=7)
    slots = []
    
    for day_offset in range(5):  # Monday - Friday
        for hour in [9, 10, 11, 14, 15, 16]:  # Morning and afternoon
            slot_time = base_date.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
            
            slot = TimeSlot(
                provider_id=dr_morales.id,
                start_time=slot_time,
                end_time=slot_time + timedelta(minutes=30),
                status=SlotStatus.AVAILABLE
            )
            slots.append(slot)
    
    db.session.add_all(slots)
    db.session.commit()
    
    print("Creating appointments...")
    
    appt1 = Appointment(
        patient_id=patient1.id,
        provider_id=dr_morales.id,
        time_slot_id=slots[0].id,
        status=AppointmentStatus.ACTIVE
    )
    slots[0].status = SlotStatus.RESERVED
    
    appt2 = Appointment(
        patient_id=patient2.id,
        provider_id=dr_morales.id,
        time_slot_id=slots[1].id,
        status=AppointmentStatus.CONFIRMED
    )
    slots[1].status = SlotStatus.RESERVED
    
    appt3 = Appointment(
        patient_id=patient3.id,
        provider_id=dr_morales.id,
        time_slot_id=slots[2].id,
        status=AppointmentStatus.CANCELLED,
        cancellation_reason="Patient requested cancellation",
        cancelled_by_id=admin.id,
        cancelled_at=datetime.now() - timedelta(days=1)
    )
    slots[2].status = SlotStatus.AVAILABLE  # Slot freed
    
    appt4 = Appointment(
        patient_id=patient1.id,
        provider_id=dr_rivera.id,
        time_slot_id=slots[3].id,
        status=AppointmentStatus.COMPLETED
    )
    slots[3].status = SlotStatus.RESERVED
    
    db.session.add_all([appt1, appt2, appt3, appt4])
    db.session.commit()
    
    print("\n✓ Database seeded successfully!")
    print(f"  - {User.query.count()} users")
    print(f"  - {TimeSlot.query.count()} time slots")
    print(f"  - {Appointment.query.count()} appointments")
    print("\nTest the app at:")
    print("  Frontend: http://localhost:3000/admin/appointments")
    print("  Backend:  http://localhost:5000/api/appointments")
