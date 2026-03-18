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
pip install playwright
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

## Future Development

Planned features include:

* scraping Open Educational Resource repositories
* connecting syllabus topics to relevant OER materials
* building a **FastAPI backend**
* connecting a **local AI model (LM Studio)** for recommendations
* building a web interface for course search

---

## Authors

Karen Armendariz
Farhana Rahman
Scott Barre
Georgia Gwinnett College
ITEC 4700 – Artificial Intelligence
