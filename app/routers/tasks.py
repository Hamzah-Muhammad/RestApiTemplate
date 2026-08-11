from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud import task as crud_task
from app.db import get_db
from app.deps import Pagination, get_current_user
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.routers.projects import get_owned_project_or_404
from app.schemas.task import TaskCreate, TaskOut, TaskPage, TaskUpdate

projects_tasks_router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task_or_404(db: Session, task_id: int, owner_id: int) -> Task:
    task = crud_task.get(db, task_id)
    if task is None or task.project.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@projects_tasks_router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    get_owned_project_or_404(db, project_id, current_user.id)
    return crud_task.create(db, project_id, task_in)


@projects_tasks_router.get("", response_model=TaskPage)
def list_tasks(
    project_id: int,
    task_status: TaskStatus | None = Query(default=None, alias="status"),
    sort_by: str = Query(default="created_at", pattern="^(created_at|due_date|title)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskPage:
    get_owned_project_or_404(db, project_id, current_user.id)
    items, total = crud_task.list_for_project(
        db,
        project_id,
        pagination.limit,
        pagination.offset,
        status=task_status,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return TaskPage(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


@tasks_router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    return _get_owned_task_or_404(db, task_id, current_user.id)


@tasks_router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = _get_owned_task_or_404(db, task_id, current_user.id)
    return crud_task.update(db, task, task_in)


@tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    task = _get_owned_task_or_404(db, task_id, current_user.id)
    crud_task.delete(db, task)
