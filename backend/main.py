
from pathlib import Path
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


# Find the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Locate the existing SQLite database
DATABASE_PATH = BASE_DIR / "database" / "geointel.db"


# Create the FastAPI application
app = FastAPI(
    title="STATECRAFT MONITOR API",
    description="Backend API for geopolitical news and intelligence.",
    version="1.0.0",
)


# Allow our React frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database connection function
def get_database_connection():
    if not DATABASE_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="Database file not found.",
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# Convert comma-separated database values into clean lists
def parse_field(value):
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def get_published_timestamp(value):
    if not value:
        return float("-inf")

    try:
        published_date = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            published_date = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except (TypeError, ValueError, OverflowError):
            return float("-inf")

    if published_date.tzinfo is None:
        published_date = published_date.replace(tzinfo=timezone.utc)

    return published_date.timestamp()


# Retrieve articles from the database
def get_all_articles():
    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        rows = cursor.execute(
            """
            SELECT id, source, title, published, link, countries, topics
            FROM articles
            ORDER BY id DESC
            """
        ).fetchall()

        articles = [dict(row) for row in rows]

        articles.sort(
            key=lambda article: (
                get_published_timestamp(article.get("published")),
                article.get("id", 0),
            ),
            reverse=True,
        )

        return articles

    finally:
        connection.close()


# API homepage
@app.get("/")
def home():
    return {
        "message": "STATECRAFT MONITOR API is operational",
        "version": "1.0.0",
    }


# Retrieve news articles
@app.get("/api/articles")
def get_articles(
    limit: int = Query(default=50, ge=1, le=200),
):
    articles = get_all_articles()

    return {
        "total": min(len(articles), limit),
        "articles": articles[:limit],
    }


# Retrieve country coverage across the database
@app.get("/api/countries")
def get_countries():
    articles = get_all_articles()

    country_counts = Counter()
    articles_with_countries = 0

    for article in articles:
        # A set ensures one article is counted only once per country
        countries = {
            country
            for country in parse_field(article.get("countries"))
            if country.casefold() != "unknown"
        }

        if countries:
            articles_with_countries += 1

        country_counts.update(countries)

    country_list = [
        {
            "country": country,
            "article_count": count,
        }
        for country, count in country_counts.most_common()
    ]

    return {
        "total_articles": len(articles),
        "articles_with_countries": articles_with_countries,
        "country_count": len(country_list),
        "countries": country_list,
    }


# Retrieve intelligence and news associated with one country
@app.get("/api/countries/{country}")
def get_country_details(country: str):
    articles = get_all_articles()

    # Match exact country names, not partial text
    matching_articles = [
        article
        for article in articles
        if any(
            item.casefold() == country.casefold()
            for item in parse_field(article.get("countries"))
        )
    ]

    if not matching_articles:
        raise HTTPException(
            status_code=404,
            detail=f"No articles found for {country}.",
        )

    # Count topics and sources across matching articles
    topic_counts = Counter()
    source_counts = Counter()

    for article in matching_articles:
        topics = set(parse_field(article.get("topics")))
        topic_counts.update(topics)

        source = article.get("source")
        if source:
            source_counts[source] += 1

    return {
        "country": country,
        "article_count": len(matching_articles),
        "source_count": len(source_counts),
        "topic_count": len(topic_counts),
        "latest_coverage": matching_articles[0].get("published"),
        "topics": [
            {"topic": topic, "article_count": count}
            for topic, count in topic_counts.most_common()
        ],
        "sources": [
            {"source": source, "article_count": count}
            for source, count in source_counts.most_common()
        ],
        "articles": matching_articles,
    }
