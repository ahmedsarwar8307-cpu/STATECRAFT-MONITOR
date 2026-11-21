
import requests
import feedparser
import pandas as pd

from pathlib import Path


# --------------------------------
# 1. NEWS SOURCES
# --------------------------------

NEWS_SOURCES = {
    "BBC": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "Deutsche Welle": "https://rss.dw.com/xml/rss-en-all",
    "France 24": "https://www.france24.com/en/rss",
    "Euronews": "https://www.euronews.com/rss",
    "Sky News": "https://feeds.skynews.com/feeds/rss/world.xml",
    "NPR": "https://feeds.npr.org/1004/rss.xml"
}


# --------------------------------
# 2. STORE COLLECTED ARTICLES
# --------------------------------

articles = []

successful_sources = []
failed_sources = []


# --------------------------------
# 3. COLLECT NEWS FROM EACH SOURCE
# --------------------------------

for source_name, rss_url in NEWS_SOURCES.items():

    print(f"\nCollecting news from {source_name}...")

    try:
        response = requests.get(
            rss_url,
            headers={
                "User-Agent": "StatecraftMonitor/1.0 (RSS news aggregator)"
            },
            timeout=30
        )

        # Check whether the request was successful
        response.raise_for_status()

        # Parse the RSS feed
        feed = feedparser.parse(response.content)

        # Check whether the feed has a parsing problem
        if feed.bozo:
            print(
                f"WARNING: {source_name} feed may be malformed: "
                f"{feed.bozo_exception}"
            )

        source_count = 0

        # Check whether the feed contains articles
        if not feed.entries:
            print(f"WARNING: No articles found in {source_name}")
            failed_sources.append(source_name)
            continue

        # Extract the first 15 articles
        for entry in feed.entries[:15]:

            article = {
                "source": source_name,
                "title": entry.get("title", "No title"),
                "published": entry.get("published", "Unknown date"),
                "link": entry.get("link", "")
            }

            # Ignore articles without a link
            if article["link"]:
                articles.append(article)
                source_count += 1

        print(f"Collected {source_count} articles from {source_name}")

        # Track successful and unsuccessful sources
        if source_count > 0:
            successful_sources.append(source_name)
        else:
            failed_sources.append(source_name)

    except requests.exceptions.RequestException as error:

        print(f"Could not collect news from {source_name}: {error}")
        failed_sources.append(source_name)


# --------------------------------
# 4. CONVERT INTO A PANDAS DATAFRAME
# --------------------------------

columns = ["source", "title", "published", "link"]

df = pd.DataFrame(articles, columns=columns)


# --------------------------------
# 5. REMOVE DUPLICATE ARTICLES
# --------------------------------

df = df.drop_duplicates(subset=["link"])


# --------------------------------
# 6. SAVE DATASET AS CSV
# --------------------------------

project_folder = Path(__file__).resolve().parent.parent

output_folder = project_folder / "data" / "raw"

output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "news.csv"

df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig",
    sep=","
)


# --------------------------------
# 7. DISPLAY RESULTS
# --------------------------------

print("\n========== STATECRAFT MONITOR ==========")
print("          NEWS COLLECTION REPORT")
print("========================================")

print(f"\nTotal unique articles: {len(df)}")

print(f"\nSuccessful sources: {len(successful_sources)}")

for source in successful_sources:
    print(f"  [OK] {source}")

print(f"\nFailed sources: {len(failed_sources)}")

for source in failed_sources:
    print(f"  [FAILED] {source}")

print("\nArticles by source:")

if not df.empty:
    print(df["source"].value_counts().to_string())
else:
    print("No articles collected.")

print(f"\nDataset saved at:\n{output_file}")

print("\n========================================")
