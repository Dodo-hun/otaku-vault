import requests
import json
import urllib.parse
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

ANILIST_API_URL = "https://graphql.anilist.co"

def fetch_media_data(search_title: str, is_manga: bool = True) -> Optional[Dict[int, Any]]:
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
        total_units = auto_fetch_comix_chapter(search_title) if is_manga else media["episodes"]
        
        return {
            "total_units": total_units or 0,
            "status": media["status"]
        }
        
    except requests.exceptions.RequestException:
        return None

def auto_fetch_comix_chapter(title: str) -> Optional[int]:
    # 1. A cím URL-baráttá tétele (pl. "Mad Dog" -> "Mad+Dog")
    safe_title = urllib.parse.quote_plus(title)
    
    # A Comix.to hivatalos kereső URL-je
    search_url = f"https://comix.to/browse?q={safe_title}&sort=relevance%3Adesc"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        # 2. Rákeresünk a mangára a weboldalon
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 3. Kikeressük az initial-data JSON blokkot a letöltött HTML-ből
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='initial-data')
        
        if script_tag and script_tag.string:
            data = json.loads(script_tag.string)
            queries = data.get("queries", {})
            
            print(safe_title, script_tag)
            
            # 4. Végigpásztázzuk a JSON objektumokat a találatokért
            for key, value_obj in queries.items():
                
                print(key, value_obj)
                
                # A keresési eredmények mindig egy "items" listában jönnek vissza
                if isinstance(value_obj, dict) and "items" in value_obj:
                    items = value_obj["items"]
                    
                    if isinstance(items, list) and len(items) > 0:
                        # Vesszük a legelső (legrelevánsabb) találatot
                        first_result = items[0]
                        
                        print(f"{first_result}, {first_result["latestChapter"]}")
                        # 5. Ellenőrizzük, hogy ez tényleg manga adat-e, és megvan-e a latestChapter
                        if "latestChapter" in first_result and "title" in first_result:
                            # A float() azért kell, mert néha tizedestörttel (pl. 14.5) jön a fejezet, amit egésszé alakítunk
                            return int(float(first_result["latestChapter"]))
                            
        return 0
        
    except Exception as e:
        print(f"Hiba a Comix keresés során: {e}")
        return None
