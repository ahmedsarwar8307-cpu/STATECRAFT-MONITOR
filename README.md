# STATECRAFT MONITOR

### Global Affairs · Intelligence · Research

STATECRAFT MONITOR is an independent geopolitical news monitoring and intelligence platform designed to collect, process, classify, and organize international news into structured country and topic-based information.

The project combines a Python data-processing pipeline with a FastAPI backend, SQLite database, and React dashboard.

**Status:** Active development

---

## Project Objectives

- Collect international news from RSS feeds.
- Clean and organize collected news data.
- Identify countries and geopolitical entities mentioned in headlines.
- Classify news into geopolitical and general-interest topics.
- Store structured news records in a relational database.
- Explore news coverage through a web-based dashboard.

## Current Features

### 1. Automated News Collection
- Collects news metadata from international RSS feeds.
- Extracts headlines, publication dates, source names, and article links.
- Removes duplicate article links.

### 2. Country Recognition
- Python-based, rule-driven country recognition.
- Uses country names and aliases to identify geographic references in headlines.
- Supports a broad country and alias dictionary.

### 3. Topic Classification
- Rule-based geopolitical and general-interest topic classification.
- Includes 15 topic categories:
  Politics, Diplomacy, Military, Security, Economics, Trade, Conflict, Technology, Energy, Environment, Society, Health, Culture, Transport, and Sports.

### 4. Database Integration
- SQLite database for structured article storage.
- Stores article sources, headlines, publication dates, links, countries, and topics.
- Uses article links to prevent duplicate records and update existing records.

### 5. Backend API
- FastAPI backend.
- Provides article and country-related API endpoints.
- Connects the dashboard to the SQLite database.

### 6. Web Dashboard
- React-based interface.
- World News and Regions & Countries pages.
- Country coverage, topic distributions, and article exploration.

---

## Technology Stack

| Component | Technologies |
|---|---|
| Programming | Python |
| Data Processing | Pandas |
| RSS Collection | Feedparser, Requests |
| Recognition & Classification | Python rule-based systems |
| Backend | FastAPI, Uvicorn |
| Database | SQLite |
| Frontend | React, Vite |
| Routing | React Router |
| Icons | Lucide React |
| Version Control | Git, GitHub |

---

## Project Structure

```text
STATECRAFT-MONITOR/
├── backend/
│   └── main.py
├── dashboard/
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
│       └── ...
├── data/
│   ├── raw/
│   └── processed/
├── database/
│   ├── geointel.db
│   └── geointel_backup_before_sync.db
├── src/
│   ├── news_collector.py
│   ├── data_processor.py
│   ├── country_recognizer.py
│   ├── topic_classifier.py
│   ├── database_manager.py
│   ├── database_queries.py
│   ├── country_analysis.py
│   ├── topic_analysis.py
│   ├── country_topic_analysis.py
│   └── inspect_database.py
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Installation and Setup

### Prerequisites

- Python 3
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd GeoIntel-AI
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the repository's actual URL.

### 2. Set up the Python environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Start the FastAPI backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

Backend:

`http://127.0.0.1:8000`

API documentation:

`http://127.0.0.1:8000/docs`

### 4. Start the React dashboard

Open a second terminal:

```bash
cd dashboard
npm install
npm run dev
```

Open:

`http://localhost:5173`

Keep both the backend and frontend running while using the dashboard.

---

## Data Pipeline

The Python processing scripts can be executed from the project root in this order:

1. `src/news_collector.py` — collect RSS news.
2. `src/data_processor.py` — clean and validate records.
3. `src/country_recognizer.py` — identify countries.
4. `src/topic_classifier.py` — classify topics.
5. `src/database_manager.py` — synchronize processed records with SQLite.

The repository also includes an existing database and processed dataset snapshot.

---

## Development Roadmap

Planned areas of development include:

- Improved country and regional intelligence.
- Geographic organization of country coverage.
- Historical news coverage analysis.
- More advanced entity recognition and classification.
- Deeper analytical tools and visualizations.
- Expanded research and briefing capabilities.

---

## Project Philosophy

STATECRAFT MONITOR aims to develop from a structured international news monitoring system into a broader geopolitical research and intelligence platform.

The project is being developed incrementally, with an emphasis on transparent data processing, structured information, and analytical usefulness.

---

**STATECRAFT MONITOR**  
Global Affairs · Intelligence · Research
