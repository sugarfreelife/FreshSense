import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.seed_demo import seed_demo_users

# Keep first-run local demos self-contained. Production databases are still managed
# exclusively through Alembic migrations.
if settings.sqlalchemy_url.startswith("sqlite:"):
    Base.metadata.create_all(bind=engine)
    ocr_columns = {column["name"] for column in inspect(engine).get_columns("ocr_results")}
    with engine.begin() as connection:
        if "provider" not in ocr_columns:
            connection.execute(
                text("ALTER TABLE ocr_results ADD COLUMN provider VARCHAR(50) NOT NULL DEFAULT 'legacy'")
            )
        if "confidence" not in ocr_columns:
            connection.execute(text("ALTER TABLE ocr_results ADD COLUMN confidence FLOAT"))
        if "expiry_label" not in ocr_columns:
            connection.execute(text("ALTER TABLE ocr_results ADD COLUMN expiry_label VARCHAR(50)"))
        if "expiry_text" not in ocr_columns:
            connection.execute(text("ALTER TABLE ocr_results ADD COLUMN expiry_text VARCHAR(50)"))
        sensor_columns = {column["name"] for column in inspect(engine).get_columns("sensor_readings")}
        if "source" not in sensor_columns:
            connection.execute(
                text("ALTER TABLE sensor_readings ADD COLUMN source VARCHAR(30) NOT NULL DEFAULT 'legacy'")
            )
    seed_demo_users()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


app = FastAPI(title="FreshSense AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/api/v1/demo-status")
def demo_status():
    if not settings.sqlalchemy_url.startswith("sqlite:"):
        return {"mode": "configured"}
    tables = set(inspect(engine).get_table_names())
    return {"mode": "local-demo", "ready": "users" in tables and "tracked_items" in tables}


@app.get("/")
def root():
    return {"service": "freshsense-ai", "docs": "/docs", "health": "/api/v1/health"}
