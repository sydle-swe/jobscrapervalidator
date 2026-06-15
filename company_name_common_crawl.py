import json
import re
import time
import requests
import pandas as pd
from tqdm import tqdm

COMMON_CRAWL_INDEX = "https://index.commoncrawl.org/CC-MAIN-2025-38-index"

QUERIES = [
    {
        "url": "*.greenhouse.io/*",
        "matchType": "domain",
    }
]

SLUG_PATTERNS = [
    r"https?://boards\.greenhouse\.io/([^/?#]+)",
    r"https?://job-boards\.greenhouse\.io/([^/?#]+)",
]

BAD_SLUGS = {
    "embed",
    "job_app",
    "jobs",
    "departments",
    "offices",
    "questions",
}


def query_common_crawl(query):
    params = {
        "url": query["url"],
        "matchType": query["matchType"],
        "output": "json",
        "fl": "url",
        "collapse": "urlkey",
        "filter": "url:.*(boards\\.greenhouse\\.io|job-boards\\.greenhouse\\.io).*",
    }

    res = requests.get(COMMON_CRAWL_INDEX, params=params, timeout=60)

    print("Request URL:", res.url)
    print("Status:", res.status_code)

    if res.status_code != 200:
        print(res.text[:500])
        return []

    return res.text.splitlines()

def extract_slug(line):
    try:
        data = json.loads(line)
        url = data.get("url", "")
    except Exception:
        url = line

    for pattern in SLUG_PATTERNS:
        match = re.search(pattern, url)
        if match:
            slug = match.group(1).lower().strip()

            if slug and slug not in BAD_SLUGS:
                return slug

    return None


def validate_greenhouse_slug(slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

    try:
        res = requests.get(url, timeout=15)

        if res.status_code == 200:
            data = res.json()
            return {
                "company_slug": slug,
                "source": "Greenhouse",
                "job_count": len(data.get("jobs", [])),
                "api_url": url,
                "board_url": f"https://boards.greenhouse.io/{slug}",
            }

    except Exception:
        pass

    return None


def main():
    discovered_slugs = set()

    for query in QUERIES:
        print(f"Searching Common Crawl for: {query['url']}")

        lines = query_common_crawl(query)

        print(f"Returned {len(lines)} rows")

        for line in lines:
            slug = extract_slug(line)
            if slug:
                discovered_slugs.add(slug)

        time.sleep(1)

    print(f"Discovered {len(discovered_slugs)} possible Greenhouse slugs")

    if not discovered_slugs:
        print("No possible Greenhouse slugs discovered.")
        df = pd.DataFrame(columns=[
            "company_slug",
            "source",
            "job_count",
            "api_url",
            "board_url",
        ])
        df.to_csv("greenhouse_companies.csv", index=False)
        return

    valid_companies = []

    for slug in tqdm(sorted(discovered_slugs)):
        result = validate_greenhouse_slug(slug)

        if isinstance(result, dict):
            valid_companies.append(result)

        time.sleep(0.15)

    df = pd.DataFrame(valid_companies)

    if df.empty or "job_count" not in df.columns:
        print("No valid Greenhouse companies found or job_count missing.")
        df = pd.DataFrame(columns=[
            "company_slug",
            "source",
            "job_count",
            "api_url",
            "board_url",
        ])
        df.to_csv("greenhouse_companies.csv", index=False)
        return

    df = df.sort_values(by="job_count", ascending=False)
    df.to_csv("greenhouse_companies.csv", index=False)

    print(f"Saved {len(df)} valid Greenhouse companies")
    print(df.head(20))


if __name__ == "__main__":
    main()