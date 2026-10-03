import streamlit as st
from sqlmodel import Field, SQLModel, create_engine, Session, select
from datetime import datetime, timezone
from typing import Optional
from api_services import *

# Adatbázis séma
class Media(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: str
    read_chapters: int = Field(default=0)
    total_chapters: int = Field(default=0)
    status: str = Field(default="Ongoing")  # Alapértelmezett státusz
    plusz_info: str = Field(default="")
    last_updated: datetime = Field(default_factory=datetime.now)
    url: str = Field(default="")  # Új mező az URL tárolására
    manual_change: bool = Field(default=False)

cloud_url = st.secrets["DATABASE_URL"] # change this to your own database URL
engine = create_engine(cloud_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# CRUD műveletek
async def add_media(title: str, media_type: str):
    with Session(engine) as session:
        new_media = Media(title=title, type=media_type)
        media = session.exec(select(Media).where(Media.title == title, Media.type == media_type)).first()
        if not media:
            fetched_data = await fetch_media_data(new_media.title, is_manga=(new_media.type == "Manga"))
            if fetched_data:
                new_media.total_chapters = fetched_data["total_units"]
                new_media.status = fetched_data["status"]
                new_media.url = fetched_data["url"]
                new_media.last_updated = datetime.now(tz= timezone.utc)
                session.add(new_media)
        else:
            raise ValueError(title, media_type)
        session.commit()

def increment_chapter(media_id: int):
    with Session(engine) as session:
        media = session.get(Media, media_id)
        if media:
            media.read_chapters += 1
            media.last_updated = datetime.now(tz= timezone.utc)
            session.add(media)
        session.commit()

async def update_total_chapters(media_id: int):
    with Session(engine) as session:
        media = session.get(Media, media_id)
        fetched_data = await fetch_media_data(media.title, is_manga=(media.type == "Manga"))
        if fetched_data and not media.manual_change and media.status != "COMPLETE" and media.status != "FINISHED":
            media.total_chapters = fetched_data["total_units"]
            media.status = fetched_data["status"]
            media.url = fetched_data["url"]
            media.last_updated = datetime.now(tz= timezone.utc)
            session.add(media)
        session.commit()

def update_media(media_id: int, new_title: str, new_status: str, new_total_chapters: int, new_read_chapters: int, plusz_info: str, new_manual_change: bool):
    with Session(engine) as session:
        media = session.get(Media, media_id)
        if media:
            media.title = new_title
            media.status = new_status
            media.total_chapters = new_total_chapters
            media.read_chapters = new_read_chapters
            media.plusz_info = plusz_info
            media.manual_change = new_manual_change
            media.last_updated = datetime.now(tz= timezone.utc)
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