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
    sensor_columns = {column["name"] for column in inspect(engine).get_columns("sensor_readings")}
    inventory_columns = {column["name"] for column in inspect(engine).get_columns("inventory_items")}
    scan_columns = {column["name"] for column in inspect(engine).get_columns("food_scans")}
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
        if "source" not in sensor_columns:
            connection.execute(
                text("ALTER TABLE sensor_readings ADD COLUMN source VARCHAR(30) NOT NULL DEFAULT 'legacy'")
            )
        if "reminder_days_before" not in inventory_columns:
            connection.execute(text("ALTER TABLE inventory_items ADD COLUMN reminder_days_before INTEGER"))
        if "storage_location" not in inventory_columns:
            connection.execute(text("ALTER TABLE inventory_items ADD COLUMN storage_location VARCHAR(40) NOT NULL DEFAULT 'unknown'"))
        if "opened_date" not in inventory_columns:
            connection.execute(text("ALTER TABLE inventory_items ADD COLUMN opened_date DATE"))
        if "storage_notes" not in inventory_columns:
            connection.execute(text("ALTER TABLE inventory_items ADD COLUMN storage_notes TEXT"))
        if "workspace_id" not in inventory_columns:
            connection.execute(text("ALTER TABLE inventory_items ADD COLUMN workspace_id VARCHAR(36)"))
        if "stock_location" not in inventory_columns:
            connection.execute(text("ALTER TABLE inventory_items ADD COLUMN stock_location VARCHAR(120)"))
        if "workspace_id" not in scan_columns:
            connection.execute(text("ALTER TABLE food_scans ADD COLUMN workspace_id VARCHAR(36)"))
    seed_demo_users()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


is_production = settings.ENVIRONMENT == "production"
app = FastAPI(
    title="FreshSense AI",
    version="0.1.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

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
    required_tables = {"users", "tracked_items", "inventory_items"}
    missing_tables = sorted(required_tables - tables)
    return {
        "mode": "local-demo",
        "ready": not missing_tables,
        "missing_tables": missing_tables,
    }


@app.get("/")
def root():
    response = {"service": "freshsense-ai", "health": "/api/v1/health"}
    if not is_production:
        response["docs"] = "/docs"
    return response
