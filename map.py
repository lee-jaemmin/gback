import os

import requests
from fastapi import HTTPException


def geocode_address(address: str):
    client_id = os.getenv("NAVER_MAP_CLIENT_ID", "").strip()
    client_secret = os.getenv("NAVER_MAP_SECRET", "").strip()

    if not client_id or not client_secret:
        raise RuntimeError("Naver Map credentials are not configured")

    response = requests.get(
        "https://maps.apigw.ntruss.com/map-geocode/v2/geocode",
        params={"query": address},
        headers={
            "x-ncp-apigw-api-key-id": client_id,
            "x-ncp-apigw-api-key": client_secret,
        },
        timeout=5,
    )

    response.raise_for_status()
    return response.json()
