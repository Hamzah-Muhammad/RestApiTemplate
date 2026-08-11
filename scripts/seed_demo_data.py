"""Seed the database with sample users, projects, and tasks.

For demoing GET endpoints without having to POST everything live first. Safe
to run more than once - every user is looked up by email first, so re-running
it is a no-op rather than a duplicate-key crash. Run after `alembic upgrade head`:

    python -m scripts.seed_demo_data
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.crud import project as crud_project
from app.crud import task as crud_task
from app.crud import user as crud_user
from app.db import SessionLocal
from app.models.task import TaskStatus
from app.models.user import User
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate
from app.schemas.user import UserCreate

DEMO_PASSWORD = "password123"
TODAY = date.today()


def _get_or_create_user(db: Session, email: str, full_name: str) -> User:
    user = crud_user.get_by_email(db, email)
    if user is not None:
        return user
    return crud_user.create(
        db, UserCreate(email=email, full_name=full_name, password=DEMO_PASSWORD)
    )


def _seed_dana(db: Session, owner: User) -> None:
    if crud_project.list_for_owner(db, owner.id, limit=1, offset=0)[1] > 0:
        return

    website = crud_project.create(
        db,
        owner.id,
        ProjectCreate(name="Website Redesign", description="Q3 marketing site refresh"),
    )
    crud_task.create(
        db,
        website.id,
        TaskCreate(
            title="Wireframe homepage", status=TaskStatus.done, due_date=TODAY - timedelta(days=10)
        ),
    )
    crud_task.create(
        db,
        website.id,
        TaskCreate(
            title="Build component library",
            status=TaskStatus.in_progress,
            due_date=TODAY + timedelta(days=5),
        ),
    )
    crud_task.create(
        db,
        website.id,
        TaskCreate(
            title="Write launch copy", status=TaskStatus.todo, due_date=TODAY + timedelta(days=14)
        ),
    )

    mobile = crud_project.create(
        db, owner.id, ProjectCreate(name="Mobile App v2", description="Native rewrite")
    )
    crud_task.create(db, mobile.id, TaskCreate(title="Set up CI pipeline", status=TaskStatus.done))
    crud_task.create(
        db,
        mobile.id,
        TaskCreate(
            title="Implement push notifications",
            status=TaskStatus.todo,
            due_date=TODAY + timedelta(days=21),
        ),
    )


def _seed_marcus(db: Session, owner: User) -> None:
    if crud_project.list_for_owner(db, owner.id, limit=1, offset=0)[1] > 0:
        return

    budget = crud_project.create(
        db, owner.id, ProjectCreate(name="Q4 Budget Review", description="Finance close-out")
    )
    crud_task.create(
        db,
        budget.id,
        TaskCreate(
            title="Reconcile vendor invoices",
            status=TaskStatus.in_progress,
            due_date=TODAY + timedelta(days=3),
        ),
    )
    crud_task.create(db, budget.id, TaskCreate(title="Draft summary deck", status=TaskStatus.todo))


def main() -> None:
    db = SessionLocal()
    try:
        dana = _get_or_create_user(db, "dana@example.com", "Dana Lee")
        marcus = _get_or_create_user(db, "marcus@example.com", "Marcus Chen")

        _seed_dana(db, dana)
        _seed_marcus(db, marcus)

        print("Seeded:")
        print(f"  user   {dana.email}  (2 projects, 5 tasks)")
        print(f"  user   {marcus.email}  (1 project, 2 tasks)")
        print(f"All passwords: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
