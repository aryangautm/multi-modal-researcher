import os

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


class Database:
    def __init__(self):
        self.POSTGRES_URL = os.getenv("POSTGRES_URL")
        if not self.POSTGRES_URL:
            raise ValueError("POSTGRES_URL environment variable not set")

        self.engine = create_engine(self.POSTGRES_URL)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.Base = declarative_base()
        memory_connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }
        self.pool = Connection.connect(self.POSTGRES_URL, **memory_connection_kwargs)

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
