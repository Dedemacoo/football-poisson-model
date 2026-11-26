"""
Multi-League CLI Runner for Poisson & Dixon-Coles Football Match Prediction Model
Supports 13 World Leagues:
Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Süper Lig,
Eredivisie, Portugal, Argentina, Brazil, Saudi Pro, Iran, Champions League.
"""

import os
import sys
from typing import Optional, List
from tabulate import tabulate

from data_loader import DataLoader
from model import FootballPoissonModel

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

LEAGUES = {
    "premier_league": {
        "name": "İngiltere Premier League",
        "file": os.path.join(DATA_DIR, "premier_league.csv"),
        "derby": ("Manchester City", "Liverpool")
    },
    "la_liga": {
        "name": "İspanya La Liga",
        "file": os.path.join(DATA_DIR, "la_liga.csv"),
        "derby": ("Real Madrid", "Barcelona")
    },
    "serie_a": {
        "name": "İtalya Serie A",
        "file": os.path.join(DATA_DIR, "serie_a.csv"),
        "derby": ("Inter", "AC Milan")
    },
    "bundesliga": {
        "name": "Almanya Bundesliga",
        "file": os.path.join(DATA_DIR, "bundesliga.csv"),
        "derby": ("Bayern Munich", "Bayer Leverkusen")
    },
    "ligue_1": {
        "name": "Fransa Ligue 1",
        "file": os.path.join(DATA_DIR, "ligue_1.csv"),
        "derby": ("PSG", "Marseille")
    },
    "super_lig": {
        "name": "Türkiye Süper Lig",
        "file": os.path.join(DATA_DIR, "super_lig.csv"),
        "derby": ("Galatasaray", "Fenerbahce")
    },
    "eredivisie": {
        "name": "Hollanda Eredivisie",
        "file": os.path.join(DATA_DIR, "eredivisie.csv"),
        "derby": ("PSV", "Ajax")
    },
    "portugal": {
        "name": "Portekiz Primeira Liga",
        "file": os.path.join(DATA_DIR, "portugal.csv"),
        "derby": ("Sporting CP", "Benfica")
    },
    "argentina": {
        "name": "Arjantin Primera División",
        "file": os.path.join(DATA_DIR, "argentina.csv"),
        "derby": ("River Plate", "Boca Juniors")
    },
    "brazil": {
        "name": "Brezilya Serie A",
        "file": os.path.join(DATA_DIR, "brazil.csv"),
        "derby": ("Flamengo", "Palmeiras")
    },
    "saudi": {
        "name": "Suudi Pro Ligi",
        "file": os.path.join(DATA_DIR, "saudi.csv"),
        "derby": ("Al Hilal", "Al Nassr")
    },
    "iran": {
        "name": "İran Pro Ligi",
        "file": os.path.join(DATA_DIR, "iran.csv"),
        "derby": ("Persepolis", "Esteghlal")
    },
    "champions_league": {
        "name": "UEFA Şampiyonlar Ligi",
        "file": os.path.join(DATA_DIR, "champions_league.csv"),
        "derby": ("Real Madrid", "Manchester City")
    }
}


def format_header(title: str, width: int = 70) -> str:
    line = "=" * width
    return f"\n{line}\n  {title.center(width - 4)}\n{line}"


def format_sub_header(title: str, width: int = 70) -> str:
    line = "-" * width
    return f"\n{line}\n  {title}\n{line}"


def print_score_matrix(matrix: List[List[float]], home_team: str, away_team: str, max_goals: int = 5):
    header = [f"Dep: {away_team[:10]}"] + [f"{j} Gol" for j in range(max_goals + 1)]
    table_data = []
    for i in range(max_goals + 1):
        row = [f"Ev: {home_team[:10]} {i} Gol"]
        for j in range(max_goals + 1):
            val = matrix[i][j] * 100
            row.append(f"{val:.2f}%")
        table_data.append(row)
    print(tabulate(table_data, headers=header, tablefmt="fancy_grid", stralign="center"))


