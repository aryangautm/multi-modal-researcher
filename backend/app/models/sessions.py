import datetime
import uuid

from core.database import db
from sqlalchemy import Column, DateTime, String


class Session(db.Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"<Session(session_id='{self.session_id}', user_id='{self.user_id}')>"
