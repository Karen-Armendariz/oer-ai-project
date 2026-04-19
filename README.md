# OER AI Project

## Overview

This project automates the retrieval of course syllabus information from the Georgia Gwinnett College **Simple Syllabus Library**.

The goal is to support an **AI assistant that can recommend Open Educational Resources (OER)** based on course syllabus content.

Instead of manually searching syllabi, the system allows a user to enter a course (for example **BIOL 1101K**) and automatically retrieve the syllabus text. That text can then be used by an AI model to generate relevant educational resource recommendations.

---

## Features

* Automated login session using Playwright
* Automated navigation of the GGC Simple Syllabus library
* Search for a syllabus by **course prefix and number**
* Scrape the full syllabus text
* Save syllabus content locally for AI processing
* RAG pipeline with ChromaDB + sentence-transformers
* Open ALG ingestion and strict relevance scoring
* FastAPI service for production integrations

Example search:

```
BIOL 1101K
```

---

## Project Structure

```
oer-ai-project
│
├── backend
│   ├── ingest_data.py        # script used to test syllabus scraping
│   ├── search_syllabus.py    # search a syllabus by course code
│   ├── api.py                # FastAPI service
│   ├── oer_service.py        # production RAG orchestration
│   ├── data
│   │   └── syllabi           # scraped syllabus text files
│   └── playwright_user_data  # browser session storage (ignored by git)
│
└── .gitignore
```

---

## Requirements

Python 3.10+

Install dependencies:

```
pip install -r backend/requirements.txt
playwright install
```

---

## How to Run

Navigate to the backend folder:

```
cd backend
```

Run the syllabus search script:

```
python search_syllabus.py
```

Enter a course when prompted:

```
Enter course (example: BIOL 1101K):
```

The script will:

1. Open the Simple Syllabus library
2. Navigate to the School of Science and Technology
3. Locate the matching course syllabus
4. Extract the full syllabus text
5. Save it to the `data/syllabi` folder

---

## Run the RAG Agent

From the project root:

```
./run_agent.sh
```

---

## Run the API (Production)

From the project root:

```
./run_api.sh
```

Example request:

```
curl -X POST http://localhost:8000/oer/search \
  -H "Content-Type: application/json" \
  -d '{"course_query":"BIOL 1101K"}'
```

---

## Docker

```
docker build -t oer-rag .
docker run -p 8000:8000 -v oer-chroma:/app/data/chroma_db oer-rag
```

Or with Compose (persists ChromaDB):

```
docker compose up --build
```

---

## Automated tests

`pytest` is installed **inside** `.venv`, so it is not on your global `PATH`. From the project root:

```
./run_tests.sh
```

Or call it explicitly:

```
./.venv/bin/pytest tests/ -v
```

---

## Configuration

Environment variables:

* `OPENAI_API_KEY` (optional)
* `OPENALG_API_KEY` (optional for full metadata)
* `HF_TOKEN` (optional for faster model downloads)
* `OER_DISTANCE_THRESHOLD` (default `1.15`)
* `OER_KEYWORD_MIN_OVERLAP` (default `1`)
* `OER_MAX_RESULTS` (default `5`)
* `OER_RETRIEVAL_TOP_K` (default `20`)
* `OER_LOG_LEVEL` (default `INFO`)
* `CORS_ORIGINS` (optional; comma-separated origins for browser clients, e.g. `http://localhost:3000`)

Copy `.env.example` to `.env` to configure local production settings.

---

## Example Output

```
Opening Simple Syllabus library...
Locating course: BIOL 1101K
Navigating to syllabus document...
Saved to:
backend/data/syllabi/sample_syllabus.txt
Character count: 29813
```

---

## Production Notes

* The RAG pipeline uses keyword overlap + distance thresholds with a relaxed fallback so courses still get ranked results.
* Use `OER_DISTANCE_THRESHOLD` and `OER_KEYWORD_MIN_OVERLAP` to tune strictness.
* API: `GET /health` returns `status`, `chroma_ready`, and `version`. Interactive docs: `/docs`.
* If Open ALG ingest fails, `POST /oer/search` still returns `ingest_error` and uses the existing Chroma index when possible.
* GitHub Actions runs `pytest` on push/PR to `main`, `master`, `develop`, or `dev`.

---

## Authors

Karen Armendariz
Farhana Rahman
Scott Barre
Georgia Gwinnett College
ITEC 4700 – Artificial Intelligence
