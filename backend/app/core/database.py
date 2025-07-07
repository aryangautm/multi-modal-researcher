from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings


class Database:
    def __init__(self):
        self.DATABASE_URL = settings.DATABASE_URL
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable not set")

        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.Base = declarative_base()
        memory_connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }
        self.pool = Connection.connect(self.DATABASE_URL, **memory_connection_kwargs)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# Create an instance of the database
db = Database()
pg_checkpointer = PostgresSaver(db.pool)
pg_checkpointer.setup()
