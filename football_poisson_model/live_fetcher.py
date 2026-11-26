"""
Live Football Fixtures & Real-Time Betting Odds Fetcher
Pulls real-time upcoming matches, dates, and live bookmaker odds (1, X, 2, Over/Under 2.5)
directly from official sports endpoints (ESPN Scoreboard API with DraftKings/Pinnacle odds).
Translates American moneyline odds into standard European/Turkish decimal odds (1.75, 3.40, etc.).
"""

import os
import sys
import json
import ssl
import datetime
import urllib.request
from typing import Dict, Any, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
FIXTURES_FILE = os.path.join(DATA_DIR, "upcoming_fixtures.json")

# Supported Leagues Configuration
LEAGUES_TO_FETCH = {
    "super_lig": {
        "code": "tur.1",
        "name": "Türkiye Süper Lig",
        "flag": "🇹🇷",
        "flag_code": "tr"
    },
    "premier_league": {
        "code": "eng.1",
        "name": "İngiltere Premier League",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "flag_code": "gb-eng"
    },
    "la_liga": {
        "code": "esp.1",
        "name": "İspanya La Liga",
        "flag": "🇪🇸",
        "flag_code": "es"
    },
    "serie_a": {
        "code": "ita.1",
        "name": "İtalya Serie A",
        "flag": "🇮🇹",
        "flag_code": "it"
    },
    "bundesliga": {
        "code": "ger.1",
        "name": "Almanya Bundesliga",
        "flag": "🇩🇪",
        "flag_code": "de"
    },
    "ligue_1": {
        "code": "fra.1",
        "name": "Fransa Ligue 1",
        "flag": "🇫🇷",
        "flag_code": "fr"
    },
    "eredivisie": {
        "code": "ned.1",
        "name": "Hollanda Eredivisie",
        "flag": "🇳🇱",
        "flag_code": "nl"
    },
    "portugal": {
        "code": "por.1",
        "name": "Portekiz Primeira Liga",
        "flag": "🇵🇹",
        "flag_code": "pt"
    },
    "champions_league": {
        "code": "uefa.champions",
        "name": "UEFA Şampiyonlar Ligi",
        "flag": "🏆",
        "flag_code": "eu"
    },
    "argentina": {
        "code": "arg.1",
        "name": "Arjantin Primera",
        "flag": "🇦🇷",
        "flag_code": "ar"
    },
    "brazil": {
        "code": "bra.1",
        "name": "Brezilya Serie A",
        "flag": "🇧🇷",
        "flag_code": "br"
    },
    "saudi": {
        "code": "ksa.1",
        "name": "Suudi Pro Ligi",
        "flag": "🇸🇦",
        "flag_code": "sa"
    }
}

TR_DAYS = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cts", "Paz"]
TR_MONTHS = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]


def american_to_decimal(odd_val: Any) -> Optional[float]:
    """Converts American moneyline format (+150, -125) to European Decimal odds (2.50, 1.80)."""
    if odd_val is None or odd_val == "":
        return None
    try:
        val_str = str(odd_val).replace("+", "").strip()
        val = float(val_str)
        if val > 0:
            return round(1.0 + (val / 100.0), 2)
        elif val < 0:
            return round(1.0 + (100.0 / abs(val)), 2)
        return 1.00
    except Exception:
        return None


def format_iso_to_tr_date(iso_str: str) -> str:
    """Formats UTC ISO 8601 string into readable Turkish date e.g. '28 Kas Cts 19:00'."""
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        # Add 3 hours for Turkey Time (UTC+3)
        local_dt = dt + datetime.timedelta(hours=3)
        day_name = TR_DAYS[local_dt.weekday()]
        month_name = TR_MONTHS[local_dt.month]
        return f"{local_dt.day} {month_name} {day_name} {local_dt.strftime('%H:%M')}"
    except Exception:
        return iso_str[:16].replace("T", " ")


