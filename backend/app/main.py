import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings

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


@app.get("/")
def root():
    return {"service": "freshsense-ai", "docs": "/docs", "health": "/api/v1/health"}
