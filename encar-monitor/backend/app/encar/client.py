from __future__ import annotations

import asyncio
import httpx


ENCAR_API_URL = "https://api.encar.com/search/car/list/general"
ENCAR_VEHICLE_URL = "https://api.encar.com/v1/readside/vehicle"


class EncarClient:

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=10.0),
            trust_env=False,
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
        page = await self.search_page(query=query, start=start, count=count)
        return page["results"]

    async def search_page(
        self,
        query: str,
        start: int = 0,
        count: int = 50,
    ) -> dict:
        params = {
            "count": "true",
            "q": query,
            "sr": f"|ModifiedDate|{start}|{count}",
        }

        last_error = None

        for attempt in range(3):
            try:
                response = await self.client.get(
                    ENCAR_API_URL,
                    params=params,
                )
            except (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.RemoteProtocolError,
            ) as error:
                last_error = error
                if attempt == 2:
                    raise
                await asyncio.sleep(1 * (attempt + 1))
                continue

            if response.status_code == 407:
                # Diagnostic only: expose headers that identify whether the
                # 407 response came through a proxy/gateway.
                interesting_headers = {
                    key: value
                    for key, value in response.headers.items()
                    if key.lower()
                    in {
                        "server",
                        "via",
                        "proxy-authenticate",
                        "www-authenticate",
                        "x-cache",
                        "x-cache-hits",
                        "cf-ray",
                        "x-served-by",
                        "x-cache-status",
                        "age",
                        "location",
                    }
                }
                body_preview = response.text[:500].replace("\n", " ")
                raise RuntimeError(
                    "Encar returned HTTP 407 Proxy Authentication Required. "
                    "Proxy environment variables are disabled for this client. "
                    f"request_start={start}; request_count={count}; "
                    f"response_headers={interesting_headers}; "
                    f"body_preview={body_preview!r}"
                )

            if response.status_code == 429:
                if attempt == 2:
                    response.raise_for_status()
                await asyncio.sleep(2 * (attempt + 1))
                continue

            if response.status_code in {502, 503, 504}:
                if attempt == 2:
                    response.raise_for_status()
                await asyncio.sleep(1 * (attempt + 1))
                continue

            response.raise_for_status()
            break
        else:
            if last_error is not None:
                raise last_error

        data = response.json()

        return {
            "results": data.get("SearchResults", []),
            "total": int(data.get("Count", 0) or 0),
        }

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
