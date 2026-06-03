"""ORM model package – import all models so Alembic auto-discovers them."""

from app.models.user_model import User
from app.models.query_model import QueryHistory
from app.models.conversation_model import Conversation, Message
from app.models.dashboard_model import Dashboard, DashboardWidget
from app.models.audit_model import AuditLog

__all__ = [
    "User", "QueryHistory", "Conversation", "Message",
    "Dashboard", "DashboardWidget", "AuditLog",
]
