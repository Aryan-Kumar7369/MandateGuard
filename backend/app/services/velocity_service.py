from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models import Event

class VelocityService:
    WINDOW_SECONDS = 60
    MAX_ATTEMPTS = 5

    @classmethod
    def check_velocity(cls, db: Session, mandate_id: str) -> tuple[bool, str]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=cls.WINDOW_SECONDS)
        
        attempt_count = (
            db.query(Event)
            .filter(
                Event.mandate_id == mandate_id,
                Event.event_type == "PRE_FLIGHT_CHECK",
                Event.created_at >= cutoff
            )
            .count()
        )

        if attempt_count >= cls.MAX_ATTEMPTS:
            return True, f"Velocity threshold exceeded: {attempt_count} attempts detected in the last {cls.WINDOW_SECONDS} seconds."
        
        return False, "Velocity within normal operating limits."