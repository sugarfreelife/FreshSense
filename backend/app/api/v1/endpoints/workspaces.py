from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.workspace import BusinessWorkspace, WorkspaceMembership
from app.schemas.workspace import (
    BusinessWorkspaceCreate,
    BusinessWorkspaceOut,
    WorkspaceMemberCreate,
    WorkspaceMemberOut,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _workspace_out(workspace: BusinessWorkspace, role: str) -> dict:
    return {
        "id": workspace.id,
        "name": workspace.name,
        "role": role,
        "created_at": workspace.created_at,
    }


def _require_member(db: Session, workspace_id: str, user_id: str) -> WorkspaceMembership:
    membership = (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.workspace_id == workspace_id, WorkspaceMembership.user_id == user_id)
        .first()
    )
    if membership is None:
        # Do not disclose whether an inaccessible workspace exists.
        raise HTTPException(status_code=404, detail="Business workspace not found")
    return membership


@router.get("", response_model=list[BusinessWorkspaceOut])
def list_workspaces(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    memberships = (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.user_id == current.id)
        .order_by(WorkspaceMembership.created_at.asc())
        .all()
    )
    return [_workspace_out(row.workspace, row.role) for row in memberships]


@router.post("", response_model=BusinessWorkspaceOut, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: BusinessWorkspaceCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Workspace name is required")
    workspace = BusinessWorkspace(name=name, created_by_user_id=current.id)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMembership(workspace_id=workspace.id, user_id=current.id, role="owner"))
    db.commit()
    db.refresh(workspace)
    return _workspace_out(workspace, "owner")


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberOut])
def list_members(
    workspace_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    _require_member(db, workspace_id, current.id)
    memberships = (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.workspace_id == workspace_id)
        .order_by(WorkspaceMembership.created_at.asc())
        .all()
    )
    return [
        {
            "id": row.id,
            "user_id": row.user.id,
            "email": row.user.email,
            "name": row.user.name,
            "role": row.role,
            "created_at": row.created_at,
        }
        for row in memberships
    ]


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    workspace_id: str,
    payload: WorkspaceMemberCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    actor = _require_member(db, workspace_id, current.id)
    if actor.role not in {"owner", "manager"}:
        raise HTTPException(status_code=403, detail="Only workspace owners and managers can add members")
    if actor.role == "manager" and payload.role != "staff":
        raise HTTPException(status_code=403, detail="Managers can add staff members only")

    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if user is None:
        raise HTTPException(status_code=404, detail="That email does not belong to a registered FreshSense account")
    if db.query(WorkspaceMembership.id).filter(
        WorkspaceMembership.workspace_id == workspace_id,
        WorkspaceMembership.user_id == user.id,
    ).first():
        raise HTTPException(status_code=409, detail="This account is already a workspace member")

    membership = WorkspaceMembership(workspace_id=workspace_id, user_id=user.id, role=payload.role)
    db.add(membership)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This account is already a workspace member") from exc
    db.refresh(membership)
    return {
        "id": membership.id,
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "role": membership.role,
        "created_at": membership.created_at,
    }


@router.delete("/{workspace_id}/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    workspace_id: str,
    membership_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    actor = _require_member(db, workspace_id, current.id)
    target = (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.id == membership_id, WorkspaceMembership.workspace_id == workspace_id)
        .first()
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Workspace member not found")
    if target.role == "owner":
        raise HTTPException(status_code=409, detail="Transfer workspace ownership before removing its owner")
    if current.id != target.user_id and actor.role != "owner":
        raise HTTPException(status_code=403, detail="Only the workspace owner can remove another member")
    db.delete(target)
    db.commit()
    return None
