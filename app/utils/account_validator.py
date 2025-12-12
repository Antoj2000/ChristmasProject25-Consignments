import httpx
from fastapi import HTTPException
import os

ACCOUNTS_API = os.getenv("ACCOUNTS_API")

def validate_account_exists(account_no: str):
    
    url = f"{ACCOUNTS_API}/api/accounts/{account_no}"  

    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(url)
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Accounts service unavailable"
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=400,
            detail=f"Account '{account_no}' does not exist"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Unknown error validating account"
        )

    return True