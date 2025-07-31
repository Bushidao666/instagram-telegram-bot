from sqlmodel import create_engine, SQLModel, Session
from pathlib import Path

# Create database directory if it doesn't exist
db_path = Path(__file__).parent.parent / "database.db"
db_path.parent.mkdir(exist_ok=True)

sqlite_url = f"sqlite:///{db_path}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session