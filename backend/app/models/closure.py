from . import db
from datetime import datetime, timezone


class Closure(db.Model):
    __tablename__ = "closures"

    id            = db.Column(db.Integer, primary_key=True)
    closure_type  = db.Column(db.String(10), nullable=False)  # 'clinic' or 'doctor'
    doctor_id     = db.Column(db.Integer, nullable=True)       # NULL = clinic-wide
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime   = db.Column(db.DateTime, nullable=False)
    description   = db.Column(db.String(255), nullable=True)   # optional reason
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":             self.id,
            "closure_type":   self.closure_type,
            "doctor_id":      self.doctor_id,
            "start_datetime": self.start_datetime.isoformat(),
            "end_datetime":   self.end_datetime.isoformat(),
            "description":    self.description,
            "created_at":     self.created_at.isoformat(),
        }