"""Create repeatable local-only demo accounts for the FreshSense demo database."""

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models import Base
from app.models.user import User

DEMO_USERS = (
    ("demo@example.com", "FreshSense Demo"),
    ("reviewer@example.com", "FreshSense Reviewer"),
)
DEMO_PASSWORD = "FreshSenseDemo2026!"


def seed_demo_users() -> None:
    with SessionLocal() as session:
        for email, name in DEMO_USERS:
            user = session.scalar(select(User).where(User.email == email))
            if user is None:
                session.add(User(email=email, name=name, hashed_password=get_password_hash(DEMO_PASSWORD)))
        session.commit()


if __name__ == "__main__":
    if not settings.sqlalchemy_url.startswith("sqlite:"):
        raise SystemExit("Refusing to seed demo accounts into a non-local database.")
    Base.metadata.create_all(bind=engine)
    seed_demo_users()
    print("Demo accounts ready: demo@example.com and reviewer@example.com")
