from curl_cffi import requests
import json
import urllib.parse
from typing import Dict, Any
import re

ANILIST_API_URL = "https://graphql.anilist.co"

async def fetch_media_data(search_title: str, is_manga: bool = True) -> Dict[int, Any]:
    if is_manga:
        #try:
        #    return await auto_fetch_comix_chapter(search_title)
        #except Exception:
        return await auto_fetch_mangaupdates(search_title)
    else:
        # GraphQL lekérdezés felépítése
        query = """
        query ($search: String, $type: MediaType) {
          Media (search: $search, type: $type) {
            id
            title {
              romaji
              english
            }
            status
            episodes
          }
        }
        """

        # Változók dinamikus beállítása a paraméterek alapján
        variables = {
            "search": search_title,
            "type":"ANIME"
        }

        try:
            response = requests.post(
                ANILIST_API_URL, 
                json={'query': query, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            media = data.get("data", {}).get("Media")
            if not media:
                return {"total_units": -1, "status": "UNKNOWN", "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(search_title)}"}

            return {
                "total_units": media.get("episodes") or 0,
                "status": media["status"],
                "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(search_title)}"
            }

        except requests.exceptions.RequestException:
            return {
                    "total_units": -1,
                    "status": "UNKNOWN",
                    "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(search_title)}"
                    }


async def auto_fetch_mangaupdates(title: str) -> dict[int, Any]:
    try:
        series_id = None
        
        search_url = "https://api.mangaupdates.com/v1/series/search"
        search_payload = {"search": title, "perpage": 2}
        search_resp = requests.post(search_url, json=search_payload, timeout=10)
        search_resp.raise_for_status()
            
        results = search_resp.json().get("results", [])
        if not results:
            return {"total_units": -1, "status": "UNKNOWN", "url": f"https://comix.to/browse?q={urllib.parse.quote_plus(title)}&sort=relevance%3Adesc&types=manga%2Cmanhwa%2Cmanhua"}
        
        for result in results:
            record = result.get("record", {})
            type = record.get("type","").lower()
            if type != "novel":
                series_id = result.get("record", {}).get("series_id")
                break
        
        if not series_id:
            return {"total_units": -1, "status": "UNKNOWN", "url": f"https://comix.to/browse?q={urllib.parse.quote_plus(title)}&sort=relevance%3Adesc&types=manga%2Cmanhwa%2Cmanhua"}
        
        detail_url = f"https://api.mangaupdates.com/v1/series/{series_id}"
        detail_resp = requests.get(detail_url, timeout=10)
        detail_resp.raise_for_status()
        detail_data = detail_resp.json()
        #print(detail_data)
        
        is_this_it = False
        
        alt_titles = detail_data.get("associated", [])
        alt_titles.append({"title": detail_data.get("title", "")})
        #print(f"Alt titles: {alt_titles}")
        for alt in alt_titles:
            alt_title = alt.get("title", "")
            if alt_title.lower() == title.lower():
                is_this_it = True
            
        if not is_this_it:
            return {"total_units": -1, "status": "UNKNOWN", "url": detail_url}
        
        status = str(detail_data.get("status", "UNKNOWN")).upper()
        if "COMPLETE" in status:
            status = "COMPLETE"
        elif "ONGOING" in status:
            status = "ONGOING"
        elif "HIATUS" in status:
            status = "HIATUS"
        elif "CANCELLED" in status:
            status = "CANCELLED"
        elif "DISCONTINUED" in status:
            status = "DISCONTINUED"
        elif "DROPPED" in status:
            status = "DROPPED"
        
        
        chapters = detail_data.get("latest_chapter",-1)
        try:
            ch_from_status = int(str(detail_data.get("status", "0")).split()[0])
            if chapters < ch_from_status:
                chapters = ch_from_status
        except:
            pass
        return {
            "total_units": chapters,
            "status": status,
            #"url": detail_url
            "url": f"https://comix.to/browse?q={urllib.parse.quote_plus(title)}&sort=relevance%3Adesc&types=manga%2Cmanhwa%2Cmanhua"
        }
    except Exception as e:
        print(f"Hiba a MangaUpdates API lekérésekor: {e}")
        return {"total_units": -1, "status": "UNKNOWN", "url": f"https://comix.to/browse?q={urllib.parse.quote_plus(title)}&sort=relevance%3Adesc&types=manga%2Cmanhwa%2Cmanhua"}

    