from curl_cffi import requests
import json
import urllib.parse
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json
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
                return {"total_units": -1, "status": "UNKNOWN", "url": ""}

            return {
                "total_units": media.get("episodes") or 0,
                "status": media["status"],
                "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(search_title)}"
            }

        except requests.exceptions.RequestException:
            return {
                    "total_units": -1,
                    "status": "UNKNOWN",
                    "url": ""
                    }

async def auto_fetch_comix_chapter(title: str) -> dict[int, Any]:
    # 1. A cím URL-baráttá tétele (pl. "Mad Dog" -> "Mad+Dog")
    safe_title = urllib.parse.quote_plus(title)
    
    # A Comix.to hivatalos kereső URL-je
    search_url = f"https://comix.to/browse?q={safe_title}&sort=relevance%3Adesc&types=manga%2Cmanhwa%2Cmanhua"
    
    async with Stealth().use_async(async_playwright()) as p:
        # Chromium elindítása láthatatlan (headless) módban
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(search_url)
            await page.wait_for_selector('.lrow__poster', timeout=10)
            soup_browse = BeautifulSoup(await page.content(), 'html.parser')
            link_element = soup_browse.find('a', class_='lrow__poster')
            
            if not link_element:
                print("Nem található manga ezzel a címmel.")
                return {"total_units": -1, "status": "UNKNOWN", "url": ""}
                
            href = link_element.get('href')
            manga_url = f"https://comix.to{href}"
            
            await page.goto(manga_url)
            
            soup_manga = BeautifulSoup(await page.content(), 'html.parser')
            script_tag = soup_manga.find('script', id='initial-data')
        
            if script_tag and script_tag.string:
                data = json.loads(script_tag.string)
                queries = data.get("queries", {})
                
                for key, value_obj in queries.items():
                    if isinstance(value_obj, dict):
                        latest_chapter = value_obj.get("latestChapter")
                        if latest_chapter is not None:
                            chapters = int(float(latest_chapter))
                            status = str(value_obj.get("status", "UNKNOWN")).upper()
                        return {"total_units": chapters, "status": status, "url": manga_url}
            return {"total_units": -1, "status": "UNKNOWN", "url": ""}

        except Exception as e:
            raise e
        finally:
            await browser.close()
    return {"total_units": -1, "status": "UNKNOWN", "url": ""}

async def auto_fetch_mangaupdates(title: str) -> dict[int, Any]:
    try:
        series_id = None
        
        search_url = "https://api.mangaupdates.com/v1/series/search"
        search_payload = {"search": title, "perpage": 2}
        search_resp = requests.post(search_url, json=search_payload, timeout=10)
        search_resp.raise_for_status()
            
        results = search_resp.json().get("results", [])
        if not results:
            return {"total_units": -1, "status": "UNKNOWN", "url": ""}
        
        for result in results:
            record = result.get("record", {})
            type = record.get("type","").lower()
            if type != "novel":
                series_id = result.get("record", {}).get("series_id")
                break
        
        if not series_id:
            return {"total_units": -1, "status": "UNKNOWN", "url": ""}
        
        detail_url = f"https://api.mangaupdates.com/v1/series/{series_id}"
        detail_resp = requests.get(detail_url, timeout=10)
        detail_resp.raise_for_status()
        detail_data = detail_resp.json()
        
        is_this_it = False
        
        alt_titles = detail_data.get("associated", [])
        alt_titles.append({"title": detail_data.get("title", "")})
        #print(f"Alt titles: {alt_titles}")
        for alt in alt_titles:
            alt_title = alt.get("title", "")
            if alt_title.lower() == title.lower():
                is_this_it = True
            
        if not is_this_it:
            return {"total_units": -1, "status": "UNKNOWN", "url": ""}
        
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
        
        return {
            "total_units": chapters,
            "status": status,
            #"url": detail_url
            "url": f"https://comix.to/browse?q={urllib.parse.quote_plus(title)}&sort=relevance%3Adesc&types=manga%2Cmanhwa%2Cmanhua"
        }
    except Exception as e:
        print(f"Hiba a MangaUpdates API lekérésekor: {e}")
        return {"total_units": -1, "status": "UNKNOWN", "url": ""}
    return {"total_units": -1, "status": "UNKNOWN", "url": ""}

    