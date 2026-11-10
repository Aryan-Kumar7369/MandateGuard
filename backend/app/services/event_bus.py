import asyncio
import json
from typing import AsyncGenerator

class EventBus:
    _subscribers: list[asyncio.Queue] = []

    @classmethod
    def subscribe(cls) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        cls._subscribers.append(queue)
        return queue

    @classmethod
    def unsubscribe(cls, queue: asyncio.Queue) -> None:
        if queue in cls._subscribers:
            cls._subscribers.remove(queue)

    @classmethod
    async def publish(cls, event_type: str, payload: dict) -> None:
        message = {"event": event_type, "data": payload}
        for queue in list(cls._subscribers):
            await queue.put(message)

    @classmethod
    async def event_generator(cls, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
        try:
            while True:
                msg = await queue.get()
                yield f"event: {msg['event']}\ndata: {json.dumps(msg['data'])}\n\n"
        except asyncio.CancelledError:
            cls.unsubscribe(queue)