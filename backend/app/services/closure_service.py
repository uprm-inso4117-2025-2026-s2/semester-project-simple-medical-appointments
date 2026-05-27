from datetime import datetime
from ..models import db
from ..models.closure import Closure


def _validate(data: dict) -> dict:
    """Check the incoming data and return a clean version, or raise ValueError."""

    # closure_type must be 'clinic' or 'doctor'
    closure_type = data.get("closure_type", "").strip().lower()
    if closure_type not in ("clinic", "doctor"):
        raise ValueError("'closure_type' must be 'clinic' or 'doctor'.")

    # doctor_id is required when type is 'doctor'
    doctor_id = data.get("doctor_id")
    if closure_type == "doctor":
        if doctor_id is None:
            raise ValueError("'doctor_id' is required when closure_type is 'doctor'.")
        doctor_id = int(doctor_id)
    else:
        doctor_id = None  
  
    try:
        start_dt = datetime.fromisoformat(data["start_datetime"])
        end_dt   = datetime.fromisoformat(data["end_datetime"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("'start_datetime' and 'end_datetime' must be ISO-8601 strings")

    if end_dt <= start_dt:
        raise ValueError("'end_datetime' must be after 'start_datetime'.")

    description = (data.get("description") or "").strip() or None

    return {
        "closure_type":  closure_type,
        "doctor_id":     doctor_id,
        "start_datetime": start_dt,
        "end_datetime":   end_dt,
        "description":   description,
    }


def create_closure(data: dict) -> Closure:
    """Validate and save a new closure. Raises ValueError if data is invalid."""
    clean = _validate(data)
    closure = Closure(**clean)
    db.session.add(closure)
    db.session.commit()
    return closure


def list_closures(closure_type=None, doctor_id=None) -> list:
    """Return all closures, can be filtered by type and/or doctor."""
    query = Closure.query
    if closure_type:
        query = query.filter_by(closure_type=closure_type.lower())
    if doctor_id is not None:
        query = query.filter_by(doctor_id=doctor_id)
    return query.order_by(Closure.start_datetime).all()


def get_closure(closure_id: int) -> Closure | None:
    """Return a single closure by id, or None if it doesn't exist."""
    return db.session.get(Closure, closure_id)


def delete_closure(closure_id: int) -> bool:
    """Delete a closure. Returns True if deleted, False if it wasn't found."""
    closure = db.session.get(Closure, closure_id)
    if closure is None:
        return False
    db.session.delete(closure)
    db.session.commit()
    return True


def is_blocked(start: datetime, end: datetime, doctor_id: int) -> tuple:
    """
    Check if a proposed appointment window overlaps with any closure.

    Returns (True, reason) if blocked, or (False, None) if it's fine.

    An appointment is blocked if:
      - A clinic-wide closure overlaps the window
      - A doctor-specific closure for this doctor overlaps the window.
    """
    overlapping = Closure.query.filter(
        Closure.start_datetime < end,   
        Closure.end_datetime   > start,  
        db.or_(
            Closure.closure_type == "clinic",
            db.and_(
                Closure.closure_type == "doctor",
                Closure.doctor_id == doctor_id,
            ),
        ),
    ).first()

    if overlapping is None:
        return False, None

    if overlapping.closure_type == "clinic":
        reason = f"The clinic is closed from {overlapping.start_datetime} to {overlapping.end_datetime}."
    else:
        reason = f"Doctor {doctor_id} is unavailable from {overlapping.start_datetime} to {overlapping.end_datetime}."

    if overlapping.description:
        reason += f" Reason: {overlapping.description}"

    return True, reason