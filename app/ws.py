from fastapi import APIRouter, WebSocket
import aioredis
import os

router = APIRouter()

@router.websocket('/ws/jobs/{job_id}')
async def job_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    redis = await aioredis.create_redis_pool(redis_url)
    res = await redis.subscribe(f'job:{job_id}')
    ch = res[0]
    try:
        while True:
            msg = await ch.get(encoding='utf-8')
            if msg is None:
                continue
            await websocket.send_text(msg)
    except Exception:
        pass
    finally:
        await redis.unsubscribe(f'job:{job_id}')
        redis.close()
        await redis.wait_closed()
