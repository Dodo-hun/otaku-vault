import streamlit as st
from sqlmodel import Field, SQLModel, create_engine, Session, select
import requests
from datetime import datetime
from typing import Optional
from database import *

# 3. Streamlit UI
def main():
    st.set_page_config(page_title="Otaku Log", page_icon="📚", layout="centered")
    st.title("Manga & Anime Tracker")

    # Adatbázis táblák létrehozása, ha még nem léteznek
    create_db_and_tables()

    # Ideiglenes teszt UI
    st.write("Az importok és az adatbázis motor sikeresen beállítva!")
    
    # Teszt adat hozzáadása UI (Később ezt lecseréljük rendes formra)
    title = st.text_input("Cím")
    media_type = st.selectbox("Típus", ["Manga", "Anime"])
    status = st.selectbox("Állapot", ["Ongoing", "Completed", "On Hold", "Dropped", "Hiatus"])
    if st.button("Teszt adat hozzáadása"):
        add_media(title=title, media_type=media_type, status=status)



    # Adatok lekérdezése és megjelenítése
    with Session(engine) as session:
        statement = select(Media)
        results = session.exec(statement).all()
        
        if results:
            st.subheader("Mentett médiák:")
            for media in results:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{media.title}**\n\n({media.type}) - {media.total_chapters} / {media.read_chapters} | Állapot: {media.status}, New Chapter on: {media.new_chapter}")
                    with col2:
                        with st.container():
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("➕", key=f"increment_{media.id}"):
                                    increment_chapter(media_id=media.id)
                                    st.rerun()
                            with col2:
                                with st.popover("✏️"):
                                    new_t = st.text_input("Új cím", value=media.title, key=f"title_{media.id}")
                                    new_s = st.selectbox("Állapot", ["Ongoing", "Completed", "On Hold", "Dropped", "Hiatus"], key=f"status_{media.id}", index=["Ongoing", "Completed", "On Hold", "Dropped", "Hiatus"].index(media.status))
                                    new_tch = st.number_input("Összes fejezet", min_value=0, value=media.total_chapters, key=f"total_{media.id}")
                                    new_cch = st.number_input("Elolvasott fejezet", min_value=0, value=media.read_chapters, key=f"read_{media.id}")
                                    new_nch = st.text_input("Új fejezet", value=media.new_chapter, key=f"new_chapter_{media.id}")
                                    if st.button("Mentés", key=f"upd_{media.id}"):
                                        update_media(media.id, new_t, new_s, new_tch, new_cch, new_nch)
                                        st.rerun()
                            with col3:
                                if st.button("🗑️", key=f"delete_{media.id}"):
                                    delete_media(media_id=media.id)
                                    st.rerun()

if __name__ == "__main__":
    main()