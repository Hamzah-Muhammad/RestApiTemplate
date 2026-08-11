from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create(db: Session, owner_id: int, project_in: ProjectCreate) -> Project:
    project = Project(**project_in.model_dump(), owner_id=owner_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get(db: Session, project_id: int) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()


def list_for_owner(
    db: Session, owner_id: int, limit: int, offset: int
) -> tuple[list[Project], int]:
    query = db.query(Project).filter(Project.owner_id == owner_id)
    total = query.count()
    items = query.order_by(Project.created_at.desc()).offset(offset).limit(limit).all()
    return items, total


def update(db: Session, project: Project, project_in: ProjectUpdate) -> Project:
    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
