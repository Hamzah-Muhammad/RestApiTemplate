from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate

SORTABLE_FIELDS = {"created_at": Task.created_at, "due_date": Task.due_date, "title": Task.title}


def create(db: Session, project_id: int, task_in: TaskCreate) -> Task:
    task = Task(**task_in.model_dump(), project_id=project_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def list_for_project(
    db: Session,
    project_id: int,
    limit: int,
    offset: int,
    status: TaskStatus | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> tuple[list[Task], int]:
    base = select(Task).where(Task.project_id == project_id)
    if status is not None:
        base = base.where(Task.status == status)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    sort_column = SORTABLE_FIELDS.get(sort_by, Task.created_at)
    order = desc(sort_column) if sort_dir == "desc" else asc(sort_column)
    items = db.scalars(base.order_by(order).offset(offset).limit(limit)).all()
    return list(items), total


def update(db: Session, task: Task, task_in: TaskUpdate) -> Task:
    for field, value in task_in.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
