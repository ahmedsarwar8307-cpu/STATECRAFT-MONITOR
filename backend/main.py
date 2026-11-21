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


# Regional country index. Country names must match the names stored by the
# country-recognition pipeline. A country is assigned to one primary region.
REGION_COUNTRIES = {
    "South Asia": [
        "Afghanistan", "Bangladesh", "Bhutan", "India", "Maldives",
        "Nepal", "Pakistan", "Sri Lanka",
    ],
    "East Asia": [
        "China", "Japan", "Mongolia", "North Korea", "South Korea", "Taiwan",
    ],
    "Southeast Asia": [
        "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar",
        "Philippines", "Singapore", "Thailand", "Timor-Leste", "Vietnam",
    ],
    "Middle East": [
        "Bahrain", "Iran", "Iraq", "Israel", "Jordan", "Kuwait", "Lebanon",
        "Oman", "Palestine", "Qatar", "Saudi Arabia", "Syria", "Turkey",
        "United Arab Emirates", "Yemen",
    ],
    "Europe": [
        "Albania", "Andorra", "Austria", "Belarus", "Belgium",
        "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus",
        "Czech Republic", "Denmark", "Estonia", "Finland", "France",
        "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
        "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg",
        "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands",
        "North Macedonia", "Norway", "Poland", "Portugal", "Romania",
        "Russia", "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain",
        "Sweden", "Switzerland", "Ukraine", "United Kingdom", "Vatican City",
    ],
    "Africa": [
        "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi",
        "Cabo Verde", "Cameroon", "Central African Republic", "Chad",
        "Comoros", "Democratic Republic of the Congo", "Djibouti", "Egypt",
        "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon",
        "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya",
        "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali",
        "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia",
        "Niger", "Nigeria", "Republic of the Congo", "Rwanda",
        "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone",
        "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania",
        "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe",
    ],
    "North America": [
        "Canada", "Mexico", "United States",
    ],
    "Latin America & Caribbean": [
        "Antigua and Barbuda", "Argentina", "Bahamas", "Barbados", "Belize",
        "Bolivia", "Brazil", "Chile", "Colombia", "Costa Rica", "Cuba",
        "Dominica", "Dominican Republic", "Ecuador", "El Salvador",
        "Grenada", "Guatemala", "Guyana", "Haiti", "Honduras", "Jamaica",
        "Nicaragua", "Panama", "Paraguay", "Peru", "Saint Kitts and Nevis",
        "Saint Lucia", "Saint Vincent and the Grenadines", "Suriname",
        "Trinidad and Tobago", "Uruguay", "Venezuela",
    ],
    "Oceania": [
        "Australia", "Fiji", "Kiribati", "Marshall Islands",
        "Micronesia", "Nauru", "New Zealand", "Palau",
        "Papua New Guinea", "Samoa", "Solomon Islands", "Tonga", "Tuvalu",
        "Vanuatu",
    ],
}


# Create the FastAPI application
app = FastAPI(
    title="STATECRAFT MONITOR API",
    description="Backend API for geopolitical news and intelligence.",
    version="1.1.0",
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


def get_published_date(value):
    if not value:
        return None

    try:
        published_date = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            published_date = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except (TypeError, ValueError, OverflowError):
            return None

    return published_date.date().isoformat()


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


def get_region_articles(articles, region_name):
    region_countries = {
        country.casefold()
        for country in REGION_COUNTRIES[region_name]
    }

    matching_articles = []

    for article in articles:
        article_countries = {
            country.casefold()
            for country in parse_field(article.get("countries"))
            if country.casefold() != "unknown"
        }

        matched_countries = article_countries.intersection(region_countries)

        if matched_countries:
            matching_articles.append({
                **article,
                "region_countries": [
                    country for country in REGION_COUNTRIES[region_name]
                    if country.casefold() in matched_countries
                ],
            })

    return matching_articles


def build_region_summary(region_name, matching_articles):
    country_counts = Counter()
    topic_counts = Counter()
    source_counts = Counter()
    coverage_counts = Counter()

    for article in matching_articles:
        country_counts.update(set(article.get("region_countries", [])))
        topic_counts.update(set(parse_field(article.get("topics"))))

        source = article.get("source")
        if source:
            source_counts[source] += 1

        published_date = get_published_date(article.get("published"))
        if published_date:
            coverage_counts[published_date] += 1

    return {
        "region": region_name,
        "article_count": len(matching_articles),
        "country_count": len(country_counts),
        "source_count": len(source_counts),
        "topic_count": len(topic_counts),
        "countries": [
            {"country": country, "article_count": count}
            for country, count in country_counts.most_common()
        ],
        "topics": [
            {"topic": topic, "article_count": count}
            for topic, count in topic_counts.most_common()
        ],
        "sources": [
            {"source": source, "article_count": count}
            for source, count in source_counts.most_common()
        ],
        "coverage_timeline": [
            {"date": date, "article_count": count}
            for date, count in sorted(coverage_counts.items())
        ],
    }


# API homepage
@app.get("/")
def home():
    return {
        "message": "STATECRAFT MONITOR API is operational",
        "version": "1.1.0",
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


# Regional coverage overview
@app.get("/api/regions")
def get_regions():
    articles = get_all_articles()
    region_summaries = []

    for region_name in REGION_COUNTRIES:
        matching_articles = get_region_articles(articles, region_name)
        summary = build_region_summary(region_name, matching_articles)
        region_summaries.append({
            "region": summary["region"],
            "article_count": summary["article_count"],
            "country_count": summary["country_count"],
            "source_count": summary["source_count"],
            "topic_count": summary["topic_count"],
            "top_countries": summary["countries"][:3],
            "top_topics": summary["topics"][:3],
        })

    region_summaries.sort(
        key=lambda item: item["article_count"],
        reverse=True,
    )

    return {
        "total_database_articles": len(articles),
        "regions_with_coverage": sum(
            1 for region in region_summaries if region["article_count"] > 0
        ),
        "region_count": len(region_summaries),
        "regions": region_summaries,
    }


# Detailed analysis for one region
@app.get("/api/regions/{region}")
def get_region_details(region: str):
    matched_region = next(
        (
            name for name in REGION_COUNTRIES
            if name.casefold() == region.casefold()
        ),
        None,
    )

    if not matched_region:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown region: {region}.",
        )

    articles = get_all_articles()
    matching_articles = get_region_articles(articles, matched_region)

    return {
        **build_region_summary(matched_region, matching_articles),
        "database_article_count": len(articles),
        "articles": matching_articles,
    }


# Retrieve intelligence and news associated with one country
@app.get("/api/countries/{country}")
def get_country_details(country: str):
    articles = get_all_articles()

    matching_articles = [
        article for article in articles
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

    topic_counts = Counter()
    source_counts = Counter()
    coverage_counts = Counter()

    for article in matching_articles:
        topics = set(parse_field(article.get("topics")))
        topic_counts.update(topics)

        published_date = get_published_date(article.get("published"))
        if published_date:
            coverage_counts[published_date] += 1

        source = article.get("source")
        if source:
            source_counts[source] += 1

    return {
        "country": country,
        "article_count": len(matching_articles),
        "source_count": len(source_counts),
        "topic_count": len(topic_counts),
        "latest_coverage": matching_articles[0].get("published"),
        "coverage_timeline": [
            {"date": date, "article_count": count}
            for date, count in sorted(coverage_counts.items())
        ],
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
