"""Script to seed initial database records (admin, user, dashboards, conversations)."""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user_model import User
from app.models.conversation_model import Conversation, Message
from app.models.dashboard_model import Dashboard, DashboardWidget


async def main() -> None:
    settings = get_settings()
    
    print("Database seeding started...")
    db_engine = create_async_engine(settings.DATABASE_URL)
    
    # ── Create all tables if they do not exist ───────────────────
    from app.db.base import Base
    import app.models
    async with db_engine.begin() as conn:
        print("Creating all tables in database if they do not exist...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables verified/created.")

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async with session_factory() as session:
        # Check if users already exist
        result = await session.execute(select(User))

        existing_users = result.scalars().all()
        if existing_users:
            print("Users already exist. Skipping database seeding.")
            await db_engine.dispose()
            return

        # ── 1. Create Users ──────────────────────────────────────────
        admin = User(
            email="admin@ragchatbot.com",
            hashed_password=hash_password("AdminSecurePassword123!"),
            full_name="System Admin",
            role="admin",
            is_active=True,
        )
        user = User(
            email="user@ragchatbot.com",
            hashed_password=hash_password("UserSecurePassword123!"),
            full_name="Business Analyst",
            role="user",
            is_active=True,
        )
        session.add_all([admin, user])
        await session.commit()
        print(f"Created Admin: {admin.email} (Password: AdminSecurePassword123!)")
        print(f"Created User:  {user.email} (Password: UserSecurePassword123!)")

        # ── 2. Create sample conversation ──────────────────────────
        conv = Conversation(
            user_id=user.id,
            title="Sales Performance Analysis",
        )
        session.add(conv)
        await session.commit()

        msg_user = Message(
            conversation_id=conv.id,
            role="user",
            content="Show me total sales by region",
        )
        msg_assistant = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Sure! Here is the breakdown of sales by geographic region.",
            metadata_json={"sql_query": "SELECT region, SUM(sales) AS total_sales FROM sales_data GROUP BY region;"},
        )
        session.add_all([msg_user, msg_assistant])

        # ── 3. Create sample dashboard ──────────────────────────────
        dash = Dashboard(
            user_id=user.id,
            title="Executive Sales Dashboard",
            description="High-level financial performance metrics and charts.",
        )
        session.add(dash)
        await session.commit()

        widget = DashboardWidget(
            dashboard_id=dash.id,
            chart_type="bar",
            title="Total Sales by Region",
            chart_config_json={
                "type": "bar",
                "x": ["North", "South", "East", "West"],
                "y": [120000, 95000, 150000, 80000],
                "marker": {"color": "#6366f1"},
            },
            position_x=0,
            position_y=0,
            width=6,
            height=4,
        )
        session.add(widget)
        await session.commit()

        print("Database seeded successfully with users, conversations, and dashboards.")

    await db_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
