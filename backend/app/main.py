import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from app.config import settings
from app.database import engine, Base
from app.routers import (
    auth_router,
    facilities_router,
    checklists_router,
    inspections_router,
    audit_router
)

# Auto-create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Smart Inspection and Risk Prevention System - REST API for Field Inspection & Supervisor Governance",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Web and Mobile development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static media uploads for photos/evidence
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Frontend directory path
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Include Routers
app.include_router(auth_router.router, prefix=settings.API_PREFIX)
app.include_router(facilities_router.router, prefix=settings.API_PREFIX)
app.include_router(checklists_router.router, prefix=settings.API_PREFIX)
app.include_router(inspections_router.router, prefix=settings.API_PREFIX)
app.include_router(audit_router.router, prefix=settings.API_PREFIX)

@app.get("/", include_in_schema=False)
def root():
    # If index.html exists in frontend, serve it
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": settings.DATABASE_URL.split("://")[0]
    }
