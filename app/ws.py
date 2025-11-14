from fastapi import APIRouter, WebSocket
import os
import asyncio
from redis.asyncio import Redis

router = APIRouter()

@router.websocket('/ws/jobs/{job_id}')
async def job_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    redis = Redis.from_url(redis_url)

    pubsub = redis.pubsub()
    await pubsub.subscribe(f'job:{job_id}')

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
            if message:
                await websocket.send_text(message["data"].decode())
            await asyncio.sleep(0.1)
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f'job:{job_id}')
        await redis.close()
