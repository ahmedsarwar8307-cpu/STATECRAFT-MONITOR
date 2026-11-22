import json
import hashlib
import os
from pathlib import Path
import sqlite3
from collections import Counter
from datetime import date, datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests


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
    "Central Asia": [
        "Kazakhstan", "Kyrgyzstan", "Tajikistan", "Turkmenistan", "Uzbekistan",
    ],
    "Middle East": [
        "Armenia", "Azerbaijan", "Bahrain", "Georgia", "Iran", "Iraq", "Israel",
        "Jordan", "Kuwait", "Lebanon", "Oman", "Palestine", "Qatar",
        "Saudi Arabia", "Syria", "Turkey",
        "United Arab Emirates", "Yemen",
    ],
    "Europe": [
        "Albania", "Andorra", "Austria", "Belarus", "Belgium",
        "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus",
        "Czechia", "Denmark", "Estonia", "Finland", "France",
        "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
        "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg",
        "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands",
        "North Macedonia", "Norway", "Poland", "Portugal", "Romania",
        "Russia", "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain",
        "Sweden", "Switzerland", "Ukraine", "United Kingdom", "Holy See",
    ],
    "Africa": [
        "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi",
        "Cabo Verde", "Cameroon", "Central African Republic", "Chad",
        "Comoros", "Democratic Republic of the Congo", "Djibouti", "Egypt",
        "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon",
        "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya",
        "Lesotho", "Liberia", "Libya", "Madagascar", "Malawi", "Mali",
        "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia",
        "Niger", "Nigeria", "Congo (Congo-Brazzaville)", "Rwanda",
        "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone",
        "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania",
        "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe",
    ],
    "North America": [
        "Canada", "United States",
    ],
    "Latin America & Caribbean": [
        "Antigua and Barbuda", "Argentina", "Bahamas", "Barbados", "Belize",
        "Bolivia", "Brazil", "Chile", "Colombia", "Costa Rica", "Cuba",
        "Dominica", "Dominican Republic", "Ecuador", "El Salvador",
        "Grenada", "Guatemala", "Guyana", "Haiti", "Honduras", "Jamaica", "Mexico",
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


def build_country_relationships(articles):
    """Count unique article co-mentions for every country pair."""
    pair_articles = {}
    country_counts = Counter()
    multi_country_article_count = 0

    for article in articles:
        countries = sorted({
            country.strip()
            for country in parse_field(article.get("countries"))
            if country.strip() and country.casefold() != "unknown"
        }, key=str.casefold)

        if len(countries) < 2:
            continue

        multi_country_article_count += 1
        country_counts.update(countries)

        for index, country_a in enumerate(countries):
            for country_b in countries[index + 1:]:
                pair_key = (country_a, country_b)
                if pair_key not in pair_articles:
                    pair_articles[pair_key] = {
                        "articles": [],
                        "topics": Counter(),
                        "sources": Counter(),
                    }

                pair_data = pair_articles[pair_key]
                pair_data["articles"].append(article)
                pair_data["topics"].update(set(parse_field(article.get("topics"))))

                source = article.get("source")
                if source:
                    pair_data["sources"][source] += 1

    pairs = []
    for (country_a, country_b), data in pair_articles.items():
        pairs.append({
            "country_a": country_a,
            "country_b": country_b,
            "article_count": len(data["articles"]),
            "topic_count": len(data["topics"]),
            "source_count": len(data["sources"]),
            "top_topics": [
                {"topic": topic, "article_count": count}
                for topic, count in data["topics"].most_common(5)
            ],
            "top_sources": [
                {"source": source, "article_count": count}
                for source, count in data["sources"].most_common(5)
            ],
        })

    pairs.sort(
        key=lambda item: (
            item["article_count"],
            item["country_a"].casefold(),
            item["country_b"].casefold(),
        ),
        reverse=True,
    )

    return {
        "country_count": len(country_counts),
        "countries_with_shared_coverage": len({
            country
            for pair in pair_articles
            for country in pair
        }),
        "articles_with_multiple_countries": multi_country_article_count,
        "total_pairs": len(pairs),
        "pairs": pairs,
    }


def build_coverage_trends(articles, window_days=7):
    """Compare topic and country coverage in two windows ending at latest data date."""
    dated_articles = []
    for article in articles:
        published_date = get_published_date(article.get("published"))
        if published_date:
            dated_articles.append((date.fromisoformat(published_date), article))

    if not dated_articles:
        return {
            "available": False,
            "message": "No valid publication dates are available for trend analysis.",
            "dated_article_count": 0,
            "topics": [],
            "countries": [],
            "timeline": [],
        }

    latest_date = max(item[0] for item in dated_articles)
    recent_start = latest_date - timedelta(days=window_days - 1)
    previous_end = recent_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=window_days - 1)

    def aggregate_dimension(field, start_date, end_date):
        counts = Counter()
        for published_date, article in dated_articles:
            if start_date <= published_date <= end_date:
                values = {
                    value for value in parse_field(article.get(field))
                    if value and value.casefold() != "unknown"
                }
                counts.update(values)
        return counts

    def compare_dimension(field):
        recent = aggregate_dimension(field, recent_start, latest_date)
        previous = aggregate_dimension(field, previous_start, previous_end)
        names = set(recent) | set(previous)
        results = []

        for name in names:
            recent_count = recent.get(name, 0)
            previous_count = previous.get(name, 0)
            difference = recent_count - previous_count

            if previous_count == 0:
                change_percent = None
                status = "new" if recent_count else "no recent coverage"
            else:
                change_percent = round((difference / previous_count) * 100, 1)
                status = "rising" if difference > 0 else (
                    "declining" if difference < 0 else "stable"
                )

            results.append({
                "name": name,
                "recent_count": recent_count,
                "previous_count": previous_count,
                "change": difference,
                "change_percent": change_percent,
                "status": status,
            })

        results.sort(
            key=lambda item: (
                item["recent_count"],
                item["change"],
                item["name"].casefold(),
            ),
            reverse=True,
        )
        return {
            "total": len(results),
            "items": results[:12],
        }

    timeline_start = max(
        min(item[0] for item in dated_articles),
        latest_date - timedelta(days=29),
    )
    daily_counts = Counter(
        published_date.isoformat()
        for published_date, _ in dated_articles
        if timeline_start <= published_date <= latest_date
    )

    recent_article_count = sum(
        1 for published_date, _ in dated_articles
        if recent_start <= published_date <= latest_date
    )
    previous_article_count = sum(
        1 for published_date, _ in dated_articles
        if previous_start <= published_date <= previous_end
    )

    return {
        "available": True,
        "window_days": window_days,
        "latest_data_date": latest_date.isoformat(),
        "recent_window": {
            "start": recent_start.isoformat(),
            "end": latest_date.isoformat(),
            "article_count": recent_article_count,
        },
        "previous_window": {
            "start": previous_start.isoformat(),
            "end": previous_end.isoformat(),
            "article_count": previous_article_count,
        },
        "dated_article_count": len(dated_articles),
        "topic_count": compare_dimension("topics")["total"],
        "country_count": compare_dimension("countries")["total"],
        "topics": compare_dimension("topics")["items"],
        "countries": compare_dimension("countries")["items"],
        "timeline": [
            {"date": (timeline_start + timedelta(days=offset)).isoformat(),
             "article_count": daily_counts.get(
                 (timeline_start + timedelta(days=offset)).isoformat(), 0
             )}
            for offset in range((latest_date - timeline_start).days + 1)
        ],
    }



