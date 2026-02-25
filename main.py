import os
import requests
import time
from datetime import datetime

# --- KONFIGURÁCIÓ (GitHub Secrets-ből jön) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

def send_telegram(message):
    """Üzenet küldése a Telegram botnak."""
    if not BOT_TOKEN or not CHAT_ID:
        print("Hiba: Hiányzó Telegram Secret adatok!")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram hiba: {e}")

def get_live_matches():
    """Lekéri az élő E-football meccseket a BetsAPI-ról."""
    if not RAPID_API_KEY:
        print("Hiba: Nincs RAPID_API_KEY beállítva!")
        return []

    url = "https://betsapi2.p.rapidapi.com/v1/events/inplay"
    # Sport_id 1 a foci, ezen belül a ligákat az API válaszból szűrjük
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "betsapi2.p.rapidapi.com"
    }
    params = {"sport_id": "1"} 

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"API hiba a lekérdezésnél: {e}")
        return []

def calculate_kelly_stake(my_prob, odds):
    """Kelly-kritérium alapú tétméretezés (10% fractional)."""
    if odds <= 1: return 0
    b = odds - 1
    p = my_prob
    q = 1 - p
    kelly_f = (p * b - q) / b
    # Skálázás 0-10 egységre, 0.1-es biztonsági szorzóval
    stake = max(0, kelly_f * 0.1 * 100)
    return round(stake, 1)

def run_agent():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Elemzés indul...")
    
    matches = get_live_matches()
    
    # E-soccer ligák szűrése (a név alapján keressük az e-sport meccseket)
    for match in matches:
        league_name = match.get("league", {}).get("name", "").lower()
        
        # Csak azokat a meccseket nézzük, amik e-sportok (pl. "Esoccer", "GT Leagues")
        if "esoccer" in league_name or "gt leagues" in league_name:
            home = match.get("home", {}).get("name")
            away = match.get("away", {}).get("name")
            
            # FIGYELEM: Az élő oddsokat gyak
