import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import pandas as pd
import requests


# ============================================================
# 1. NEWS SOURCES AND COLLECTION SETTINGS
# ============================================================

NEWS_SOURCES = {
    "BBC": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "Deutsche Welle": "https://rss.dw.com/xml/rss-en-all",
    "France 24": "https://www.france24.com/en/rss",
    "Euronews": "https://www.euronews.com/rss",
    "Sky News": "https://feeds.skynews.com/feeds/rss/world.xml",
    "NPR": "https://feeds.npr.org/1004/rss.xml",
}

ARTICLES_PER_SOURCE = 15
REQUEST_TIMEOUT = (10, 25)
MAX_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 2

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
RAW_FOLDER = PROJECT_FOLDER / "data" / "raw"
OUTPUT_FILE = RAW_FOLDER / "news.csv"
REPORT_FILE = RAW_FOLDER / "collection_report.json"


# ============================================================
# 2. NORMALIZATION HELPERS
# ============================================================

def normalize_link(link):
    """Remove URL fragments and common tracking parameters safely."""
    if not link:
        return ""

    try:
        parts = urlsplit(str(link).strip())
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            return str(link).strip()

        tracking_parameters = {
            "fbclid",
            "gclid",
            "mc_cid",
            "mc_eid",
            "ref_src",
        }

        query = [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith("utm_")
            and key.lower() not in tracking_parameters
        ]

        path = parts.path.rstrip("/") or "/"

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            urlencode(query, doseq=True),
            "",
        ))
    except (TypeError, ValueError):
        return str(link).strip()


def normalize_published_date(entry):
    """Prefer feedparser's parsed date and store a consistent UTC ISO value."""
    parsed_value = (
        entry.get("published_parsed")
        or entry.get("updated_parsed")
    )

    if parsed_value:
        try:
            published = datetime(
                *parsed_value[:6],
                tzinfo=timezone.utc,
            )
            return published.isoformat(timespec="seconds")
        except (TypeError, ValueError, OverflowError):
            pass

    raw_value = entry.get("published") or entry.get("updated") or ""

    if raw_value:
        try:
            published = parsedate_to_datetime(raw_value)
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            return published.astimezone(timezone.utc).isoformat(
                timespec="seconds"
            )
        except (TypeError, ValueError, OverflowError):
            # Keep the publisher's original value; the API can still parse
            # common RSS date formats and will safely ignore invalid dates.
            return str(raw_value).strip()

    return ""


# ============================================================
# 3. COLLECT ONE SOURCE WITH A LIMITED RETRY
# ============================================================

def collect_source(source_name, rss_url):
    result = {
        "source": source_name,
        "status": "failed",
        "attempts": 0,
        "http_status": None,
        "feed_entries": 0,
        "accepted_articles": 0,
        "skipped_entries": 0,
        "warning": None,
        "error": None,
    }

    for attempt in range(1, MAX_ATTEMPTS + 1):
        result["attempts"] = attempt

        try:
            response = requests.get(
                rss_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; "
                        "StatecraftMonitor/1.0; RSS reader)"
                    ),
                    "Accept": (
                        "application/rss+xml, application/atom+xml, "
                        "application/xml, text/xml;q=0.9, */*;q=0.8"
                    ),
                },
                timeout=REQUEST_TIMEOUT,
            )

            result["http_status"] = response.status_code
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            result["feed_entries"] = len(feed.entries)

            if feed.bozo:
                result["warning"] = str(feed.bozo_exception)

            articles = []

            for entry in feed.entries[:ARTICLES_PER_SOURCE]:
                title = str(entry.get("title") or "").strip()
                link = normalize_link(entry.get("link") or "")

                if not title or not link:
                    result["skipped_entries"] += 1
                    continue

                articles.append({
                    "source": source_name,
                    "title": title,
                    "published": normalize_published_date(entry),
                    "link": link,
                })

            result["accepted_articles"] = len(articles)

            if not feed.entries:
                result["status"] = "empty"
            elif not articles:
                result["status"] = "no_valid_articles"
            elif feed.bozo:
                result["status"] = "partial"
            else:
                result["status"] = "ok"

            return articles, result

        except requests.exceptions.RequestException as error:
            result["error"] = str(error)
        except Exception as error:
            # Isolate unexpected source-specific errors so one feed cannot
            # stop collection from every other publisher.
            result["error"] = f"{type(error).__name__}: {error}"

        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS * attempt)

    return [], result


# ============================================================
# 4. RUN THE COLLECTION
# ============================================================

def main():
    RAW_FOLDER.mkdir(parents=True, exist_ok=True)

    collected_articles = []
    source_results = []

    print("\n========== STATECRAFT MONITOR ==========")
    print("          NEWS COLLECTION")
    print("========================================")

    for source_name, rss_url in NEWS_SOURCES.items():
        print(f"\nCollecting news from {source_name}...")

        articles, source_result = collect_source(
            source_name,
            rss_url,
        )

        collected_articles.extend(articles)
        source_results.append(source_result)

        if source_result["status"] in {"ok", "partial"}:
            print(
                f"[OK] {source_name}: "
                f"{source_result['accepted_articles']} articles"
            )
        else:
            print(
                f"[WARNING] {source_name}: "
                f"{source_result['status']} "
                f"({source_result['error'] or 'No valid entries'})"
            )

        if source_result["warning"]:
            print(f"  Feed parsing warning: {source_result['warning']}")

    columns = ["source", "title", "published", "link"]
    df = pd.DataFrame(collected_articles, columns=columns)

    before_deduplication = len(df)
    if not df.empty:
        df = df.drop_duplicates(subset=["link"]).copy()
    duplicates_removed = before_deduplication - len(df)

    # A completely failed collection must never replace a previously
    # usable raw dataset with an empty CSV.
    dataset_updated = False

    if not df.empty:
        df.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig",
        )
        dataset_updated = True
    elif OUTPUT_FILE.exists():
        print(
            "\nWARNING: No valid articles were collected. "
            "The previous raw dataset has been preserved."
        )
    else:
        # Create a correctly structured empty file on the first-ever run.
        df.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig",
        )
        dataset_updated = True

    successful_sources = sum(
        1 for item in source_results
        if item["status"] in {"ok", "partial"}
    )
    failed_sources = [
        item["source"]
        for item in source_results
        if item["status"] not in {"ok", "partial"}
    ]

    report = {
        "collected_at": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ),
        "configured_sources": len(NEWS_SOURCES),
        "successful_sources": successful_sources,
        "failed_or_empty_sources": len(failed_sources),
        "articles_before_deduplication": before_deduplication,
        "duplicates_removed": duplicates_removed,
        "unique_articles_collected": len(df),
        "dataset_updated": dataset_updated,
        "dataset_path": str(OUTPUT_FILE),
        "sources": source_results,
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n========== COLLECTION REPORT ==========")
    print(f"Sources configured: {len(NEWS_SOURCES)}")
    print(f"Sources returning valid articles: {successful_sources}")
    print(f"Failed or empty sources: {len(failed_sources)}")
    print(f"Articles before deduplication: {before_deduplication}")
    print(f"Duplicate links removed: {duplicates_removed}")
    print(f"Unique articles collected: {len(df)}")
    print(f"Raw dataset updated: {'Yes' if dataset_updated else 'No'}")

    if failed_sources:
        print("\nSources requiring attention:")
        for source in failed_sources:
            print(f"  - {source}")

    print(f"\nRaw dataset: {OUTPUT_FILE}")
    print(f"Collection report: {REPORT_FILE}")
    print("\n========================================")


if __name__ == "__main__":
    main()
