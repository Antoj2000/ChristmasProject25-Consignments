import httpx
import os

ACCOUNTS_API = os.getenv("ACCOUNTS_API")

async def get_next_con_num(account_no: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{ACCOUNTS_API}/api/accounts/{account_no}/currentConNum")
        res.raise_for_status()
        num = res.json()["current_con_num"]

        # increment it after grabbing
        await client.patch(f"{ACCOUNTS_API}/api/accounts/{account_no}/incrementConNum")

        return num