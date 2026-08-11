from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import project as crud_project
from app.db import get_db
from app.deps import Pagination, get_current_user
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut, ProjectPage, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


def get_owned_project_or_404(db: Session, project_id: int, owner_id: int) -> Project:
    project = crud_project.get(db, project_id)
    if project is None or project.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    return crud_project.create(db, current_user.id, project_in)


@router.get("", response_model=ProjectPage)
def list_projects(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectPage:
    items, total = crud_project.list_for_owner(
        db, current_user.id, pagination.limit, pagination.offset
    )
    return ProjectPage(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    return get_owned_project_or_404(db, project_id, current_user.id)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = get_owned_project_or_404(db, project_id, current_user.id)
    return crud_project.update(db, project, project_in)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    project = get_owned_project_or_404(db, project_id, current_user.id)
    crud_project.delete(db, project)
