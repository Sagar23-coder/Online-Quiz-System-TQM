import asyncio
import sys
from pathlib import Path

backend_dir = Path(r"c:\Users\Asus\ONLINE QUIZ SYSTEM\QuizFlow\backend")
sys.path.insert(0, str(backend_dir))

from httpx import ASGITransport, AsyncClient
from app.main import app

async def main():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        print("Status:", res.status_code)
        print("JSON:", res.json())

if __name__ == "__main__":
    asyncio.run(main())
