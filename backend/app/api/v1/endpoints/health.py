from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core import database

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    try:
        with database.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "service": "freshsense-ai", "database": "ok"}
