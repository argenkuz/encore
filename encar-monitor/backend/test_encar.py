import asyncio

import httpx


async def main():
    url = "https://api.encar.com/search/car/list/general"

    params = {
        "count": "true",
        "q": "(And.Hidden.N._.CarType.Y.)",
        "sr": "|ModifiedDate|0|20",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        )
    }

    async with httpx.AsyncClient(
        timeout=20,
        headers=headers,
    ) as client:

        response = await client.get(
            url,
            params=params,
        )

        print("STATUS:", response.status_code)
        print("URL:", response.url)
        print()
        print(response.text[:10000])


if __name__ == "__main__":
    asyncio.run(main())