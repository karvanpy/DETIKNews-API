from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn
import httpx
import asyncio
from selectolax.parser import HTMLParser
from typing import List, Dict, Union

app = FastAPI()


# Define the data model for the parsed result
class ScrapeResult(BaseModel):
    title: str
    url: str
    date: str
    desc: str
    content: str


async def fetch_page(url: str, params: dict, headers: dict) -> Union[str, None]:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url, params=params, headers=headers, timeout=10.0
            )
            return response.text
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, detail=f"Timeout: unable to connect to {url}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=response.status_code, detail=str(e))


async def parse_content(url: str) -> str:
    html = await fetch_page(url, {}, {})
    parser = HTMLParser(html)
    paragraphs = [p.text() for p in parser.css("div.detail__body-text > p")]
    return "\n".join(paragraphs) if paragraphs else "No content available."


async def parse_item(result) -> Dict[str, str]:
    title = result.css_first("h3.media__title").text()
    date = result.css_first(".media__date > span").attrs["title"]
    url = result.css_first("a").attrs["href"]
    desc_element = result.css_first("div.media__desc")
    desc = desc_element.text() if desc_element else "No description"
    content = await parse_content(url)
    return {
        "title": title.strip(),
        "url": url,
        "date": date,
        "desc": desc.strip(),
        "content": content,
    }


async def parse(url: str, params: dict, headers: dict) -> List[Dict[str, str]]:
    html = await fetch_page(url, params, headers)
    if not html:
        return []
    parser = HTMLParser(html)
    search_results = parser.css("article")
    return await asyncio.gather(*[parse_item(result) for result in search_results])


async def fetch_json(url: str, headers: dict = None) -> Union[Dict, None]:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, detail=f"Timeout: unable to connect to {url}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=response.status_code, detail=str(e))


async def get_trending_keywords(api_url: str, headers: dict) -> List[str]:
    json_data = await fetch_json(api_url, headers)
    if (
        not json_data
        or "body" not in json_data
        or "topKeywordSearch" not in json_data["body"]
    ):
        return []
    return [item["keyword"] for item in json_data["body"]["topKeywordSearch"]]


@app.get("/trending_keywords", response_model=List[str])
async def trending_keywords():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/244.178.44.111 Safari/537.36",
    }
    api_url = "https://explore-api.detik.com/trending"
    return await get_trending_keywords(api_url, headers)


@app.get("/scrape", response_model=List[ScrapeResult])
async def scrape(
    keyword: str = Query(..., description="Keyword to search for"),
    pages: int = Query(1, ge=1),
):
    search_url = "https://www.detik.com/search/searchall?"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/244.178.44.111 Safari/537.36",
    }
    all_items = []
    for page in range(1, pages + 1):
        params = {"query": keyword, "page": page}
        items = await parse(search_url, params, headers)
        all_items.extend(items)
    return all_items


@app.get("/")
async def root():
    return {
        "message": "Welcome to the DETIKScraper API!",
        "description": "An API for scraping search results and fetching trending keywords from Detik.",
        "endpoints": {
            "/trending_keywords": {
                "method": "GET",
                "description": "Retrieve a list of trending keywords.",
            },
            "/scrape": {
                "method": "GET",
                "description": "Scrape search results for a specific keyword.",
                "parameters": {
                    "keyword": "str (required) - The search term to scrape.",
                    "pages": "int (optional) - The number of pages to scrape, defaults to 1.",
                },
            },
        },
        "documentation": "Link to detailed documentation if available, e.g., /docs or /redoc",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
