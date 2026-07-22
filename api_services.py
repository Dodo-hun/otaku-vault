from curl_cffi import requests
import json
import urllib.parse
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json

ANILIST_API_URL = "https://graphql.anilist.co"

async def fetch_media_data(search_title: str, is_manga: bool = True) -> Optional[Dict[int, Any]]:
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
        chapters
      }
    }
    """
    
    # Változók dinamikus beállítása a paraméterek alapján
    variables = {
        "search": search_title,
        "type": "MANGA" if is_manga else "ANIME"
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
            return None
            
        # Adatok normalizálása a Streamlit/SQLModel rendszer számára
        total_units = await auto_fetch_comix_chapter(search_title) if is_manga else media["episodes"]
        
        return {
            "total_units": total_units or 0,
            "status": media["status"]
        }
        
    except requests.exceptions.RequestException:
        return {
                "total_units": await auto_fetch_comix_chapter(search_title) if is_manga else None,
                "status": "UNKNOWN"
                }

async def auto_fetch_comix_chapter(title: str) -> Optional[int]:
    # 1. A cím URL-baráttá tétele (pl. "Mad Dog" -> "Mad+Dog")
    safe_title = urllib.parse.quote_plus(title)
    
    # A Comix.to hivatalos kereső URL-je
    search_url = f"https://comix.to/browse?q={safe_title}&sort=relevance%3Adesc"
    
    async with Stealth().use_async(async_playwright()) as p:
        # Chromium elindítása láthatatlan (headless) módban
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        webdriver_status = await page.evaluate("navigator.webdriver")
        
        try:
            await page.goto(search_url)
            await page.wait_for_selector('.lrow__poster', timeout=10000)
            soup_browse = BeautifulSoup(await page.content(), 'html.parser')
            link_element = soup_browse.find('a', class_='lrow__poster')
            
            if not link_element:
                print("Nem található manga ezzel a címmel.")
                return 0
                
            href = link_element.get('href')
            manga_url = f"https://comix.to{href}"
            
            await page.goto(manga_url)
            
            soup_manga = BeautifulSoup(await page.content(), 'html.parser')
            script_tag = soup_manga.find('script', id='initial-data')
        
            if script_tag and script_tag.string:
                data = json.loads(script_tag.string)
                queries = data.get("queries", {})
                
                for key, value_obj in queries.items():
                    if isinstance(value_obj, dict) and "latestChapter" in value_obj:
                        return int(float(value_obj["latestChapter"]))
            return 0

        except Exception as e:
            print(f"Hiba a Comix keresés során: {e}")
            return 0
        finally:
            await browser.close()
    return 0