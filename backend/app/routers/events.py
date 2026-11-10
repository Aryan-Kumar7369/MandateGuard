from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.event_bus import EventBus

router = APIRouter(prefix="/api/v1/events", tags=["Realtime Events"])

@router.get("/stream")
async def stream_live_events():
    queue = EventBus.subscribe()
    return StreamingResponse(
        EventBus.event_generator(queue),
        media_type="text/event-stream"
    )