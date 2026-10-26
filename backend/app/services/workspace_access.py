from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import WorkspaceMembership


def get_workspace_scope(
    db: Session,
    current: User,
    workspace_mode: str,
    workspace_id: str | None,
) -> tuple[str, str | None, str | None]:
    """Validate the requested stock scope and return mode, workspace ID, and member role."""
    if workspace_mode not in {"personal", "business"}:
        raise HTTPException(status_code=422, detail="Unknown inventory workspace mode")
    if workspace_mode == "personal":
        return "personal", None, None
    if not workspace_id:
        return "business", None, None
    role = db.query(WorkspaceMembership.role).filter(
        WorkspaceMembership.workspace_id == workspace_id,
        WorkspaceMembership.user_id == current.id,
    ).scalar()
    if role is None:
        # Do not disclose whether an inaccessible workspace exists.
        raise HTTPException(status_code=404, detail="Business workspace not found")
    return "business", workspace_id, role
