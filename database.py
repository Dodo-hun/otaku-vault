from sqlmodel import Field, SQLModel, create_engine, Session, select
from datetime import datetime
from typing import Optional

# Adatbázis séma
class Media(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: str
    read_chapters: int = Field(default=0)
    total_chapters: int = Field(default=0)
    status: str = Field(default="Ongoing")  # Alapértelmezett státusz
    new_chapter: str = Field(default="")
    last_updated: datetime = Field(default_factory=datetime.now)

sqlite_file_name = "tracker.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# CRUD műveletek
def add_media(title: str, media_type: str, status: str):
    with Session(engine) as session:
        new_media = Media(title=title, type=media_type, status=status)
        
        session.add(new_media)
        session.commit()

def increment_chapter(media_id: int):
    with Session(engine) as session:
        media = session.get(Media, media_id)
        if media:
            media.read_chapters += 1
            media.last_updated = datetime.now()
            session.add(media)
            session.commit()

def update_media(media_id: int, new_title: str, new_status: str, new_total_chapters: int, new_read_chapters: int, new_chapter: str):
    with Session(engine) as session:
        media = session.get(Media, media_id)
        if media:
            media.title = new_title
            media.status = new_status
            media.total_chapters = new_total_chapters
            media.read_chapters = new_read_chapters
            media.new_chapter = new_chapter
            media.last_updated = datetime.now()
            session.add(media)
            session.commit()

def delete_media(media_id: int):
    with Session(engine) as session:
        media = session.get(Media, media_id)
        if media:
            session.delete(media)
            session.commit()

def get_all_media():
    with Session(engine) as session:
        return session.exec(select(Media).order_by(Media.last_updated.desc())).all()