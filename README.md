# DETIKNews-API
(Unofficial) DETIKNews-API designed for scraping search results and fetching trending keywords from DETIK.com

Live: https://detik-news-api.vercel.app/

## Features
- **Trending Keywords**: Retrieve a list of trending keywords from DETIK.com.
- **Keywords Search**: Scrapes search results based on a provided keyword and returns article details, such as title, URL, date, description, and content.

## Installation

### Pre-requisites
- Python 3.x
- Libraries: httpx, selectolax, fastapi, uvicorn 

```
python -m pip install httpx selectolax fastapi uvicorn
```

## Run
```bash
uvicorn app:app --reload
```

## Test
[http://localhost:8000/scrape/?keyword=teknologi&pages=10](http://127.0.0.1:8000/scrape/?keyword=teknologi&pages=10)
```bash
curl -X GET "http://localhost:8000/scrape/?keyword=teknologi&pages=10"
```
