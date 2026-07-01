import streamlit as st
from sqlmodel import Field, SQLModel, create_engine, Session, select
import requests
from datetime import datetime
from typing import Optional

# 1. Adatbázis séma (SQLModel)
class Media(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: str  # "Manga" vagy "Anime"
    read_chapters: int = Field(default=0)
    total_chapters: int = Field(default=0)
    status: str = Field(default="Ongoing") # Ongoing, Finished, Hiatus
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# 2. Adatbázis motor inicializálása (SQLite)
sqlite_file_name = "tracker.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 3. Streamlit UI
def main():
    st.set_page_config(page_title="Otaku Log", page_icon="📚", layout="centered")
    st.title("📚 Manga & Anime Tracker")

    # Adatbázis táblák létrehozása, ha még nem léteznek
    create_db_and_tables()

    # Ideiglenes teszt UI
    st.write("Az importok és az adatbázis motor sikeresen beállítva!")
    
    # Teszt adat hozzáadása UI (Később ezt lecseréljük rendes formra)
    if st.button("Teszt adat hozzáadása"):
        with Session(engine) as session:
            new_media = Media(title="One Piece", type="Manga", read_chapters=1070, total_chapters=1080)
            session.add(new_media)
            session.commit()
            st.success("One Piece hozzáadva az adatbázishoz!")

    # Adatok lekérdezése és megjelenítése
    with Session(engine) as session:
        statement = select(Media)
        results = session.exec(statement).all()
        
        if results:
            st.subheader("Mentett médiák:")
            for media in results:
                st.write(f"**{media.title}** ({media.type}) - {media.read_chapters} / {media.total_chapters} | Állapot: {media.status}")

if __name__ == "__main__":
    main()