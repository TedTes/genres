from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="ResumeMatcher API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample job data (in a real app, this would come from a database)
SAMPLE_JOBS = [
    {
        "id": "1",
        "title": "Frontend Developer",
        "company": "TechCorp",
        "location": "Toronto, ON",
        "type": "Full-time",
        "description": "We're looking for a Frontend Developer with React experience",
        "requirements": ["React", "JavaScript", "CSS", "HTML"],
        "postedDate": "2025-02-20",
        "category": "development"
    },
    {
        "id": "2",
        "title": "Backend Engineer",
        "company": "DataSystems",
        "location": "Vancouver, BC",
        "type": "Full-time",
        "description": "Backend role focused on API development and database optimization",
        "requirements": ["Python", "FastAPI", "SQL", "AWS"],
        "postedDate": "2025-02-18",
        "category": "development"
    },
    {
        "id": "3",
        "title": "Marketing Specialist",
        "company": "GrowthCo",
        "location": "Montreal, QC",
        "type": "Contract",
        "description": "Digital marketing specialist with focus on SEO and content",
        "requirements": ["SEO", "Content Marketing", "Analytics", "Social Media"],
        "postedDate": "2025-02-22",
        "category": "marketing"
    },
    {
        "id": "4",
        "title": "Data Analyst",
        "company": "InsightMetrics",
        "location": "Ottawa, ON",
        "type": "Full-time",
        "description": "Analyze business data and create actionable reports",
        "requirements": ["SQL", "Python", "Tableau", "Excel"],
        "postedDate": "2025-02-15",
        "category": "data"
    },
    {
        "id": "5",
        "title": "UX Designer",
        "company": "CreativeMinds",
        "location": "Calgary, AB",
        "type": "Remote",
        "description": "Design intuitive user experiences for web and mobile applications",
        "requirements": ["Figma", "User Research", "Prototyping", "UI Design"],
        "postedDate": "2025-02-21",
        "category": "design"
    }
]

# Job schema
class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    type: str
    description: str
    requirements: List[str]
    postedDate: str
    category: str

# Available job categories
JOB_CATEGORIES = ["development", "marketing", "data", "design", "management"]

@app.get("/")
def read_root():
    return {"message": "Welcome to ResumeMatcher API"}

@app.get("/api/jobs", response_model=List[Job])
def get_jobs(category: Optional[str] = None):
    """
    Get all jobs or filter by category
    """
    if category:
        return [job for job in SAMPLE_JOBS if job["category"] == category]
    return SAMPLE_JOBS

@app.get("/api/categories")
def get_categories():
    """
    Get all available job categories
    """
    return JOB_CATEGORIES

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)