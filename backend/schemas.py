from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    course_query: str | None = Field(default=None, description="Course code, e.g. BIOL 1101K")
    syllabus_text: str | None = Field(default=None, description="Raw syllabus text")


class OERResultItem(BaseModel):
    title: str | None = None
    license: str | None = None
    creators: str | None = None
    links: str | None = None
    distance: float | None = None
    keyword_overlap: int | None = None
    score: float | None = None


class SearchResponse(BaseModel):
    query: str | None = None
    syllabus_source: str | None = None
    keywords: list[str] = Field(default_factory=list)
    results: list[OERResultItem] = Field(default_factory=list)
    ingest_error: str | None = Field(
        default=None,
        description="Set when live Open ALG ingest failed; search may use index only.",
    )


class HealthResponse(BaseModel):
    status: str
    chroma_ready: bool = False
    version: str = "1.0.0"
