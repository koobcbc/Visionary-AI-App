# utils/http_client.py
import asyncio, httpx
from fastapi import HTTPException

class HttpClient:
    def __init__(self, timeout: int = 25, retries: int = 2):
        self.timeout, self.retries = timeout, retries

    async def post_json(self, url: str, payload: dict) -> dict:
        last_err = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.retries + 1):
                try:
                    r = await client.post(url, json=payload)
                    r.raise_for_status()
                    return r.json()
                except Exception as e:
                    last_err = e
                    await asyncio.sleep(0.3 * (attempt + 1))
        raise HTTPException(status_code=502, detail=f"Downstream {url} error: {last_err}")