EVENT_TITLE_STOPWORDS = {
    "about", "after", "against", "amid", "among", "and", "are", "been",
    "before", "between", "from", "have", "into", "over", "says", "said",
    "that", "their", "there", "these", "this", "through", "under", "with",
    "will", "would", "what", "when", "where", "while", "whose", "could",
    "should", "report", "reports", "latest", "live", "update", "updates",
    "news", "more", "than", "they", "them", "then", "also", "after",
    "first", "next", "amid", "during", "such", "its", "his", "her",
}


def event_title_tokens(title):
    import re

    words = re.findall(r"[a-z0-9]{3,}", (title or "").casefold())
    return {
        word for word in words
        if word not in EVENT_TITLE_STOPWORDS and not word.isdigit()
    }


def build_event_development(members):
    """Summarise how reporting within one candidate event cluster changes over time."""
    if not members:
        return {
            "span_days": 0,
            "active_days": 0,
            "daily_timeline": [],
            "first_phase": {"article_count": 0},
            "later_phase": {"article_count": 0},
            "reporting_change": {
                "difference": 0,
                "percent": None,
                "status": "insufficient_data",
            },
            "newly_observed": {"countries": [], "topics": [], "sources": []},
        }

    start_date = min(item["date"] for item in members)
    end_date = max(item["date"] for item in members)
    span_days = (end_date - start_date).days + 1
    split_date = start_date + timedelta(days=max(0, (span_days - 1) // 2))

    first_phase = [
        item for item in members if item["date"] <= split_date
    ]
    later_phase = [
        item for item in members if item["date"] > split_date
    ]

    daily_counts = Counter(item["date"].isoformat() for item in members)
    daily_timeline = [
        {
            "date": (start_date + timedelta(days=offset)).isoformat(),
            "article_count": daily_counts.get(
                (start_date + timedelta(days=offset)).isoformat(), 0
            ),
        }
        for offset in range(span_days)
    ]

    first_count = len(first_phase)
    later_count = len(later_phase)
    difference = later_count - first_count
    if first_count == 0:
        change_percent = None
        status = "no_baseline"
    else:
        change_percent = round((difference / first_count) * 100, 1)
        status = (
            "more_reports" if difference > 0
            else "fewer_reports" if difference < 0
            else "same_reports"
        )

    def observed_values(phase, field):
        values = set()
        for item in phase:
            article = item["article"]
            if field == "sources":
                value = article.get("source")
                if value:
                    values.add(value)
            else:
                values.update(
                    value for value in parse_field(article.get(field))
                    if value and value.casefold() != "unknown"
                )
        return values

    newly_observed = {}
    for field in ("countries", "topics", "sources"):
        first_values = observed_values(first_phase, field)
        later_values = observed_values(later_phase, field)
        newly_observed[field] = sorted(
            later_values - first_values,
            key=str.casefold,
        )

    return {
        "span_days": span_days,
        "active_days": sum(1 for count in daily_counts.values() if count),
        "split_date": split_date.isoformat(),
        "first_phase": {
            "start": start_date.isoformat(),
            "end": split_date.isoformat(),
            "article_count": first_count,
        },
        "later_phase": {
            "start": (split_date + timedelta(days=1)).isoformat() if later_phase else None,
            "end": end_date.isoformat() if later_phase else None,
            "article_count": later_count,
        },
        "reporting_change": {
            "difference": difference,
            "percent": change_percent,
            "status": status,
        },
        "newly_observed": newly_observed,
        "daily_timeline": daily_timeline,
    }


def build_event_clusters(articles, window_days=30, min_articles=2):
    """Group likely reports of the same event using title, topic, country and date overlap."""
    dated = []
    for article in articles:
        published_date = get_published_date(article.get("published"))
        if published_date:
            dated.append((date.fromisoformat(published_date), article))

    if not dated:
        return {
            "available": False,
            "message": "No valid publication dates are available for event clustering.",
            "latest_data_date": None,
            "articles_analysed": 0,
            "cluster_count": 0,
            "clustered_article_count": 0,
            "unclustered_article_count": 0,
            "clusters": [],
        }

    latest_date = max(item[0] for item in dated)
    start_date = latest_date - timedelta(days=window_days - 1)
    selected = [
        article for published_date, article in dated
        if start_date <= published_date <= latest_date
    ]
    selected.sort(
        key=lambda article: get_published_timestamp(article.get("published")),
        reverse=True,
    )

    prepared = []
    for article in selected:
        prepared.append({
            "article": article,
            "date": date.fromisoformat(get_published_date(article.get("published"))),
            "tokens": event_title_tokens(article.get("title")),
            "countries": {
                value.casefold() for value in parse_field(article.get("countries"))
                if value.casefold() != "unknown"
            },
            "topics": {
                value.casefold() for value in parse_field(article.get("topics"))
            },
        })

    parent = list(range(len(prepared)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left, right):
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for left in range(len(prepared)):
        first = prepared[left]
        if len(first["tokens"]) < 2:
            continue

        for right in range(left + 1, len(prepared)):
            second = prepared[right]
            day_gap = abs((first["date"] - second["date"]).days)
            if day_gap > 10:
                continue

            shared_tokens = first["tokens"].intersection(second["tokens"])
            if len(shared_tokens) < 2:
                continue

            shared_context = bool(
                first["countries"].intersection(second["countries"])
                or first["topics"].intersection(second["topics"])
            )
            if not shared_context:
                continue

            title_similarity = len(shared_tokens) / max(
                1, min(len(first["tokens"]), len(second["tokens"]))
            )
            if title_similarity >= 0.34:
                union(left, right)

    components = {}
    for index in range(len(prepared)):
        components.setdefault(find(index), []).append(prepared[index])

    clusters = []
    clustered_ids = set()

    for members in components.values():
        if len(members) < min_articles:
            continue

        member_articles = [item["article"] for item in members]
        clustered_ids.update(article["id"] for article in member_articles)

        country_counts = Counter()
        topic_counts = Counter()
        source_counts = Counter()
        for article in member_articles:
            country_counts.update(set(
                value for value in parse_field(article.get("countries"))
                if value.casefold() != "unknown"
            ))
            topic_counts.update(set(parse_field(article.get("topics"))))
            if article.get("source"):
                source_counts[article["source"]] += 1

        dates = [item["date"] for item in members]
        clusters.append({
            "cluster_id": min(article["id"] for article in member_articles),
            "headline": member_articles[0].get("title") or "Untitled event",
            "article_count": len(member_articles),
            "first_seen": min(dates).isoformat(),
            "latest_seen": max(dates).isoformat(),
            "countries": [
                {"name": name, "article_count": count}
                for name, count in country_counts.most_common(8)
            ],
            "topics": [
                {"name": name, "article_count": count}
                for name, count in topic_counts.most_common(6)
            ],
            "sources": [
                {"name": name, "article_count": count}
                for name, count in source_counts.most_common()
            ],
            "development": build_event_development(members),
            "articles": member_articles,
        })

    clusters.sort(
        key=lambda item: (
            item["article_count"],
            item["latest_seen"],
        ),
        reverse=True,
    )

    return {
        "available": True,
        "window_days": window_days,
        "latest_data_date": latest_date.isoformat(),
        "window_start": start_date.isoformat(),
        "articles_analysed": len(selected),
        "cluster_count": len(clusters),
        "clustered_article_count": len(clustered_ids),
        "unclustered_article_count": len(selected) - len(clustered_ids),
        "clusters": clusters,
    }


@app.get("/api/events")
def get_event_clusters(
    days: int = Query(default=30, ge=7, le=90),
    min_articles: int = Query(default=2, ge=2, le=10),
):
    return build_event_clusters(
        get_all_articles(),
        window_days=days,
        min_articles=min_articles,
    )



def ensure_event_watchlist_table():
    connection = get_database_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tracked_events (
                cluster_id INTEGER PRIMARY KEY,
                headline TEXT NOT NULL,
                tracked_at TEXT NOT NULL
            )
        """)
        connection.commit()
    finally:
        connection.close()


@app.get("/api/events/watchlist")
def get_tracked_events():
    ensure_event_watchlist_table()
    connection = get_database_connection()
    try:
        rows = connection.execute(
            "SELECT cluster_id, headline, tracked_at FROM tracked_events ORDER BY tracked_at DESC"
        ).fetchall()
        tracked = [dict(row) for row in rows]
    finally:
        connection.close()

    current = build_event_clusters(get_all_articles(), window_days=90)
    current_clusters = current.get("clusters", [])
    results = []

    for item in tracked:
        # cluster_id is retained as a stable anchor article ID, not as a
        # temporary cluster ID. A cluster may merge or split as the window changes.
        cluster = next(
            (
                candidate for candidate in current_clusters
                if any(
                    article.get("id") == item["cluster_id"]
                    for article in candidate.get("articles", [])
                )
            ),
            None,
        )
        results.append({
            **item,
            "currently_detected": cluster is not None,
            "article_count": cluster["article_count"] if cluster else 0,
            "latest_seen": cluster["latest_seen"] if cluster else None,
            "headline": cluster["headline"] if cluster else item["headline"],
            "article_ids": [
                article.get("id") for article in cluster.get("articles", [])
            ] if cluster else [item["cluster_id"]],
        })

    return {"tracked_count": len(results), "events": results}


@app.post("/api/events/watchlist")
def track_event(article_id: int = Query(..., ge=1)):
    ensure_event_watchlist_table()
    analysis = build_event_clusters(get_all_articles(), window_days=90)
    cluster = next(
        (
            item for item in analysis.get("clusters", [])
            if any(
                article.get("id") == article_id
                for article in item.get("articles", [])
            )
        ),
        None,
    )
    if not cluster:
        raise HTTPException(
            status_code=404,
            detail="This article is not part of a detected event in the latest 90-day analysis.",
        )

    # Save the selected article's ID as a stable anchor. Do not save the
    # generated cluster ID, because that ID can change when clusters merge.
    connection = get_database_connection()
    try:
        connection.execute(
            """
            INSERT INTO tracked_events (cluster_id, headline, tracked_at)
            VALUES (?, ?, ?)
            ON CONFLICT(cluster_id) DO UPDATE SET
                headline = excluded.headline,
                tracked_at = excluded.tracked_at
            """,
            (article_id, cluster["headline"], datetime.now(timezone.utc).isoformat()),
        )
        connection.commit()
    finally:
        connection.close()

    return {
        "tracked": True,
        "article_id": article_id,
        "headline": cluster["headline"],
        "article_ids": [
            article.get("id") for article in cluster.get("articles", [])
        ],
    }


@app.delete("/api/events/watchlist")
def untrack_event(article_id: int = Query(..., ge=1)):
    ensure_event_watchlist_table()
    connection = get_database_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM tracked_events WHERE cluster_id = ?",
            (article_id,),
        )
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tracked event not found.")
    finally:
        connection.close()
    return {"tracked": False, "article_id": article_id}



# Source reliability and publisher coverage analysis
@app.get("/api/source-health")
def get_source_health(runs: int = Query(default=30, ge=1, le=365)):
    history_path = BASE_DIR / "data" / "raw" / "collection_history.jsonl"
    history = []
    if history_path.exists():
        with history_path.open("r", encoding="utf-8") as history_file:
            for line in history_file:
                try:
                    record = json.loads(line)
                    if isinstance(record, dict) and record.get("collected_at"):
                        history.append(record)
                except (json.JSONDecodeError, TypeError):
                    continue

    history.sort(key=lambda item: item.get("collected_at", ""))
    selected_runs = history[-runs:]
    articles = get_all_articles()
    source_history = {}

    for run in selected_runs:
        for item in run.get("sources", []):
            name = item.get("source")
            if not name:
                continue
            entry = source_history.setdefault(name, {
                "observations": 0, "successful_runs": 0, "failed_runs": 0,
                "articles_collected": 0, "attempts": 0,
                "latest_status": None, "latest_error": None,
                "latest_collected_at": None,
            })
            entry["observations"] += 1
            succeeded = item.get("status") in {"ok", "partial"}
            entry["successful_runs"] += int(succeeded)
            entry["failed_runs"] += int(not succeeded)
            entry["articles_collected"] += int(item.get("accepted_articles") or 0)
            entry["attempts"] += int(item.get("attempts") or 0)
            entry["latest_status"] = item.get("status", "failed")
            entry["latest_error"] = item.get("error")
            entry["latest_collected_at"] = run.get("collected_at")

    database_coverage = {}
    for article in articles:
        source = article.get("source")
        if not source:
            continue
        item = database_coverage.setdefault(source, {
            "database_articles": 0, "countries": Counter(), "topics": Counter()
        })
        item["database_articles"] += 1
        item["countries"].update({
            value for value in parse_field(article.get("countries"))
            if value.casefold() != "unknown"
        })
        item["topics"].update(parse_field(article.get("topics")))

    source_rows = []
    for name in set(source_history) | set(database_coverage):
        h = source_history.get(name, {})
        c = database_coverage.get(name, {})
        observations = h.get("observations", 0)
        successes = h.get("successful_runs", 0)
        source_rows.append({
            "source": name,
            "observations": observations,
            "successful_runs": successes,
            "failed_runs": h.get("failed_runs", 0),
            "success_rate": round(successes / observations * 100, 1) if observations else None,
            "articles_collected": h.get("articles_collected", 0),
            "attempts": h.get("attempts", 0),
            "latest_status": h.get("latest_status") or "not_recorded",
            "latest_error": h.get("latest_error"),
            "latest_collected_at": h.get("latest_collected_at"),
            "database_articles": c.get("database_articles", 0),
            "top_countries": [
                {"name": key, "article_count": count}
                for key, count in c.get("countries", Counter()).most_common(5)
            ],
            "top_topics": [
                {"name": key, "article_count": count}
                for key, count in c.get("topics", Counter()).most_common(5)
            ],
        })

    source_rows.sort(
        key=lambda item: (
            item["success_rate"] is not None,
            item["success_rate"] if item["success_rate"] is not None else -1,
            item["database_articles"],
        ),
        reverse=True,
    )
    observations = sum(item["observations"] for item in source_rows)
    successes = sum(item["successful_runs"] for item in source_rows)
    return {
        "available": bool(selected_runs),
        "message": None if selected_runs else (
            "No collection history has been recorded yet. Run the news collector to begin building reliability trends."
        ),
        "history_file_available": history_path.exists(),
        "runs_requested": runs,
        "runs_recorded": len(selected_runs),
        "latest_run": selected_runs[-1] if selected_runs else None,
        "configured_sources": selected_runs[-1].get("configured_sources", 0) if selected_runs else 0,
        "successful_sources_latest": selected_runs[-1].get("successful_sources", 0) if selected_runs else 0,
        "failed_sources_latest": selected_runs[-1].get("failed_or_empty_sources", 0) if selected_runs else 0,
        "recent_success_rate": round(successes / observations * 100, 1) if observations else None,
        "database_article_count": len(articles),
        "sources": source_rows,
    }


# API homepage
@app.get("/")
def home():
    return {
        "message": "STATECRAFT MONITOR API is operational",
        "version": "1.1.0",
    }


# Topic and country coverage trends
@app.get("/api/trends")
def get_coverage_trends(
    days: int = Query(default=7, ge=3, le=30),
):
    articles = get_all_articles()
    return build_coverage_trends(articles, window_days=days)


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


# Country-to-country shared news coverage
@app.get("/api/country-relations")
def get_country_relations(
    limit: int = Query(default=50, ge=1, le=200),
    min_articles: int = Query(default=1, ge=1),
):
    articles = get_all_articles()
    analysis = build_country_relationships(articles)
    filtered_pairs = [
        pair for pair in analysis["pairs"]
        if pair["article_count"] >= min_articles
    ]

    return {
        "country_count": analysis["country_count"],
        "countries_with_shared_coverage": analysis["countries_with_shared_coverage"],
        "articles_with_multiple_countries": analysis["articles_with_multiple_countries"],
        "total_pairs": len(filtered_pairs),
        "pairs": filtered_pairs[:limit],
    }


@app.get("/api/country-relations/pair")
def get_country_relation_details(
    country_a: str,
    country_b: str,
):
    if country_a.casefold() == country_b.casefold():
        raise HTTPException(
            status_code=400,
            detail="Choose two different countries.",
        )

    articles = get_all_articles()
    matching_articles = []

    for article in articles:
        article_countries = {
            country.casefold()
            for country in parse_field(article.get("countries"))
            if country.casefold() != "unknown"
        }

        if country_a.casefold() in article_countries and country_b.casefold() in article_countries:
            matching_articles.append(article)

    if not matching_articles:
        raise HTTPException(
            status_code=404,
            detail=f"No shared coverage found for {country_a} and {country_b}.",
        )

    topic_counts = Counter()
    source_counts = Counter()

    for article in matching_articles:
        topic_counts.update(set(parse_field(article.get("topics"))))
        source = article.get("source")
        if source:
            source_counts[source] += 1

    return {
        "country_a": country_a,
        "country_b": country_b,
        "article_count": len(matching_articles),
        "topic_count": len(topic_counts),
        "source_count": len(source_counts),
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


# Strategic coverage signals
@app.get("/api/strategic-signals")
def get_strategic_signals(days: int = Query(default=14, ge=7, le=30)):
    """Identify notable changes in media coverage, not real-world risk predictions."""
    articles = get_all_articles()
    dated_articles = []
    for article in articles:
        published_date = get_published_date(article.get("published"))
        if published_date:
            dated_articles.append((date.fromisoformat(published_date), article))

    if not dated_articles:
        return {
            "available": False,
            "message": "No valid publication dates are available for signal analysis.",
            "days": days,
            "latest_data_date": None,
            "articles_analysed": 0,
            "signals": [],
            "summary": {"total_signals": 0, "country_shifts": 0,
                        "topic_shifts": 0, "multi_source_events": 0},
        }

    latest_date = max(item[0] for item in dated_articles)
    recent_start = latest_date - timedelta(days=days - 1)
    previous_end = recent_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)

    recent = [
        article for published_date, article in dated_articles
        if recent_start <= published_date <= latest_date
    ]
    previous = [
        article for published_date, article in dated_articles
        if previous_start <= published_date <= previous_end
    ]

    def dimension_counts(items, field):
        counts = Counter()
        sources = {}
        examples = {}
        for article in items:
            values = {
                value for value in parse_field(article.get(field))
                if value and value.casefold() != "unknown"
            }
            for value in values:
                counts[value] += 1
                if article.get("source"):
                    sources.setdefault(value, set()).add(article["source"])
                examples.setdefault(value, [])
                if len(examples[value]) < 4:
                    examples[value].append({
                        "id": article.get("id"),
                        "title": article.get("title"),
                        "source": article.get("source"),
                        "published": article.get("published"),
                        "link": article.get("link"),
                    })
        return counts, sources, examples

    signals = []
    for field, signal_type, label in (
        ("countries", "country_shift", "Country coverage shift"),
        ("topics", "topic_shift", "Topic coverage shift"),
    ):
        recent_counts, recent_sources, recent_examples = dimension_counts(recent, field)
        previous_counts, _, _ = dimension_counts(previous, field)

        for name, recent_count in recent_counts.items():
            previous_count = previous_counts.get(name, 0)
            difference = recent_count - previous_count
            if recent_count < 2:
                continue

            if previous_count == 0:
                status = "new"
                change_percent = None
                qualifies = True
            else:
                change_percent = round((difference / previous_count) * 100, 1)
                status = "rising" if difference > 0 else (
                    "declining" if difference < 0 else "stable"
                )
                qualifies = difference >= 2 and change_percent >= 50

            if not qualifies:
                continue

            source_names = sorted(recent_sources.get(name, set()), key=str.casefold)
            signals.append({
                "id": f"{signal_type}:{name.casefold()}",
                "type": signal_type,
                "label": label,
                "name": name,
                "status": status,
                "recent_mentions": recent_count,
                "previous_mentions": previous_count,
                "change": difference,
                "change_percent": change_percent,
                "source_count": len(source_names),
                "sources": source_names[:8],
                "articles": recent_examples.get(name, []),
                "interpretation": (
                    f"Reporting about {name} appeared in {recent_count} articles "
                    f"across {len(source_names)} source(s), compared with "
                    f"{previous_count} in the preceding {days}-day period."
                ),
            })

    event_analysis = build_event_clusters(recent, window_days=90, min_articles=2)
    for cluster in event_analysis.get("clusters", []):
        if cluster.get("latest_seen", "") < recent_start.isoformat():
            continue
        source_names = sorted(
            {item.get("name") for item in cluster.get("sources", []) if item.get("name")},
            key=str.casefold,
        )
        if len(source_names) < 2:
            continue

        signals.append({
            "id": f"event:{cluster.get('cluster_id')}",
            "type": "multi_source_event",
            "label": "Multi-source event coverage",
            "name": cluster.get("headline") or "Unlabelled event",
            "status": "multiple_publishers",
            "recent_mentions": cluster.get("article_count", 0),
            "previous_mentions": None,
            "change": None,
            "change_percent": None,
            "source_count": len(source_names),
            "sources": source_names[:8],
            "countries": [item.get("name") for item in cluster.get("countries", [])[:6]],
            "topics": [item.get("name") for item in cluster.get("topics", [])[:6]],
            "articles": [
                {
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "source": article.get("source"),
                    "published": article.get("published"),
                    "link": article.get("link"),
                }
                for article in cluster.get("articles", [])[:5]
            ],
            "interpretation": (
                f"This event cluster contains {cluster.get('article_count', 0)} "
                f"related headlines from {len(source_names)} publishers. "
                "This is evidence of cross-publisher coverage, not independent "
                "verification of every claim in those reports."
            ),
        })

    type_order = {"multi_source_event": 0, "country_shift": 1, "topic_shift": 2}
    signals.sort(
        key=lambda item: (
            type_order.get(item["type"], 9),
            -item.get("source_count", 0),
            -item.get("recent_mentions", 0),
            item["name"].casefold(),
        ),
        reverse=False,
    )
    signals = signals[:30]

    return {
        "available": True,
        "days": days,
        "latest_data_date": latest_date.isoformat(),
        "recent_period": {
            "start": recent_start.isoformat(),
            "end": latest_date.isoformat(),
            "article_count": len(recent),
        },
        "previous_period": {
            "start": previous_start.isoformat(),
            "end": previous_end.isoformat(),
            "article_count": len(previous),
        },
        "articles_analysed": len(dated_articles),
        "signals": signals,
        "summary": {
            "total_signals": len(signals),
            "country_shifts": sum(item["type"] == "country_shift" for item in signals),
            "topic_shifts": sum(item["type"] == "topic_shift" for item in signals),
            "multi_source_events": sum(item["type"] == "multi_source_event" for item in signals),
        },
        "methodology": (
            "Signals are generated from changes in collected headline coverage. "
            "Country/topic shifts require at least two recent mentions and either "
            "no previous-period mentions or an increase of at least two mentions "
            "and 50 percent. Multi-source event signals require at least two "
            "publishers in a candidate headline cluster. These are monitoring "
            "indicators, not forecasts, severity ratings, or fact-check verdicts."
        ),
    }


# Evidence-led country strategic assessment brief
@app.get("/api/briefs/country/{country}")
def get_country_strategic_brief(
    country: str,
    days: int = Query(default=30, ge=7, le=90),
):
    """Compile a traceable country brief from collected news metadata and headlines."""
    all_articles = get_all_articles()
    matched = [
        article for article in all_articles
        if any(
            value.casefold() == country.casefold()
            for value in parse_field(article.get("countries"))
        )
    ]

    if not matched:
        raise HTTPException(
            status_code=404,
            detail=f"No articles currently match {country}.",
        )

    dated = []
    undated_count = 0
    for article in matched:
        published = get_published_date(article.get("published"))
        if published:
            dated.append((date.fromisoformat(published), article))
        else:
            undated_count += 1

    if not dated:
        raise HTTPException(
            status_code=422,
            detail=f"Articles for {country} do not contain usable publication dates.",
        )

    latest_date = max(item[0] for item in dated)
    recent_start = latest_date - timedelta(days=days - 1)
    previous_end = recent_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)

    recent = [
        article for published, article in dated
        if recent_start <= published <= latest_date
    ]
    previous = [
        article for published, article in dated
        if previous_start <= published <= previous_end
    ]

    def count_dimension(items, field):
        counts = Counter()
        for article in items:
            values = {
                value for value in parse_field(article.get(field))
                if value and value.casefold() != "unknown"
            }
            counts.update(values)
        return counts

    recent_topics = count_dimension(recent, "topics")
    previous_topics = count_dimension(previous, "topics")
    recent_sources = Counter(
        article.get("source") for article in recent if article.get("source")
    )
    previous_sources = Counter(
        article.get("source") for article in previous if article.get("source")
    )

    topic_comparison = []
    for topic in set(recent_topics) | set(previous_topics):
        current = recent_topics.get(topic, 0)
        earlier = previous_topics.get(topic, 0)
        topic_comparison.append({
            "topic": topic,
            "recent_articles": current,
            "previous_articles": earlier,
            "change": current - earlier,
            "status": (
                "new" if earlier == 0 and current > 0
                else "rising" if current > earlier
                else "declining" if current < earlier
                else "stable"
            ),
        })
    topic_comparison.sort(
        key=lambda item: (item["recent_articles"], item["change"], item["topic"].casefold()),
        reverse=True,
    )

    recent_count = len(recent)
    previous_count = len(previous)
    if previous_count == 0:
        coverage_change = None
        coverage_status = "no_comparison_baseline"
    else:
        coverage_change = round(
            ((recent_count - previous_count) / previous_count) * 100, 1
        )
        coverage_status = (
            "increased" if recent_count > previous_count
            else "decreased" if recent_count < previous_count
            else "unchanged"
        )

    source_count = len(recent_sources)
    if recent_count < 5 or source_count < 2:
        evidence_depth = "Limited"
        evidence_note = "The selected period contains few articles or a narrow publisher mix. Treat this brief as an initial coverage snapshot."
    elif recent_count < 15 or source_count < 3:
        evidence_depth = "Developing"
        evidence_note = "The selected period provides some cross-publisher coverage, but the evidence base remains modest."
    else:
        evidence_depth = "Broader"
        evidence_note = "The selected period has a broader article and publisher base. This describes coverage depth, not factual accuracy."

    event_result = build_event_clusters(recent, window_days=90, min_articles=2)
    country_events = []
    for cluster in event_result.get("clusters", []):
        event_sources = [
            item.get("name") for item in cluster.get("sources", [])
            if item.get("name")
        ]
        if len(event_sources) >= 2:
            country_events.append({
                "headline": cluster.get("headline"),
                "article_count": cluster.get("article_count", 0),
                "source_count": len(event_sources),
                "sources": event_sources,
                "first_seen": cluster.get("first_seen"),
                "latest_seen": cluster.get("latest_seen"),
                "topics": [item.get("name") for item in cluster.get("topics", [])],
                "articles": [
                    {
                        "id": article.get("id"),
                        "title": article.get("title"),
                        "source": article.get("source"),
                        "published": article.get("published"),
                        "link": article.get("link"),
                    }
                    for article in cluster.get("articles", [])[:5]
                ],
            })

    country_events.sort(
        key=lambda item: (item["article_count"], item["latest_seen"] or ""),
        reverse=True,
    )

    timeline_counts = Counter(
        published.isoformat() for published, _ in dated
        if recent_start <= published <= latest_date
    )
    timeline = [
        {
            "date": (recent_start + timedelta(days=offset)).isoformat(),
            "article_count": timeline_counts.get(
                (recent_start + timedelta(days=offset)).isoformat(), 0
            ),
        }
        for offset in range(days)
    ]

    recent_articles = [
        {
            "id": article.get("id"),
            "title": article.get("title"),
            "source": article.get("source"),
            "published": article.get("published"),
            "link": article.get("link"),
            "topics": parse_field(article.get("topics")),
        }
        for article in recent
    ]
    recent_articles.sort(
        key=lambda item: get_published_timestamp(item.get("published")),
        reverse=True,
    )

    canonical_country = next(
        (
            value.strip()
            for article in matched
            for value in parse_field(article.get("countries"))
            if value.casefold() == country.casefold()
        ),
        country,
    )

    return {
        "available": True,
        "brief_type": "Country Strategic Assessment",
        "country": canonical_country,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_days": days,
        "data_through": latest_date.isoformat(),
        "period": {
            "start": recent_start.isoformat(),
            "end": latest_date.isoformat(),
            "article_count": recent_count,
        },
        "comparison_period": {
            "start": previous_start.isoformat(),
            "end": previous_end.isoformat(),
            "article_count": previous_count,
        },
        "coverage_overview": {
            "recent_articles": recent_count,
            "previous_articles": previous_count,
            "change_percent": coverage_change,
            "change_status": coverage_status,
            "all_time_country_articles": len(matched),
            "recent_source_count": source_count,
            "previous_source_count": len(previous_sources),
            "evidence_depth": evidence_depth,
            "evidence_note": evidence_note,
        },
        "topic_analysis": [
            {
                **item,
                "recent_share_percent": round(
                    (item["recent_articles"] / recent_count) * 100, 1
                ) if recent_count else 0,
            }
            for item in topic_comparison[:10]
        ],
        "source_distribution": [
            {"source": source, "article_count": count}
            for source, count in recent_sources.most_common()
        ],
        "multi_publisher_event_coverage": country_events[:8],
        "coverage_timeline": timeline,
        "key_headlines": recent_articles[:20],
        "data_quality": {
            "dated_country_articles": len(dated),
            "undated_country_articles": undated_count,
            "period_article_count": recent_count,
            "period_source_count": source_count,
            "limitations": [
                "This brief analyses the STATECRAFT MONITOR collection, not all reporting published worldwide.",
                "Country and topic labels are produced by the project's current rule-based recognition and classification pipeline.",
                "Headline-level analysis cannot establish the full context or factual accuracy of an article.",
                "Multiple publishers covering an event does not by itself constitute independent verification.",
                "Coverage volume is not a measure of national stability, threat level, policy effectiveness or event severity.",
            ],
        },
    }


# Optional Gemini AI synthesis. The deterministic country assessment remains
# available even when no API key is configured or the free quota is exhausted.
def load_local_environment():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and value and name not in os.environ:
            os.environ[name] = value


load_local_environment()


def build_ai_assessment_cache_key(brief):
    evidence_fingerprint = {
        "country": brief.get("country"),
        "period_days": brief.get("period_days"),
        "data_through": brief.get("data_through"),
        "coverage_overview": brief.get("coverage_overview"),
        "topic_analysis": brief.get("topic_analysis"),
        "source_distribution": brief.get("source_distribution"),
        "multi_publisher_event_coverage": brief.get("multi_publisher_event_coverage"),
        "key_headlines": brief.get("key_headlines"),
    }
    encoded = json.dumps(
        evidence_fingerprint, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_cached_ai_assessment(cache_key):
    connection = get_database_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ai_brief_cache (
                cache_key TEXT PRIMARY KEY,
                assessment_json TEXT NOT NULL,
                generated_at TEXT NOT NULL
            )
        """)
        connection.commit()
        row = connection.execute(
            "SELECT assessment_json, generated_at FROM ai_brief_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if not row:
            return None
        return {
            "assessment": json.loads(row["assessment_json"]),
            "generated_at": row["generated_at"],
            "cached": True,
        }
    finally:
        connection.close()


def save_ai_assessment_cache(cache_key, assessment, generated_at):
    connection = get_database_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ai_brief_cache (
                cache_key TEXT PRIMARY KEY,
                assessment_json TEXT NOT NULL,
                generated_at TEXT NOT NULL
            )
        """)
        connection.execute(
            """
            INSERT OR REPLACE INTO ai_brief_cache
            (cache_key, assessment_json, generated_at)
            VALUES (?, ?, ?)
            """,
            (
                cache_key,
                json.dumps(assessment, ensure_ascii=False),
                generated_at,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def build_ai_assessment_prompt(brief):
    evidence = {
        "country": brief.get("country"),
        "analysis_period": brief.get("period"),
        "comparison_period": brief.get("comparison_period"),
        "coverage_overview": brief.get("coverage_overview"),
        "topic_analysis": brief.get("topic_analysis", []),
        "publisher_distribution": brief.get("source_distribution", []),
        "multi_publisher_event_coverage": brief.get("multi_publisher_event_coverage", []),
        "key_headlines": [
            {
                "article_id": item.get("id"),
                "headline": item.get("title"),
                "publisher": item.get("source"),
                "published": item.get("published"),
                "topics": item.get("topics", []),
            }
            for item in brief.get("key_headlines", [])
        ],
        "known_limitations": brief.get("data_quality", {}).get("limitations", []),
    }
    return (
        "You are the analytical writing component of STATECRAFT MONITOR, an "
        "evidence-led geopolitical news monitoring platform. Prepare a cautious "
        "country strategic assessment using ONLY the supplied evidence package. "
        "Do not use outside knowledge, invent facts, infer motives, or turn media "
        "attention into a claim about real-world severity. Distinguish reported "
        "developments from your interpretation. Treat publisher names as source "
        "labels, not proof of independent verification. If evidence is thin, say so. "
        "Every concrete development should include supporting article IDs in the "
        "form [Article ID: 123]. Do not cite an ID that is not in the evidence. "
        "Potential implications must be explicitly framed as conditional analytical "
        "possibilities, not predictions. Identify uncertainty and information gaps. "
        "Return ONLY valid JSON with exactly these keys, each value an array of "
        "2-4 concise strings: executive_overview, major_developments, "
        "analytical_observations, potential_implications, uncertainties_information_gaps. "
        "No markdown fences and no extra keys.\n\nEVIDENCE PACKAGE:\n"
        + json.dumps(evidence, ensure_ascii=False)
    )


def generate_gemini_assessment(brief):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini is not configured yet. Add GEMINI_API_KEY to the local .env file.",
        )

    cache_key = build_ai_assessment_cache_key(brief)
    cached = get_cached_ai_assessment(cache_key)
    if cached:
        return {
            "available": True,
            "provider": "Google Gemini",
            "model": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            **cached,
        }

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + model
        + ":generateContent"
    )
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": build_ai_assessment_prompt(brief)}],
        }],
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 1800,
            "responseMimeType": "application/json",
        },
    }

    try:
        response = requests.post(
            endpoint,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=(10, 60),
        )
    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Could not reach Gemini. Check your internet connection and try again.",
        )

    if response.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail="Gemini's free-tier request limit has been reached. Try again later; your evidence-based report is still available.",
        )
    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=502,
            detail="Gemini rejected the API key or project access. Check the key in Google AI Studio.",
        )
    if not response.ok:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini returned an API error (HTTP {response.status_code}). Check the configured model and API access.",
        )

    try:
        response_data = response.json()
        generated_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        assessment = json.loads(generated_text)
        required_sections = (
            "executive_overview",
            "major_developments",
            "analytical_observations",
            "potential_implications",
            "uncertainties_information_gaps",
        )
        if not isinstance(assessment, dict) or any(
            not isinstance(assessment.get(section), list)
            or not assessment[section]
            for section in required_sections
        ):
            raise ValueError("Gemini response did not match the required assessment structure.")
        assessment = {
            section: [str(item) for item in assessment[section][:4]]
            for section in required_sections
        }
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(
            status_code=502,
            detail="Gemini responded, but its assessment could not be validated. Please try again.",
        )

    generated_at = datetime.now(timezone.utc).isoformat()
    save_ai_assessment_cache(cache_key, assessment, generated_at)
    return {
        "available": True,
        "provider": "Google Gemini",
        "model": model,
        "assessment": assessment,
        "generated_at": generated_at,
        "cached": False,
    }


@app.get("/api/briefs/country/{country}/ai")
def get_ai_country_strategic_assessment(
    country: str,
    days: int = Query(default=30, ge=7, le=90),
):
    """Generate a cached AI interpretation from the existing evidence-led brief."""
    brief = get_country_strategic_brief(country, days)
    return generate_gemini_assessment(brief)
