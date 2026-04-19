import re
from collections import Counter


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "will", "have",
    "has", "was", "were", "not", "you", "your", "our", "their", "they", "them",
    "course", "students", "student", "class", "semester", "credit", "hours",
    "required", "materials", "textbook", "reading", "list", "section", "policy",
    "policies", "week", "weeks", "college", "university", "online", "campus",
    "date", "meeting", "meetings", "lab", "start", "end", "day", "times",
    "time", "location", "room", "building", "modality", "wlab",
    "mcgraw", "hill", "simnet", "connectmaster", "bundle", "pearson", "cengage",
    "wiley", "publisher",
}


def clean_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]*>", "", text)


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-/]{2,}", text)
    return [token.lower() for token in tokens]


def _section(text: str, label: str) -> str:
    pattern = rf"{label}\s*:(.*?)(\n\s*\n|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_keywords_from_syllabus(text: str, course_query: str | None = None, max_keywords: int = 12) -> list[str]:
    cleaned = clean_html(text)
    sections = [
        _section(cleaned, "Course Title"),
        _section(cleaned, "Course Description"),
        _section(cleaned, "Learning Outcomes"),
        _section(cleaned, "Required Materials"),
        _section(cleaned, "Textbook"),
    ]
    base_text = " ".join(section for section in sections if section)
    if not base_text:
        base_text = cleaned[:2000]

    tokens = [t for t in _tokenize(base_text) if t not in STOPWORDS]
    counts = Counter(tokens)

    prioritized = []
    if course_query:
        query_tokens = _tokenize(course_query)
        for token in query_tokens:
            if token not in STOPWORDS and token not in prioritized:
                prioritized.append(token)

        subject_match = re.search(r"([A-Za-z]{3,4})\s*(\d{3,4}[A-Za-z]?)", course_query, re.IGNORECASE)
        if subject_match:
            subject = subject_match.group(1).lower()
            if subject not in prioritized:
                prioritized.append(subject)
            num = subject_match.group(2).lower()
            if num not in prioritized:
                prioritized.append(num)

    keywords = prioritized[:]
    for word, _ in counts.most_common():
        if word not in keywords and word not in STOPWORDS:
            keywords.append(word)
        if len(keywords) >= max_keywords:
            break

    return keywords[:max_keywords]


def build_rag_query_text(
    text: str,
    keywords: list[str],
    course_query: str | None = None,
    max_chars: int = 2500,
) -> str:
    """Short, course-focused text for embedding. Full syllabi dilute similarity to OER snippets."""
    cleaned = clean_html(text)
    parts: list[str] = []
    if course_query:
        parts.append(f"Course: {course_query.strip()}")
    if keywords:
        parts.append("Topics: " + ", ".join(keywords[:20]))
    for label in ("Course Description", "Learning Outcomes", "Required Materials"):
        sec = _section(cleaned, label)
        if sec:
            parts.append(sec[:1500])
    body = "\n\n".join(parts)
    if len(body.strip()) < 80:
        body = cleaned[:max_chars]
    return body[:max_chars]
