from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine_options = {"pool_pre_ping": True}
if settings.sqlalchemy_url.startswith(("postgresql://", "postgresql+")):
    engine_options["connect_args"] = {"connect_timeout": 10}
engine = create_engine(settings.sqlalchemy_url, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
