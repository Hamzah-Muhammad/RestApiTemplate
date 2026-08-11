from fastapi import FastAPI

from app.routers import auth, projects, tasks

app = FastAPI(
    title="RestApiTemplate",
    description="A production-hygiene FastAPI template: JWT auth, CRUD, pagination, tests, "
    "Docker, CI.",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.projects_tasks_router)
app.include_router(tasks.tasks_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
