import httpx
import os

GAZZING_API = os.getenv("GAZZING_API")

async def resolve_depot_number(area: str) -> int:
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{GAZZING_API}/api/depot",
            json={"addressline4": area}
        )
        res.raise_for_status()
        return res.json()["depot_number"]