from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine_options = {"pool_pre_ping": True}
if settings.sqlalchemy_url.startswith(("postgresql://", "postgresql+")):
    # Bound recovery from idle network connections that the database has dropped.
    engine_options["pool_recycle"] = 300
    engine_options["connect_args"] = {
        "connect_timeout": 10,
        "tcp_user_timeout": 15000,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 3,
        "options": "-c statement_timeout=30000",
    }
elif settings.sqlalchemy_url.startswith("sqlite:"):
    engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(settings.sqlalchemy_url, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