def display_match_prediction(result: dict):
    home = result["home_team"]
    away = result["away_team"]

    print(format_header(f"MAÇ ANALİZİ: {home.upper()} vs {away.upper()}"))

    xg_data = [
        ["Takım", "Rol", "Beklenen Gol (Lambda / xG)"],
        [home, "Ev Sahibi", f"{result['lambda_home']:.2f}"],
        [away, "Deplasman", f"{result['lambda_away']:.2f}"],
        ["TOPLAM", "Karşılaşma", f"{result['expected_total_goals']:.2f} Gol"],
    ]
    print(tabulate(xg_data, headers="firstrow", tablefmt="rounded_grid"))

    p1x2 = result["probabilities_1x2"]
    f1x2 = result["fair_odds_1x2"]
    outcomes_data = [
        ["Seçenek", "Olasılık (%)", "Model Adil Oranı (Fair Odds)"],
        [f"1 ({home} Galibiyeti)", f"{p1x2['HomeWin']:.2f}%", f"{f1x2['1']:.2f}"],
        ["X (Beraberlik)", f"{p1x2['Draw']:.2f}%", f"{f1x2['X']:.2f}"],
        [f"2 ({away} Galibiyeti)", f"{p1x2['AwayWin']:.2f}%", f"{f1x2['2']:.2f}"],
    ]
    print(format_sub_header("1. MAÇ SONUCU (1X2) İSTATİSTİKLERİ VE ADİL ORANLAR"))
    print(tabulate(outcomes_data, headers="firstrow", tablefmt="rounded_grid", numalign="center"))

    top5 = result["top_5_scores"]
    top5_data = [["Sıra", "Skor", "Olasılık (%)", "Model Adil Oranı"]]
    for idx, item in enumerate(top5, 1):
        top5_data.append([
            f"#{idx}",
            item["score"],
            f"{item['percentage']:.2f}%",
            f"{item['fair_odds']:.2f}"
        ])
    print(format_sub_header("2. EN OLASI İLK 5 SKOR TAHMİNİ"))
    print(tabulate(top5_data, headers="firstrow", tablefmt="rounded_grid", numalign="center"))

    ou = result["over_under_2_5"]
    btts = result["btts"]
    goals_data = [
        ["Piyasa", "Tahmin / Seçenek", "Olasılık (%)", "Model Adil Oranı"],
        ["2.5 Gol", "2.5 ALT", f"{ou['under_prob_pct']:.2f}%", f"{ou['fair_odds_under']:.2f}"],
        ["2.5 Gol", "2.5 ÜST", f"{ou['over_prob_pct']:.2f}%", f"{ou['fair_odds_over']:.2f}"],
        ["Karşılıklı Gol (KG)", "KG VAR", f"{btts['yes_prob_pct']:.2f}%", f"{btts['fair_odds_yes']:.2f}"],
        ["Karşılıklı Gol (KG)", "KG YOK", f"{btts['no_prob_pct']:.2f}%", f"{btts['fair_odds_no']:.2f}"],
    ]
    print(format_sub_header("3. 2.5 GOL ALT/ÜST VE KARŞILIKLI GOL (KG) ORANLARI"))
    print(tabulate(goals_data, headers="firstrow", tablefmt="rounded_grid", numalign="center"))

    print(format_sub_header("4. 6x6 SKOR OLASILIK MATRİSİ (Poisson / Dixon-Coles Dağılımı)"))
    print_score_matrix(result["matrix"], home, away, max_goals=result["max_goals"])


def analyze_league(league_key: str):
    info = LEAGUES[league_key]
    print(format_header(f"LİG: {info['name'].upper()}"))
    df = DataLoader.load(info["file"])
    summary = DataLoader.get_summary_stats(df)

    print(f"[*] Toplam Maç: {summary['total_matches']} | Takım Sayısı: {summary['unique_teams_count']}")
    print(f"[*] Ev Gol Ort: {summary['avg_home_goals']:.2f} | Dep Gol Ort: {summary['avg_away_goals']:.2f} | Toplam Gol Ort: {summary['avg_total_goals']:.2f}")

    model = FootballPoissonModel(default_rho=-0.08)
    model.fit(df)

    print("\n" + format_sub_header("TAKIM GÜÇ KATSAYILARI (HÜCUM & SAVUNMA İNDEKSLERİ)"))
    ratings = model.get_team_ratings_rows()
    print(tabulate(ratings[:8], headers="keys", tablefmt="rounded_grid"))

    h_team, a_team = info["derby"]
    pred = model.predict_match(h_team, a_team, max_goals=5)
    display_match_prediction(pred)


def main():
    print(format_header("GLOBAL FUTBOL POISSON & DIXON-COLES TAHMİN SİSTEMİ"))
    print("Mevcut 13 Dünya Ligi:")
    for idx, (k, v) in enumerate(LEAGUES.items(), 1):
        print(f"  {idx:2d}. {v['name']} ({k})")

    target_league = "iran"
    if len(sys.argv) > 1:
        arg = sys.argv[1].replace("--league=", "").strip()
        if arg in LEAGUES:
            target_league = arg

    print(f"\n[*] İncelenen Lig: {LEAGUES[target_league]['name']}")
    analyze_league(target_league)

    print("\n" + "=" * 70)
    print("  Görsel arayüz ve Kupon Analizörü için: python dashboard.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
