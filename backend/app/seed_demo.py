"""Create repeatable local-only demo accounts for the FreshSense demo database."""

from datetime import date, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.inventory import InventoryItem
from app.models import Base
from app.models.user import User

DEMO_USERS = (
    ("demo@example.com", "FreshSense Demo"),
    ("reviewer@example.com", "FreshSense Reviewer"),
)
DEMO_PASSWORD = "FreshSenseDemo2026!"
DEMO_STOCK = (
    ("Fresh milk", "Dairy", 2, 3, "refrigerator", "Home fridge"),
    ("Whole wheat bread", "Bread & bakery", 1, 5, "pantry", "Home pantry"),
    ("Canned tuna", "Canned fish", 6, 365, "pantry", "Home pantry"),
    ("Orange juice", "Drinks", 1, 80, "refrigerator", "Home fridge"),
)


def seed_demo_users() -> None:
    with SessionLocal() as session:
        for email, name in DEMO_USERS:
            user = session.scalar(select(User).where(User.email == email))
            if user is None:
                session.add(User(email=email, name=name, hashed_password=get_password_hash(DEMO_PASSWORD)))
        session.commit()

        demo_user = session.scalar(select(User).where(User.email == DEMO_USERS[0][0]))
        assert demo_user is not None
        today = date.today()
        for product_name, category, quantity, days_until_expiry, location, stock_location in DEMO_STOCK:
            exists = session.scalar(
                select(InventoryItem.id).where(
                    InventoryItem.user_id == demo_user.id,
                    InventoryItem.product_name == product_name,
                    InventoryItem.workspace_id.is_(None),
                )
            )
            if exists is None:
                session.add(
                    InventoryItem(
                        user_id=demo_user.id,
                        product_name=product_name,
                        category=category,
                        quantity=quantity,
                        expiry_date=today + timedelta(days=days_until_expiry),
                        expiry_source="user_entered",
                        reminder_days_before=3,
                        storage_location=location,
                        stock_location=stock_location,
                        storage_notes="Synthetic sample batch for the local presentation demo.",
                    )
                )
        session.commit()


if __name__ == "__main__":
    if not settings.sqlalchemy_url.startswith("sqlite:"):
        raise SystemExit("Refusing to seed demo accounts into a non-local database.")
    Base.metadata.create_all(bind=engine)
    seed_demo_users()
    print("Demo accounts and synthetic pantry batches are ready for the local demo.")
