from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import register_error_handlers
from app.db import get_db
from app.routers import auth, projects, tasks

API_V1_PREFIX = "/v1"

app = FastAPI(
    title="RestAPI - User Management Example",
    description="A production-hygiene FastAPI template: JWT auth, CRUD, pagination, tests, "
    "Docker, CI.",
    version="1.0.0",
)
register_error_handlers(app)

# All resource routes live under a version prefix so a breaking change can ship as /v2
# alongside /v1 instead of breaking existing clients. Health endpoints stay unversioned:
# infrastructure (load balancers, Docker HEALTHCHECK) shouldn't have to track API versions.
api_v1 = APIRouter(prefix=API_V1_PREFIX)
api_v1.include_router(auth.router)
api_v1.include_router(projects.router)
api_v1.include_router(tasks.projects_tasks_router)
api_v1.include_router(tasks.tasks_router)
app.include_router(api_v1)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness: the process is up and serving requests."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness: the process can actually do work (database reachable)."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable"
        ) from exc
    return {"status": "ok", "database": "ok"}
