from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

from app.config import settings
from app.database import engine, Base
from app.routers import patients, sessions, analyze, dashboard, fusion, history

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router, prefix=settings.API_V1_STR)
app.include_router(sessions.router, prefix=settings.API_V1_STR)
app.include_router(analyze.router, prefix=settings.API_V1_STR)
app.include_router(fusion.router, prefix=settings.API_V1_STR)
app.include_router(history.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to MEDHA AI API"}

@app.get("/test", response_class=HTMLResponse)
def read_test_ui():
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
    with open(template_path, "r") as f:
        return f.read()
