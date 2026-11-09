import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Event

class AuditService:
    GENESIS_HASH = "0" * 64

    @staticmethod
    def _compute_hash(previous_hash: str, event_type: str, payload: dict, mandate_id: str | None, timestamp_str: str) -> str:
        payload_json = json.dumps(payload, sort_keys=True)
        raw_data = f"{previous_hash}|{event_type}|{mandate_id or ''}|{payload_json}|{timestamp_str}"
        return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

    @classmethod
    def record_event(
        cls,
        db: Session,
        event_type: str,
        payload: dict,
        mandate_id: str | None = None
    ) -> Event:
        last_event = db.query(Event).order_by(Event.created_at.desc(), Event.id.desc()).first()
        previous_hash = last_event.current_hash if last_event else cls.GENESIS_HASH

        now = datetime.now(timezone.utc)
        timestamp_str = now.isoformat()

        current_hash = cls._compute_hash(
            previous_hash=previous_hash,
            event_type=event_type,
            payload=payload,
            mandate_id=mandate_id,
            timestamp_str=timestamp_str
        )

        event_id = f"evt_{hashlib.md5(f'{current_hash}{timestamp_str}'.encode('utf-8')).hexdigest()[:16]}"
        event = Event(
            id=event_id,
            mandate_id=mandate_id,
            event_type=event_type,
            payload=payload,
            previous_hash=previous_hash,
            current_hash=current_hash,
            created_at=now
        )

        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @classmethod
    def verify_chain(cls, db: Session) -> tuple[bool, str, int]:
        events = db.query(Event).order_by(Event.created_at.asc(), Event.id.asc()).all()
        if not events:
            return True, "Audit log is empty.", 0

        expected_previous_hash = cls.GENESIS_HASH

        for idx, event in enumerate(events):
            if event.previous_hash != expected_previous_hash:
                return (
                    False,
                    f"Chain broken at event index {idx} (ID: {event.id}). Expected previous hash {expected_previous_hash}, got {event.previous_hash}.",
                    idx
                )

            timestamp_str = event.created_at.isoformat() if event.created_at.tzinfo else event.created_at.replace(tzinfo=timezone.utc).isoformat()
            recalculated_hash = cls._compute_hash(
                previous_hash=event.previous_hash,
                event_type=event.event_type,
                payload=event.payload,
                mandate_id=event.mandate_id,
                timestamp_str=timestamp_str
            )

            if recalculated_hash != event.current_hash:
                return (
                    False,
                    f"Tamper detected at event index {idx} (ID: {event.id}). Stored hash {event.current_hash} does not match computed {recalculated_hash}.",
                    idx
                )

            expected_previous_hash = event.current_hash

        return True, "Audit log chain verification passed.", len(events)