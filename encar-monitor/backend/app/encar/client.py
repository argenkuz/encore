from __future__ import annotations

import httpx


ENCAR_API_URL = "https://api.encar.com/search/car/list/general"
ENCAR_VEHICLE_URL = "https://api.encar.com/v1/readside/vehicle"


class EncarClient:

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=20.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/140.0.0.0 "
                    "Safari/537.36"
                )
            },
        )

    async def search(
        self,
        query: str,
        start: int = 0,
        count: int = 20,
    ) -> list[dict]:
        params = {
            "count": "true",
            "q": query,
            "sr": f"|ModifiedDate|{start}|{count}",
        }

        response = await self.client.get(
            ENCAR_API_URL,
            params=params,
        )
        response.raise_for_status()

        data = response.json()

        return data.get("SearchResults", [])

    async def get_vehicle_details(self, encar_id: int) -> dict:
        response = await self.client.get(
            f"{ENCAR_VEHICLE_URL}/{encar_id}",
            params={
                "include": "MANAGE,SPEC,CONDITION,ADVERTISEMENT",
            },
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
