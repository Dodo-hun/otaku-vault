from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Ezt az egy sort kell importálnod
from pydantic import BaseModel
from typing import List
from database import (
    get_all_media, 
    create_db_and_tables, 
    add_media, 
    increment_chapter, 
    update_total_chapters, 
    update_media, 
    delete_media
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Fejlesztés alatt minden külső portot engedélyezünk
    allow_credentials=True,
    allow_methods=["*"], # Engedélyezi a GET, POST, PUT, DELETE metódusokat
    allow_headers=["*"],
)

# --- ADATMODELLEK (Ezek mondják meg, milyen JSON-t vár az API a JS-től) ---

class NewMedias(BaseModel):
    titles: str
    media_type: str

class UpdateMediaData(BaseModel):
    new_title: str
    new_status: str
    new_total_chapters: int
    new_read_chapters: int
    plusz_info: str
    new_manual_change: bool

class BulkRefreshData(BaseModel):
    media_ids: List[int]

# Create table
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Get all medias
@app.get("/api/media")
def read_all_media():
    # Meghívjuk a saját, már létező függvényedet
    results = get_all_media()
    
    # Visszaadjuk a listát, a FastAPI pedig elintézi a JSON-ösítést
    return results

# Add one or more media
@app.post("/api/media")
async def create_media(medias: NewMedias):
    wrongtitles = []
    for title in medias.titles.split("."):                                                                                                                             
        title = title.strip()                                                                                                                               
        if title:
            try:
                await add_media(title=title, media_type=medias.media_type)
                return {"message": f"Added **{title}** as **{medias.media_type}**."} 
            except ValueError: 
                raise HTTPException(status_code=400, detail=f"Media with title **{title}** and type **{medias.media_type}** already exists.")
            except NameError as ne:
                wrongtitles.append(title)
                raise HTTPException(status_code=404, detail=f"Media not found in alternative titles as well please check for spelling errors:\n\n {"\n\n".join(ne.args[0])} \n\n {ne.args[1]}")

# DELETE
@app.delete("/api/media/{media_id}")
def remove_media(media_id: int):
    delete_media(media_id)
    return {"message": "Deleted."}

# Add 1 to read/watched chapters/episodes
@app.post("/api/media/{media_id}/increment")
def increment_media_chapter(media_id: int):
    increment_chapter(media_id)
    return {"message": "+1 chapter or epsiode added."}

# Api refresh
@app.post("/api/media/{media_id}/refresh")
async def refresh_media_chapters(media_id: int):
    await update_total_chapters(media_id)
    return {"message": "Chapter and Status refreshed from API."}

# 2. Add hozzá az új csoportos végpontot
@app.post("/api/media/refresh-bulk")
async def refresh_multiple_media(data: BulkRefreshData):
    for m_id in data.media_ids:
        await update_total_chapters(m_id)
        
    return {"message": f"Chapters and Statuses refreshed from API."}

# Update a media
@app.put("/api/media/{media_id}")
def edit_media(media_id: int, data: UpdateMediaData):
    update_media(
        media_id=media_id,
        new_title=data.new_title,
        new_status=data.new_status,
        new_total_chapters=data.new_total_chapters,
        new_read_chapters=data.new_read_chapters,
        plusz_info=data.plusz_info,
        new_manual_change=data.new_manual_change
    )
    return {"message": "Sikeresen módosítva."}