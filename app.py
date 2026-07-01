import streamlit as st
from sqlmodel import Field, SQLModel, create_engine, Session, select
import requests
from datetime import datetime
from typing import Optional
from database import *
from PIL import Image
import pytesseract

# 3. Streamlit UI
def main():
    st.set_page_config(page_title="Otaku Log", page_icon="📚", layout="centered")
    st.title("Manga & Anime Tracker")

    # Adatbázis táblák létrehozása, ha még nem léteznek
    create_db_and_tables()
    
    uploaded_file = st.file_uploader("Upload Image",type=["jpg", "jpeg", "png"])
    text = ""
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Feltöltött kép')
        try:
            # Kép szöveggé alakítása
            text = pytesseract.image_to_string(image, lang='hun+eng')
        except Exception as e:
            st.error("Hiba történt a szövegfelismerés során. Ellenőrizd, hogy a Tesseract telepítve van-e.")

    # Teszt adat hozzáadása UI (Később ezt lecseréljük rendes formra)
    with st.expander("New Media"):
        title = st.text_input("Title", value=text)
        media_type = st.selectbox("Type", ["Manga", "Anime"])
        status = st.selectbox("Status", ["Ongoing", "Completed", "On Hold", "Dropped", "Hiatus"])
        if st.button("Add"):
            add_media(title=title, media_type=media_type, status=status)



    # Adatok lekérdezése és megjelenítése
    with Session(engine) as session:
        statement = select(Media)
        results = session.exec(statement).all()
        
        with st.expander("Search & Filter"):
            Search = st.text_input("Search by title")
            if Search:
                results = [media for media in results if Search.lower() in media.title.lower()]
            SearchType = st.selectbox("Filter by type", ["All", "Manga", "Anime"])
            if SearchType != "All":
                results = [media for media in results if media.type == SearchType]
            SearchStatus = st.selectbox("Filter by status", ["All", "Ongoing", "Completed", "On Hold", "Dropped", "Hiatus"])
            if SearchStatus != "All":
                results = [media for media in results if media.status == SearchStatus]
            SearchOrder = st.selectbox("Order by", ["Norm","ASC", "DESC"])
            if SearchOrder == "ASC":
                results = session.exec(statement.order_by(Media.title.asc())).all()
            elif SearchOrder == "DESC":
                results = session.exec(statement.order_by(Media.title.desc())).all()
                
            
        
        if results:
            st.subheader("Saved media:")
            for media in results:
                update_total_chapters(media_id=media.id) # Update total chapters based on elapsed time
                with st.container(border=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        if media.type == "Manga":
                            st.write(f"{media.title}  \n({media.type}) - {media.total_chapters} / {media.read_chapters} | Állapot: {media.status}, New Chapter on: {media.new_chapter}")
                        else:
                            st.write(f"{media.title}  \n({media.type}) - {media.total_chapters} / {media.read_chapters} | Állapot: {media.status}, New Episode on: {media.new_chapter}")
                    with col2:
                        with st.container():
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("➕", key=f"increment_{media.id}"):
                                    increment_chapter(media_id=media.id)
                                    st.rerun()
                            with col2:
                                with st.popover("✏️"):
                                    new_t = st.text_input("New name", value=media.title, key=f"title_{media.id}")
                                    new_s = st.selectbox("Status", ["Ongoing", "Completed", "On Hold", "Dropped", "Hiatus"], key=f"status_{media.id}", index=["Ongoing", "Completed", "On Hold", "Dropped", "Hiatus"].index(media.status))
                                    new_tch = st.number_input("Total", min_value=0, value=media.total_chapters, key=f"total_{media.id}")
                                    new_cch = st.number_input("Read chapters", min_value=0, value=media.read_chapters, key=f"read_{media.id}")
                                    new_nch = st.text_input("New chapter/episode", value=media.new_chapter, key=f"new_chapter_{media.id}")
                                    if st.button("Save", key=f"upd_{media.id}"):
                                        update_media(media.id, new_t, new_s, new_tch, new_cch, new_nch)
                                        st.rerun()
                            with col3:
                                if st.button("🗑️", key=f"delete_{media.id}"):
                                    delete_media(media_id=media.id)
                                    st.rerun()
        else:
            st.write("Not found.")

if __name__ == "__main__":
    main()