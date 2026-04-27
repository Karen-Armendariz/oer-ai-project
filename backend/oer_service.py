from __future__ import annotations

import logging
from pathlib import Path
from turtle import distance

from backend.config import Settings
from backend.keywording import extract_keywords_from_syllabus, clean_html, build_rag_query_text
from backend.oer_client import OpenALGClient
from backend.rag_store import OERRAGStore


SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
SYLLABI_DIR = PROJECT_ROOT / "data" / "syllabi"
logger = logging.getLogger(__name__)


class OERService:
    def __init__(self, settings: Settings | None = None, store: OERRAGStore | None = None):
        self.settings = settings or Settings()
        self.store = store or OERRAGStore(persist_directory=self.settings.chroma_dir)
        api_key = getattr(self.settings, "openalg_api_key", None)
        self.client = OpenALGClient(api_key=api_key)

    def resolve_syllabus(self, course_query: str) -> tuple[str | None, Path | None]:
        for syllabus in SYLLABI_DIR.rglob("*.txt"):
            if course_query.upper() in syllabus.name.upper():
                return syllabus.read_text(encoding="utf-8"), syllabus
        return None, None

    def ingest_open_alg(self, keywords: list[str]) -> int:
        results = self.client.fetch_all_relevant_oer(keywords)
        if not results:
            return 0
        for res in results:
            res["license"] = clean_html(res["license"]).strip()
            res["description"] = clean_html(res["description"]).strip()
        self.store.add_resources(results)
        return len(results)

    def search(
        self,
        course_query: str | None = None,
        syllabus_text: str | None = None,
        progress_cb=None,
    ) -> dict:
        if not course_query and not syllabus_text:
            raise ValueError("course_query or syllabus_text is required.")

        resolved_text = syllabus_text
        source_file = None
        if course_query and not resolved_text:
            resolved_text, source_file = self.resolve_syllabus(course_query)
        if not resolved_text:
            resolved_text = course_query or ""

        keywords = extract_keywords_from_syllabus(resolved_text, course_query=course_query)
        course_expansions = {
             "ENGL 1101": "English Composition I writing rhetoric essays research composition",
             "ENGL 1102": "English Composition II writing literature research argument essays",
             "HIST 2111": "United States History I American history to 1877 colonial America revolution colonial period civil war",
             "HIST 2112": "United States History II American history since 1877 reconstruction modern America",
        }

        if course_query:
            normalized_course = course_query.upper().strip()    
            if normalized_course in course_expansions:
               keywords.extend(course_expansions[normalized_course].split())
        logger.info("Keywords extracted: %s", keywords)
        if progress_cb:
            progress_cb("keywords", {"keywords": keywords})

        ingested = 0
        ingest_error: str | None = None
        try:
            if progress_cb:
                progress_cb("ingest_start", {"keywords": keywords})
            ingested = self.ingest_open_alg(keywords)
            logger.info("Ingested %s resources from Open ALG", ingested)
            if progress_cb:
                progress_cb("ingest_done", {"ingested": ingested})
        except Exception as exc:
            logger.exception("Open ALG ingest failed; continuing with indexed data only")
            ingest_error = "Open ALG ingest failed; results may be limited to previously indexed resources."
            if progress_cb:
                progress_cb("ingest_error", {"message": ingest_error})

        query_text = build_rag_query_text(resolved_text, keywords, course_query=course_query)
        
        if course_query:
            normalized_course = course_query.upper().strip()
            if normalized_course in course_expansions:
                query_text = f"{course_query} {course_expansions[normalized_course]} {query_text}"
        
        
        k = max(self.settings.retrieval_top_k, self.settings.max_results)
        if progress_cb:
            progress_cb("query", {"top_k": k})
        results = self.store.query_oer(query_text, n_results=k)
        if progress_cb:
            progress_cb("rank", {})
        ranked = self._rank_results(results, keywords, course_query=course_query)

        return {
            "query": course_query,
            "syllabus_source": str(source_file) if source_file else None,
            "keywords": keywords,
            "results": ranked,
            "ingest_error": ingest_error,
        }

    def _rank_results(self, results: dict, keywords: list[str], course_query: str | None = None) -> list[dict]:
        if not results or not results.get("documents"):
            return []

        docs = results["documents"][0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        keyword_set = {kw.lower() for kw in keywords if len(kw) >= 2}

        def score_row(doc: str, meta: dict, distance: float, relaxed: bool) -> dict | None:
            if distance is None:
                return None
            doc_lower = doc.lower()
            overlap = sum(1 for kw in keyword_set if kw in doc_lower)
            course_match = bool(course_query and course_query.lower() in doc_lower)
            if not relaxed:
                if not course_match and (
                     distance > self.settings.distance_threshold
                      or overlap < self.settings.keyword_min_overlap
        ) :
                    return None
            else:
                 if not course_match and distance > 1.35:
                      return None
            similarity = max(0.0, 1.0 - min(distance, 2.0) / 2.0)
            overlap_score = min(overlap / max(len(keyword_set), 1), 1.0)
            score = round((0.7 * similarity + 0.3 * overlap_score) * 100, 2)
            return {
                "title": meta.get("title"),
                "license": meta.get("license"),
                "creators": meta.get("creators"),
                "links": meta.get("links"),
                "distance": round(distance, 4),
                "keyword_overlap": overlap,
                "score": score,
            }

        ranked = []
        for doc, meta, distance in zip(docs, metas, distances):
            row = score_row(doc, meta, distance, relaxed=False)
            if row:
                ranked.append(row)

        if not ranked:
            for doc, meta, distance in zip(docs, metas, distances):
                row = score_row(doc, meta, distance, relaxed=True)
                if row:
                    ranked.append(row)

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[: self.settings.max_results]
