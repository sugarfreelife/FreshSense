from pathlib import Path

from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core import database

router = APIRouter(tags=["health"])
_required_revisions = set(
    ScriptDirectory(str(Path(__file__).resolve().parents[4] / "alembic")).get_heads()
)


@router.get("/health")
def health():
    try:
        with database.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            if connection.dialect.name == "postgresql":
                current_revisions = set(MigrationContext.configure(connection).get_current_heads())
                if current_revisions != _required_revisions:
                    raise HTTPException(
                        status_code=503,
                        detail="Database schema is out of date. Run 'alembic upgrade head' from the backend directory.",
                    )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "service": "freshsense-ai", "database": "ok"}
