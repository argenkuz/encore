from __future__ import annotations

import httpx


ENCAR_API_URL = (
    "https://api.encar.com/search/car/list/general"
)


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
            "sr": (
                f"|ModifiedDate|"
                f"{start}|"
                f"{count}"
            ),
        }


        response = await self.client.get(
            ENCAR_API_URL,
            params=params,
        )


        response.raise_for_status()


        data = response.json()


        return data.get(
            "SearchResults",
            [],
        )


    async def close(self):

        await self.client.aclose()