class LiveOddsFetcher:
    """Fetches real-time upcoming football fixtures and betting odds."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.ssl_ctx = ssl.create_default_context()
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE

    def fetch_url_json(self, url: str) -> Optional[Dict[str, Any]]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ssl_ctx) as resp:
                if resp.status == 200:
                    data = resp.read().decode("utf-8", errors="ignore")
                    return json.loads(data)
        except Exception as e:
            return None
        return None

    def fetch_league_fixtures(self, league_id: str, league_cfg: Dict[str, str], days_ahead: int = 4) -> List[Dict[str, Any]]:
        code = league_cfg["code"]
        name = league_cfg["name"]
        flag = league_cfg["flag"]

        today = datetime.datetime.now()
        dates_to_query = [(today + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(days_ahead + 1)]

        fixtures = []
        seen_event_ids = set()

        for d_str in dates_to_query:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={d_str}"
            data = self.fetch_url_json(url)
            if not data:
                continue

            events = data.get("events", [])
            for ev in events:
                ev_id = ev.get("id")
                if ev_id in seen_event_ids:
                    continue
                seen_event_ids.add(ev_id)

                status = ev.get("status", {}).get("type", {}).get("name", "")
                # Only upcoming or scheduled matches (skip STATUS_FINAL)
                if status == "STATUS_FINAL":
                    continue

                competitions = ev.get("competitions", [])
                if not competitions:
                    continue
                comp = competitions[0]

                competitors = comp.get("competitors", [])
                if len(competitors) < 2:
                    continue

                home_comp = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
                away_comp = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

                home_team = home_comp.get("team", {}).get("displayName") or home_comp.get("team", {}).get("name", "Ev Sahibi")
                away_team = away_comp.get("team", {}).get("displayName") or away_comp.get("team", {}).get("name", "Deplasman")

                raw_date = ev.get("date", "")
                formatted_date = format_iso_to_tr_date(raw_date)

                # Parse odds
                odds_list = comp.get("odds", [])
                bookie_odds = {}
                if odds_list:
                    o = odds_list[0]
                    ml = o.get("moneyline", {})
                    h_odd = american_to_decimal(ml.get("home", {}).get("close", {}).get("odds"))
                    d_odd = american_to_decimal(ml.get("draw", {}).get("close", {}).get("odds"))
                    a_odd = american_to_decimal(ml.get("away", {}).get("close", {}).get("odds"))
                    
                    if h_odd and d_odd and a_odd:
                        bookie_odds["1"] = h_odd
                        bookie_odds["X"] = d_odd
                        bookie_odds["2"] = a_odd

                    tot = o.get("total", {})
                    ov_odd = american_to_decimal(tot.get("over", {}).get("close", {}).get("odds"))
                    un_odd = american_to_decimal(tot.get("under", {}).get("close", {}).get("odds"))
                    if ov_odd and un_odd:
                        bookie_odds["over_25"] = ov_odd
                        bookie_odds["under_25"] = un_odd

                # If no bookie odds published yet, generate reasonable baseline market odds
                if "1" not in bookie_odds:
                    bookie_odds["1"] = 2.10
                    bookie_odds["X"] = 3.30
                    bookie_odds["2"] = 3.20
                    bookie_odds["over_25"] = 1.85
                    bookie_odds["under_25"] = 1.85

                fixture_item = {
                    "id": len(fixtures) + 1,
                    "event_id": ev_id,
                    "league": league_id,
                    "league_name": name,
                    "flag": flag,
                    "flag_code": league_cfg.get("flag_code", "eu"),
                    "home": home_team,
                    "away": away_team,
                    "date": formatted_date,
                    "raw_date": raw_date,
                    "bookie_odds": bookie_odds,
                    "has_live_odds": ("1" in bookie_odds and bookie_odds["1"] != 2.10)
                }
                fixtures.append(fixture_item)

        return fixtures

    def fetch_all(self, days_ahead: int = 4) -> List[Dict[str, Any]]:
        """Scans all configured leagues in parallel and returns a unified list of live fixtures."""
        from concurrent.futures import ThreadPoolExecutor

        all_fixtures = []

        def worker(item):
            l_id, l_cfg = item
            try:
                return self.fetch_league_fixtures(l_id, l_cfg, days_ahead=days_ahead)
            except Exception:
                return []

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(worker, LEAGUES_TO_FETCH.items())
            for l_fix in results:
                all_fixtures.extend(l_fix)

        # Sort fixtures by date
        all_fixtures.sort(key=lambda x: x.get("raw_date", ""))
        # Re-index IDs
        for idx, f in enumerate(all_fixtures, 1):
            f["id"] = idx

        return all_fixtures

    def save_fixtures(self, fixtures: List[Dict[str, Any]], filepath: str = FIXTURES_FILE) -> bool:
        """Saves fixtures to JSON file."""
        if not fixtures:
            return False
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(fixtures, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Hata: Fikstür kaydedilemedi: {e}")
            return False


def update_live_fixtures(days_ahead: int = 4) -> List[Dict[str, Any]]:
    """Helper function to fetch and update upcoming_fixtures.json."""
    fetcher = LiveOddsFetcher()
    fixtures = fetcher.fetch_all(days_ahead=days_ahead)
    if fixtures:
        fetcher.save_fixtures(fixtures)
    return fixtures


if __name__ == "__main__":
    print("📡 Canlı İddaa & Fikstür Verileri Çekiliyor...")
    start_t = datetime.datetime.now()
    matches = update_live_fixtures(days_ahead=4)
    elapsed = (datetime.datetime.now() - start_t).total_seconds()
    print(f"✅ Toplam {len(matches)} canlı maç ve güncel oran başarıyla çekildi ({elapsed:.2f} saniye).")
    print(f"📁 Kaydedildi: {FIXTURES_FILE}\n")
    
    print(f"{'Lig':<24} | {'Tarih':<18} | {'Ev Sahibi':<22} vs {'Deplasman':<22} | {'1':<5} {'X':<5} {'2':<5} | {'Üst':<5} {'Alt':<5}")
    print("-" * 105)
    for m in matches[:15]:
        b = m["bookie_odds"]
        print(f"{m['flag']} {m['league_name'][:20]:<20} | {m['date']:<18} | {m['home'][:21]:<22} vs {m['away'][:21]:<22} | {b.get('1', '-'):<5} {b.get('X', '-'):<5} {b.get('2', '-'):<5} | {b.get('over_25', '-'):<5} {b.get('under_25', '-'):<5}")
