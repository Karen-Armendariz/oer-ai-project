import json
import logging
import queue
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, model_validator
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pathlib import Path

from pydantic import model_validator

from backend.config import Settings
from backend.logging_setup import configure_logging
from backend.oer_service import OERService
from backend.schemas import HealthResponse, SearchRequest, SearchResponse
from backend.search_syllabus import scrape_syllabus

logger = logging.getLogger(__name__)
settings = Settings()
_service: OERService | None = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_STATIC = Path(__file__).resolve().parent / "static"
_ROOT_STATIC = PROJECT_ROOT / "static"


def _ui_index_path() -> Path | None:
    """Prefer UI next to api.py (always deployed with backend); fallback to repo root/static."""
    for candidate in (_BACKEND_STATIC / "index.html", _ROOT_STATIC / "index.html"):
        if candidate.is_file():
            return candidate
    return None


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings.log_level)
    yield


def get_service() -> OERService:
    global _service
    if _service is None:
        _service = OERService(settings=settings)
    return _service


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)


def _setup_cors(application: FastAPI) -> None:
    raw = (settings.cors_origins or "").strip()
    if not raw:
        return
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins:
        return
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


_setup_cors(app)
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")


class CourseRequest(BaseModel):
    course: str


class SearchBody(SearchRequest):
    @model_validator(mode="after")
    def require_payload(self):
        cq = (self.course_query or "").strip()
        st = (self.syllabus_text or "").strip()
        if not cq and not st:
            raise ValueError("course_query or syllabus_text is required")
        if cq and len(cq) < 3:
            raise ValueError("course_query must be at least 3 characters when provided")
        if st and len(st) < 20:
            raise ValueError("syllabus_text must be at least 20 characters when provided")
        return self


@app.get("/", include_in_schema=False)
def root():
    return JSONResponse(
        {
            "message": "OER AI backend is running",
            "ui": "/ui",
            "docs": "/docs",
            "health": "/health",
        }
    )


@app.get("/ui", include_in_schema=False)
def oer_agent_ui():
    """Browser UI for course search (same pipeline as run_agent.sh)."""
    index = _ui_index_path()
    if index is None:
        raise HTTPException(
            status_code=404,
            detail="UI not found (missing backend/static/index.html)",
        )
    return FileResponse(index, media_type="text/html")


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    logger.exception("Unhandled error: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
def root():
    return {"message": "OER AI backend is running"}


@app.post("/search-syllabus")
def search_syllabus_endpoint(request: CourseRequest):
    try:
        result = scrape_syllabus(request.course)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    chroma_path = settings.chroma_dir
    try:
        chroma_ready = Path(chroma_path).exists()
    except OSError:
        chroma_ready = False
    return HealthResponse(
        status="ok",
        chroma_ready=chroma_ready,
        version=settings.api_version,
    )


@app.post("/oer/search", response_model=SearchResponse)
def search_oer(
    payload: SearchBody,
    svc: OERService = Depends(get_service),
) -> SearchResponse:
    data = svc.search(
        course_query=payload.course_query.strip() if payload.course_query else None,
        syllabus_text=payload.syllabus_text.strip() if payload.syllabus_text else None,
    )
    return SearchResponse.model_validate(data)


@app.get("/oer/search/stream")
def search_oer_stream(
    course_query: str,
    svc: OERService = Depends(get_service),
):
    """Server-sent events stream for live UI activity."""
    if not course_query or len(course_query.strip()) < 3:
        raise HTTPException(status_code=400, detail="course_query must be at least 3 characters.")

    q: queue.SimpleQueue[dict] = queue.SimpleQueue()
    done = threading.Event()

    def emit(event: str, data: dict):
        q.put({"event": event, "data": data})

    def worker():
        try:
            emit("start", {"course_query": course_query})
            payload = svc.search(course_query=course_query, progress_cb=emit)
            emit("done", payload)
        except Exception as exc:
            logger.exception("Stream search failed")
            emit("error", {"detail": "Search failed."})
        finally:
            done.set()

    threading.Thread(target=worker, daemon=True).start()

    def stream():
        while not (done.is_set() and q.empty()):
            item = q.get()
            yield f"event: {item['event']}\n"
            yield "data: " + json.dumps(item["data"]) + "\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
