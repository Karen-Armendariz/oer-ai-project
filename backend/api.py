from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from search_syllabus import scrape_syllabus

app = FastAPI()


class CourseRequest(BaseModel):
    course: str


@app.get("/")
def root():
    return {"message": "OER AI backend is running"}


@app.post("/search-syllabus")
def search_syllabus_endpoint(request: CourseRequest):
    try:
        result = scrape_syllabus(request.course)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))