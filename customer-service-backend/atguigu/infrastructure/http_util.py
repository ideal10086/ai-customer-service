import asyncio

import httpx
from langsmith import AsyncClient

http_client: AsyncClient | None = None
def init_http_client():
    global http_client
    http_client = httpx.AsyncClient()

async def close_http_client():
    await http_client.aclose()

if __name__ == '__main__':
    async def test_get_request():
        init_http_client()
        response = await http_client.get("http://localhost:18081/users/u1001/orders")
        print(response.json())
        await close_http_client()

    asyncio.run(test_get_request())
