import requests
import pandas as pd
from datetime import datetime

KEYWORDS = [
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack engineer",
    "machine learning engineer",
    "data engineer",
]

def is_software_job(title: str) -> bool:
    title = title.lower()
    return any(keyword in title for keyword in KEYWORDS)


def scrape_greenhouse(company: str):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    jobs = []

    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()

        for job in res.json().get("jobs", []):
            title = job.get("title", "")

            if is_software_job(title):
                jobs.append({
                    "source": "Greenhouse",
                    "company": company,
                    "title": title,
                    "location": job.get("location", {}).get("name"),
                    "url": job.get("absolute_url"),
                    "scraped_at": datetime.now().isoformat(),
                    "updated_at": job.get("updated_at"),
                    "published": job.get("first_published"), 
                    "deadline": job.get("application_deadline") or ""
                })

    except Exception as e:
        print(f"Greenhouse error for {company}: {e}")

    return jobs


def scrape_lever(company: str):
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    jobs = []

    try:
        res = requests.get(url, timeout=10)

        print("URL:", res.url)
        print("Status:", res.status_code)
        print("Text preview:", res.text[:500])

        res.raise_for_status()

        data = res.json()

        print("JSON type:", type(data))
        print("Number of postings:", len(data) if isinstance(data, list) else "not a list")

        if not isinstance(data, list):
            return jobs

        for job in data:
            title = job.get("text", "")

            print("Found title:", title)

            if is_software_job(title):
                jobs.append({
                    "source": "Lever",
                    "company": company,
                    "title": title,
                    "location": job.get("categories", {}).get("location"),
                    "url": job.get("hostedUrl"),
                    "scraped_at": datetime.now().isoformat()
                })

    except Exception as e:
        print(f"Lever error for {company}: {e}")

    return jobs


def scrape_remotive():
    url = "https://remotive.com/api/remote-jobs"
    jobs = []

    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()

        for job in res.json().get("jobs", []):
            title = job.get("title", "")

            if is_software_job(title):
                jobs.append({
                    "source": "Remotive",
                    "company": job.get("company_name"),
                    "title": title,
                    "location": "Remote",
                    "url": job.get("url"),
                    "scraped_at": datetime.now().isoformat(),
                    "updated_at": job.get("updated_at"),
                    "published": job.get("publication_date"),
                    "deadline": job.get("application_deadline") or ""
                })

    except Exception as e:
        print(f"Remotive error: {e}")

    return jobs


def main():
    greenhouse_companies = [
        "airbnb",
        "reddit",
        "stripe",
        "doordash",
    ]

    lever_companies = [
        "netflix",
        "figma",
        "scaleai",
        "benchling",
    ]

    all_jobs = []

    for company in greenhouse_companies:
        all_jobs.extend(scrape_greenhouse(company))

    for company in lever_companies:
        all_jobs.extend(scrape_lever(company))

    all_jobs.extend(scrape_remotive())

    df = pd.DataFrame(all_jobs)

    if not df.empty:
        df = df.drop_duplicates(subset=["company", "title", "url"])
        df.to_csv("software_jobs.csv", index=False)
        print(df.head(20))
        print(f"Saved {len(df)} jobs to software_jobs.csv")
    else:
        print("No jobs found.")


if __name__ == "__main__":
    main()