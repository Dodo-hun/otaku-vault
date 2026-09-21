import asyncio
import streamlit as st
from sqlmodel import Session, select
from database import *

types = ["Manga", "Anime"]
statuses = ["RELEASING", "ONGOING", "FINISHED", "COMPLETE", "CANCELLED", "HIATUS", "UNKNOWN", "DISCONTINUED", "DROPPED", "NONE"]

# 3. Streamlit UI
async def main():
    st.set_page_config(page_title="Otaku Log", page_icon="📚", layout="centered")
    st.title("Manga & Anime Tracker")

    # Adatbázis táblák létrehozása, ha még nem léteznek
    create_db_and_tables()
    
    text = ""

    # Teszt adat hozzáadása UI (Később ezt lecseréljük rendes formra)
    with st.expander("New Media"):
        stitle = st.text_input("Title", value=text)
        smedia_type = st.selectbox("Type", types)
        if st.button("Add"):
            try:
                await add_media(title=stitle, media_type=smedia_type)
                st.success(f"Added **{stitle}** as **{smedia_type}**.")
            except ValueError as e:
                st.error(f"Media with title **{stitle}** and type **{smedia_type}** already exists.")
                
    dialog = False
    with st.expander("Multiple Media"):
        titles = st.text_input("Titles", value=text)
        medias_type = st.selectbox("Types", types)
        if st.button("Add all media"):
            for title in titles.split("."):
                    title = title.strip()
                    if title and not dialog:
                        try:
                            await add_media(title=title, media_type=medias_type)
                            st.success(f"Added **{title}** as **{medias_type}**.")
                        except ValueError as e:
                            st.error(f"Media with title **{title}** and type **{medias_type}** already exists.")

    # Adatok lekérdezése és megjelenítése
    with Session(engine) as session:
        statement = select(Media)
        results = session.exec(statement).all()
        
        with st.expander("Search & Filter"):
            SearchOrder = st.selectbox("Order by", ["Norm","ASC", "DESC", "UNREAD"])
            if SearchOrder == "Norm":
                results = session.exec(statement.order_by(Media.last_updated.desc())).all()
            elif SearchOrder == "ASC":
                results = session.exec(statement.order_by(Media.title.asc())).all()
            elif SearchOrder == "DESC":
                results = session.exec(statement.order_by(Media.title.desc())).all()
            elif SearchOrder == "UNREAD":
                results = [media for media in results if media.read_chapters < media.total_chapters]
            Search = st.text_input("Search by title")
            results = [media for media in results if Search.lower() in media.title.lower()]
            SearchType = st.selectbox("Filter by type", ["All"] + types)
            if SearchType != "All":
                results = [media for media in results if media.type == SearchType]
            SearchStatus = st.selectbox("Filter by status", ["All"] + statuses)
            if SearchStatus != "All":
                results = [media for media in results if media.status == SearchStatus]
            
                
            
        
        if results:
            st.subheader("Saved media:")
            st.button("API refresh", on_click=lambda: [asyncio.run(update_total_chapters(media_id=media.id)) for media in results])
            for media in results:
                with st.container(border=True):
                    col1, col2 = st.columns([3,1])
                    with col1:
                        if media.type == "Manga":
                            st.write(f"**[{media.title}]({media.url})**  \n({media.type}) - {media.total_chapters} / {media.read_chapters} | Állapot: {media.status}, Plusz info: {media.plusz_info}")
                        else:
                            st.write(f"**[{media.title}]({media.url})**  \n({media.type}) - {media.total_chapters} / {media.read_chapters} | Állapot: {media.status}, Plusz info: {media.plusz_info}")
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
                                    new_s = st.selectbox("Status", statuses, key=f"status_{media.id}", index=statuses.index(media.status))
                                    new_tch = st.number_input("Total chapters" if media.type == "Manga" else "Total episodes", min_value=-1, value=media.total_chapters, key=f"total_{media.id}")
                                    new_cch = st.number_input("Read chapters" if media.type == "Manga" else "Watched episodes", min_value=0, value=media.read_chapters, key=f"read_{media.id}")
                                    new_pi = st.text_input("Plusz info", value=media.plusz_info, key=f"plusz_info_{media.id}")
                                    new_mc = st.checkbox("Manual change", value=media.manual_change, key=f"manual_{media.id}")
                                    if st.button("Save", key=f"upd_{media.id}"):
                                        update_media(media.id, new_t, new_s, new_tch, new_cch, new_pi, new_mc)
                                        st.rerun()
                            with col3:
                                if st.button("🗑️", key=f"delete_{media.id}"):
                                    delete_media(media_id=media.id)
                                    st.rerun()
        else:
            st.write("Not found.")

asyncio.run(main())