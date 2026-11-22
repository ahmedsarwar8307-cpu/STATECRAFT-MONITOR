import json
from pathlib import Path
import sqlite3
from collections import Counter
from datetime import date, datetime, timezone, timedelta
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
