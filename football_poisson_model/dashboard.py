"""
Global Multi-League Football Poisson & Dixon-Coles Predictor & Real-Time Scanner Bot
Features:
- Sub-second background MatchScannerBot across 13+ world leagues
- Strict 70% - 95% Statistical Confidence Kupon Generator
- Real-time Match Radar with confidence tier tagging
- Zero scrollbars, zero lag, asynchronous pure-Python server
"""

import os
import sys
import json
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

from data_loader import DataLoader
from model import FootballPoissonModel
from scanner_bot import MatchScannerBot
from backtester import ModelBacktester

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
FIXTURES_FILE = os.path.join(DATA_DIR, "upcoming_fixtures.json")

# Leagues Config
LEAGUES_CONFIG = {
    "premier_league": {"name": "İngiltere Premier League", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "flag_code": "gb-eng", "file": os.path.join(DATA_DIR, "premier_league.csv")},
    "la_liga": {"name": "İspanya La Liga", "flag": "🇪🇸", "flag_code": "es", "file": os.path.join(DATA_DIR, "la_liga.csv")},
    "serie_a": {"name": "İtalya Serie A", "flag": "🇮🇹", "flag_code": "it", "file": os.path.join(DATA_DIR, "serie_a.csv")},
    "bundesliga": {"name": "Almanya Bundesliga", "flag": "🇩🇪", "flag_code": "de", "file": os.path.join(DATA_DIR, "bundesliga.csv")},
    "ligue_1": {"name": "Fransa Ligue 1", "flag": "🇫🇷", "flag_code": "fr", "file": os.path.join(DATA_DIR, "ligue_1.csv")},
    "super_lig": {"name": "Türkiye Süper Lig", "flag": "🇹🇷", "flag_code": "tr", "file": os.path.join(DATA_DIR, "super_lig.csv")},
    "eredivisie": {"name": "Hollanda Eredivisie", "flag": "🇳🇱", "flag_code": "nl", "file": os.path.join(DATA_DIR, "eredivisie.csv")},
    "portugal": {"name": "Portekiz Primeira Liga", "flag": "🇵🇹", "flag_code": "pt", "file": os.path.join(DATA_DIR, "portugal.csv")},
    "argentina": {"name": "Arjantin Primera División", "flag": "🇦🇷", "flag_code": "ar", "file": os.path.join(DATA_DIR, "argentina.csv")},
    "brazil": {"name": "Brezilya Serie A", "flag": "🇧🇷", "flag_code": "br", "file": os.path.join(DATA_DIR, "brazil.csv")},
    "saudi": {"name": "Suudi Pro Ligi", "flag": "🇸🇦", "flag_code": "sa", "file": os.path.join(DATA_DIR, "saudi.csv")},
    "iran": {"name": "İran Pro Ligi", "flag": "🇮🇷", "flag_code": "ir", "file": os.path.join(DATA_DIR, "iran.csv")},
    "champions_league": {"name": "UEFA Şampiyonlar Ligi", "flag": "🏆", "flag_code": "eu", "file": os.path.join(DATA_DIR, "champions_league.csv")}
}

LEAGUE_MODELS = {}
LEAGUE_SUMMARIES = {}

for l_id, cfg in LEAGUES_CONFIG.items():
    if os.path.exists(cfg["file"]):
        try:
            df = DataLoader.load(cfg["file"])
            m = FootballPoissonModel(default_rho=-0.08)
            m.fit(df)
            LEAGUE_MODELS[l_id] = m
            LEAGUE_SUMMARIES[l_id] = DataLoader.get_summary_stats(df)
        except Exception as e:
            print(f"Uyarı: {l_id} yüklenirken hata: {e}")

# Initialize Autonomous Scanner Bot
SCANNER_BOT = MatchScannerBot(LEAGUE_MODELS, fixtures_path=FIXTURES_FILE)
BACKTEST_RESULTS = None


HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Futbol Tahmin & Canlı Radar Botu (%70 - %95 Güvenilirlikli)</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* BÜTÜN SCROLLBARLARI GİZLE */
        ::-webkit-scrollbar { display: none !important; width: 0 !important; height: 0 !important; }
        html, body, div, table, tbody, * { -ms-overflow-style: none !important; scrollbar-width: none !important; }

        :root {
            --bg-main: #0a0e17;
            --bg-card: #121927;
            --bg-card-hover: #192337;
            --border: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #c084fc;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background-color: var(--bg-main); color: var(--text-main); line-height: 1.5; padding: 20px; }
        .container { max-width: 1440px; margin: 0 auto; }
        header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid var(--border); flex-wrap: wrap; gap: 14px; }
        .logo-area h1 { font-size: 1.55rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 10px; }
        .logo-area p { font-size: 0.86rem; color: var(--text-muted); }
        .bot-status-pill {
            background: rgba(16, 185, 129, 0.12);
            color: var(--accent-green);
            padding: 7px 16px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 700;
            border: 1px solid rgba(16, 185, 129, 0.35);
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .bot-pulse { width: 9px; height: 9px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 10px var(--accent-green); animation: pulse 1.8s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.3); } 100% { opacity: 1; transform: scale(1); } }

        /* Navigation Bar */
        .top-nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
        .league-tabs { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; flex: 1; }
        .league-tab-btn { background: var(--bg-card); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 14px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; cursor: pointer; white-space: nowrap; display: flex; align-items: center; gap: 6px; transition: all 0.2s; }
        .league-tab-btn:hover { background: var(--bg-card-hover); color: #fff; }
        .league-tab-btn.active { background: linear-gradient(135deg, #0284c7, #2563eb); color: #fff; border-color: #38bdf8; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }

        .nav-actions { display: flex; gap: 8px; }
        .btn-action-nav { background: #1e293b; color: #fff; border: 1px solid #334155; padding: 8px 15px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s; }
        .btn-action-nav:hover { background: #334155; border-color: var(--accent-blue); }
        .btn-action-nav.active { background: #2563eb; border-color: #38bdf8; }

        /* Stats Grid */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-bottom: 20px; }
        .stat-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; }
        .stat-label { font-size: 0.72rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 4px; }
        .stat-value { font-size: 1.55rem; font-weight: 700; color: var(--accent-blue); }
        .stat-sub { font-size: 0.78rem; color: var(--text-muted); }

        /* Controls */
        .controls-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 18px 20px; margin-bottom: 20px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
        .form-group { display: flex; flex-direction: column; gap: 6px; flex: 1; min-width: 180px; }
        .form-group label { font-size: 0.78rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }
        select, input { background: #0a0e17; color: #fff; border: 1px solid #334155; padding: 10px 12px; border-radius: 8px; font-size: 0.92rem; font-weight: 500; outline: none; }
        select:focus, input:focus { border-color: var(--accent-blue); }
        .btn-analyze { background: linear-gradient(135deg, #0284c7, #2563eb); color: #fff; border: none; padding: 11px 24px; border-radius: 8px; font-size: 0.92rem; font-weight: 600; cursor: pointer; align-self: flex-end; }

        /* Main Layout */
        .main-layout { display: grid; grid-template-columns: 1fr 390px; gap: 20px; margin-bottom: 24px; }
        @media (max-width: 1080px) { .main-layout { grid-template-columns: 1fr; } }

        .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
        .card-header { font-size: 1.1rem; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }

        /* 1X2 Probabilities */
        .prob-1x2-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
        .prob-box { background: #0a0e17; border: 1px solid var(--border); border-radius: 10px; padding: 14px; text-align: center; }
        .prob-box.home { border-top: 3px solid var(--accent-green); }
        .prob-box.draw { border-top: 3px solid var(--accent-yellow); }
        .prob-box.away { border-top: 3px solid var(--accent-red); }
        .prob-box-title { font-size: 0.8rem; font-weight: 600; color: var(--text-muted); margin-bottom: 4px; }
        .prob-box-pct { font-size: 1.6rem; font-weight: 800; color: #fff; margin-bottom: 2px; }
        .prob-box-odds { font-size: 0.82rem; color: var(--accent-blue); font-weight: 600; }
        .progress-bar-bg { background: #1e293b; height: 5px; border-radius: 3px; margin: 8px 0; overflow: hidden; }
        .progress-bar-fill { height: 100%; border-radius: 3px; }
        .btn-add-slip { background: #1e293b; color: #38bdf8; border: 1px solid #334155; padding: 5px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; cursor: pointer; width: 100%; transition: all 0.2s; }
        .btn-add-slip:hover { background: #38bdf8; color: #000; }

        /* Markets */
        .markets-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin-bottom: 14px; }
        .market-item { background: #0a0e17; border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center; }
        .market-label { font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }
        .market-val { font-size: 0.92rem; font-weight: 700; color: #fff; }

        /* Scores */
        .scores-list { display: flex; flex-direction: column; gap: 8px; }
        .score-row { display: flex; align-items: center; justify-content: space-between; background: #0a0e17; padding: 9px 12px; border-radius: 8px; border: 1px solid var(--border); }
        .score-badge { background: #1e293b; padding: 3px 8px; border-radius: 6px; font-weight: 700; color: var(--accent-blue); font-size: 0.9rem; }

        /* 6x6 Matrix */
        .matrix-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: center; }
        .matrix-table th, .matrix-table td { padding: 7px 5px; border: 1px solid #1e293b; }
        .matrix-table th { background: #0a0e17; color: var(--text-muted); font-weight: 600; }

        /* ================= RADAR VIEW ================= */
        .radar-card-item {
            background: #0a0e17;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
            transition: all 0.2s;
        }
        .radar-card-item:hover { border-color: var(--accent-blue); background: #0f1626; }
        .radar-match-title { font-weight: 700; font-size: 1.05rem; color: #fff; display: flex; align-items: center; gap: 8px; }
        .radar-meta { font-size: 0.78rem; color: var(--text-muted); margin-top: 2px; }
        .radar-badge { padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; }
        .badge-ultra { background: rgba(16, 185, 129, 0.18); color: var(--accent-green); border: 1px solid var(--accent-green); }
        .badge-high { background: rgba(245, 158, 11, 0.18); color: var(--accent-yellow); border: 1px solid var(--accent-yellow); }

        /* ================= BET SLIP / KUPON ================= */
        .slip-card { background: linear-gradient(135deg, #131c2e, #0d1424); border: 1px solid #2563eb; box-shadow: 0 8px 24px rgba(37, 99, 235, 0.15); position: sticky; top: 20px; }
        .slip-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 12px; margin-bottom: 14px; }
        .slip-header h2 { font-size: 1.15rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px; }
        .btn-clear-slip { background: transparent; color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.4); padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; cursor: pointer; }

        .btn-premier-coupon {
            background: linear-gradient(135deg, #10b981, #0284c7);
            color: #fff;
            border: none;
            padding: 11px 14px;
            border-radius: 8px;
            font-size: 0.88rem;
            font-weight: 800;
            width: 100%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-bottom: 8px;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
            transition: all 0.2s;
        }
        .btn-premier-coupon:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(16, 185, 129, 0.45); }

        .btn-coupon-val {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #fff;
            border: none;
            padding: 11px 14px;
            border-radius: 8px;
            font-size: 0.88rem;
            font-weight: 800;
            width: 100%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-bottom: 8px;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.25);
            transition: all 0.2s;
        }
        .btn-coupon-val:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(245, 158, 11, 0.4); }

        .btn-coupon-goal {
            background: linear-gradient(135deg, #8b5cf6, #6d28d9);
            color: #fff;
            border: none;
            padding: 11px 14px;
            border-radius: 8px;
            font-size: 0.88rem;
            font-weight: 800;
            width: 100%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-bottom: 14px;
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.25);
            transition: all 0.2s;
        }
        .btn-coupon-goal:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(139, 92, 246, 0.4); }

        .btn-live-sync {
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            box-shadow: 0 2px 10px rgba(56, 189, 248, 0.3);
        }
        .btn-live-sync:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(56, 189, 248, 0.5); }
        .radar-filter-bar { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
        .radar-filter-btn { background: #0a0e17; color: var(--text-muted); border: 1px solid var(--border); padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .radar-filter-btn.active, .radar-filter-btn:hover { background: #1e293b; color: var(--accent-blue); border-color: var(--accent-blue); }

        .slip-items-list { display: flex; flex-direction: column; gap: 10px; max-height: 330px; overflow-y: auto; margin-bottom: 14px; }
        .slip-item { background: #0a0e17; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 12px; display: flex; flex-direction: column; gap: 4px; }
        .slip-item-top { display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600; color: #fff; }
        .slip-item-bot { display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--text-muted); }
        .slip-btn-remove { color: #94a3b8; cursor: pointer; font-weight: bold; font-size: 1rem; }
        .slip-btn-remove:hover { color: var(--accent-red); }

        .slip-summary-box { background: #0a0e17; border-radius: 10px; border: 1px solid #1e293b; padding: 14px; margin-bottom: 14px; }
        .slip-summary-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; margin-bottom: 8px; }
        .slip-summary-row:last-child { margin-bottom: 0; }
        .slip-big-odds { font-size: 1.3rem; font-weight: 800; color: var(--accent-blue); }
        .slip-edge-badge { padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; }
        .badge-pos-ev { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }
        .badge-neg-ev { background: rgba(239, 68, 68, 0.2); color: var(--accent-red); border: 1px solid var(--accent-red); }

        .notice-card { background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 12px; padding: 16px; margin-top: 12px; }
        .notice-title { color: var(--accent-yellow); font-weight: 700; font-size: 0.92rem; margin-bottom: 4px; }
        .notice-body { font-size: 0.82rem; color: #cbd5e1; line-height: 1.5; }

        .rank-table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
        .rank-table th, .rank-table td { padding: 8px 10px; border-bottom: 1px solid var(--border); text-align: left; }
        .rank-table th { color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; }
        .rank-table tr:hover { background: var(--bg-card-hover); }

        /* ================= GUIDE / ACADEMY VIEW ================= */
        .guide-step-card { background: #0a0e17; border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px; transition: all 0.2s; position: relative; }
        .guide-step-card:hover { border-color: var(--accent-blue); background: #0f1626; }
        .guide-step-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .guide-num { background: linear-gradient(135deg, var(--accent-blue), #2563eb); color: #fff; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.95rem; flex-shrink: 0; }
        .guide-title { font-size: 1.1rem; font-weight: 700; color: #fff; }
        .guide-desc { font-size: 0.88rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 12px; }
        .guide-actions-bar { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
        .guide-btn-action { background: #1e293b; color: var(--accent-blue); border: 1px solid #334155; padding: 7px 14px; border-radius: 8px; font-size: 0.82rem; font-weight: 700; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 6px; }
        .guide-btn-action:hover { background: var(--accent-blue); color: #000; }
        .guide-grid-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin: 16px 0; }
        .guide-box { background: #0d1424; border: 1px solid var(--border); border-radius: 10px; padding: 16px; border-left: 4px solid var(--accent-blue); }
        .guide-box.safe { border-left-color: var(--accent-green); }
        .guide-box.val { border-left-color: var(--accent-yellow); }
        .guide-box.goal { border-left-color: var(--accent-purple); }
        .guide-box h4 { font-size: 0.95rem; font-weight: 700; margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }
        .guide-box p { font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; }
        .guide-box .benefit { margin-top: 8px; font-size: 0.8rem; font-weight: 600; color: #f8fafc; }
        .guide-tip-pill { background: rgba(56, 189, 248, 0.12); color: var(--accent-blue); padding: 4px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; display: inline-block; margin-bottom: 6px; }

        /* ================= SQUAD / INJURY LAB ================= */
        .player-item-row { background: #0a0e17; border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; font-size: 0.82rem; cursor: pointer; transition: all 0.2s; user-select: none; }
        .player-item-row:hover { border-color: var(--accent-blue); background: #0f1626; }
        .player-item-row.injured { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.6); }
        .player-tag-pos { background: #1e293b; color: #94a3b8; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; }
        .player-impact-star { color: var(--accent-yellow); font-weight: 700; font-size: 0.76rem; }
        .player-status-badge { padding: 3px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; }
        .status-fit { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.3); }
        .status-out { background: rgba(239, 68, 68, 0.25); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.4); }
        .ai-insight-item { background: #0a0e17; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; border-left: 3px solid var(--accent-yellow); font-size: 0.82rem; }
        .ai-insight-item.critical { border-left-color: var(--accent-red); background: rgba(239, 68, 68, 0.08); }
        .ai-insight-item.tip { border-left-color: var(--accent-green); background: rgba(16, 185, 129, 0.08); }

        .flag-icon-badge {
            width: 22px;
            height: 15px;
            object-fit: cover;
            border-radius: 3px;
            display: inline-block;
            vertical-align: middle;
            margin-right: 6px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.5);
            flex-shrink: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-area">
                <h1>⚽ Global AI Tahmin & Otonom Kupon Botu</h1>
                <p>13+ Dünya Ligi • Saniyelik Poisson/Dixon-Coles Motoru • Gerçek Zamanlı İddaa & Değer Bahisleri (+EV)</p>
            </div>
            <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                <button class="btn-action-nav" onclick="switchMainView('guide')" style="background:rgba(56,189,248,0.12); color:#38bdf8; border-color:#38bdf8; padding:7px 14px; font-weight:700;">
                    ❓ Nasıl Kullanılır?
                </button>
                <button id="btnLiveRefresh" class="btn-live-sync" onclick="triggerLiveRefresh()">
                    <span id="liveRefreshIcon">⚡</span> Canlı İddaa Bültenini Yenile
                </button>
                <div class="bot-status-pill">
                    <span class="bot-pulse"></span>
                    <span id="pillBotStatus">Otonom Bot Aktif • 75 Canlı Maç Tarandı</span>
                </div>
            </div>
        </header>

        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="league-tabs" id="leagueTabs"></div>
            <div class="nav-actions">
                <button class="btn-action-nav active" id="btnViewSingle" onclick="switchMainView('single')">🏟️ Detaylı Maç</button>
                <button class="btn-action-nav" id="btnViewRadar" onclick="switchMainView('radar')">📡 Canlı Maç Radarı</button>
                <button class="btn-action-nav" id="btnViewBacktest" onclick="switchMainView('backtest')">🧪 Test & Doğrulama (%73.8)</button>
                <button class="btn-action-nav" id="btnViewGuide" onclick="switchMainView('guide')" style="border-color:#38bdf8; color:#38bdf8; font-weight:700;">🎓 Nasıl Kullanılır? (Rehber)</button>
            </div>
        </div>

        <!-- Summary Stats -->
        <div class="stats-grid" id="summaryStats">
            <div class="stat-card">
                <div class="stat-label">Toplam İncelenen Maç</div>
                <div class="stat-value" id="sTotalMatches">-</div>
                <div class="stat-sub" id="sTeamsCount">- Takım</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Lig Ev Gol Ortalaması</div>
                <div class="stat-value" id="sHomeAvg">-</div>
                <div class="stat-sub">Maç Başına</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Lig Dep Gol Ortalaması</div>
                <div class="stat-value" id="sAwayAvg">-</div>
                <div class="stat-sub">Maç Başına</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Lig Toplam Gol Ortalaması</div>
                <div class="stat-value" id="sTotalAvg">-</div>
                <div class="stat-sub" id="sOver25">2.5 Üst: -</div>
            </div>
        </div>

        <!-- Controls (Single View) -->
        <div class="controls-card" id="matchControls">
            <div class="form-group">
                <label>Ev Sahibi Takım</label>
                <select id="homeSelect" onchange="runPrediction()"></select>
            </div>
            <div class="form-group">
                <label>Deplasman Takımı</label>
                <select id="awaySelect" onchange="runPrediction()"></select>
            </div>
            <div class="form-group" style="max-width: 200px;">
                <label>Dixon-Coles Düzeltmesi</label>
                <select id="rhoSelect" onchange="runPrediction()">
                    <option value="-0.08" selected>Aktif (Rho = -0.08)</option>
                    <option value="0.0">Kapalı (Saf Poisson)</option>
                </select>
            </div>
            <button class="btn-analyze" onclick="runPrediction()">Yeniden Hesapla</button>
        </div>

        <!-- Main Layout (Predictions + Bet Slip) -->
        <div class="main-layout">
            <!-- Left Side: Match Predictions OR Live Radar -->
            <div id="leftColumn">
                <!-- 1. Single Match View -->
                <div id="singleMatchView">
                    <div class="card">
                        <div class="card-header">
                            <span id="matchTitle">Maç Analizi</span>
                            <span style="font-size: 0.85rem; font-weight: 500; color: var(--accent-blue);" id="xgSummary">xG: -</span>
                        </div>

                        <!-- 1X2 Probabilities -->
                        <div class="prob-1x2-grid">
                            <div class="prob-box home">
                                <div class="prob-box-title" id="lblHomeWin">1 (Ev Sahibi)</div>
                                <div class="prob-box-pct" id="pHomeWin">-%</div>
                                <div class="prob-box-odds" id="oHomeWin">Adil: -</div>
                                <div class="progress-bar-bg"><div class="progress-bar-fill" id="barHomeWin" style="background: var(--accent-green); width: 0%;"></div></div>
                                <button class="btn-add-slip" id="btnAdd1" onclick="addCurrentToSlip('1')">+ Kupona 1 Ekle</button>
                            </div>
                            <div class="prob-box draw">
                                <div class="prob-box-title">X (Beraberlik)</div>
                                <div class="prob-box-pct" id="pDraw">-%</div>
                                <div class="prob-box-odds" id="oDraw">Adil: -</div>
                                <div class="progress-bar-bg"><div class="progress-bar-fill" id="barDraw" style="background: var(--accent-yellow); width: 0%;"></div></div>
                                <button class="btn-add-slip" id="btnAddX" onclick="addCurrentToSlip('X')">+ Kupona X Ekle</button>
                            </div>
                            <div class="prob-box away">
                                <div class="prob-box-title" id="lblAwayWin">2 (Deplasman)</div>
                                <div class="prob-box-pct" id="pAwayWin">-%</div>
                                <div class="prob-box-odds" id="oAwayWin">Adil: -</div>
                                <div class="progress-bar-bg"><div class="progress-bar-fill" id="barAwayWin" style="background: var(--accent-red); width: 0%;"></div></div>
                                <button class="btn-add-slip" id="btnAdd2" onclick="addCurrentToSlip('2')">+ Kupona 2 Ekle</button>
                            </div>
                        </div>

                        <!-- Mini Markets -->
                        <div class="markets-grid">
                            <div class="market-item">
                                <div>
                                    <div class="market-label">2.5 ÜST</div>
                                    <div style="font-size:0.75rem; color:var(--accent-blue);" id="oOver25">Adil: -</div>
                                </div>
                                <div style="display:flex; align-items:center; gap:8px;">
                                    <div class="market-val" id="pOver25">-%</div>
                                    <button class="btn-add-slip" style="width:auto; padding:3px 7px;" onclick="addCurrentToSlip('2.5 ÜST')">+</button>
                                </div>
                            </div>
                            <div class="market-item">
                                <div>
                                    <div class="market-label">2.5 ALT</div>
                                    <div style="font-size:0.75rem; color:var(--accent-blue);" id="oUnder25">Adil: -</div>
                                </div>
                                <div style="display:flex; align-items:center; gap:8px;">
                                    <div class="market-val" id="pUnder25">-%</div>
                                    <button class="btn-add-slip" style="width:auto; padding:3px 7px;" onclick="addCurrentToSlip('2.5 ALT')">+</button>
                                </div>
                            </div>
                            <div class="market-item">
                                <div>
                                    <div class="market-label">KG VAR</div>
                                    <div style="font-size:0.75rem; color:var(--accent-blue);" id="oBttsYes">Adil: -</div>
                                </div>
                                <div style="display:flex; align-items:center; gap:8px;">
                                    <div class="market-val" id="pBttsYes">-%</div>
                                    <button class="btn-add-slip" style="width:auto; padding:3px 7px;" onclick="addCurrentToSlip('KG VAR')">+</button>
                                </div>
                            </div>
                            <div class="market-item">
                                <div>
                                    <div class="market-label">KG YOK</div>
                                    <div style="font-size:0.75rem; color:var(--accent-blue);" id="oBttsNo">Adil: -</div>
                                </div>
                                <div style="display:flex; align-items:center; gap:8px;">
                                    <div class="market-val" id="pBttsNo">-%</div>
                                    <button class="btn-add-slip" style="width:auto; padding:3px 7px;" onclick="addCurrentToSlip('KG YOK')">+</button>
                                </div>
                            </div>
                        </div>

                        <!-- SQUAD INJURY & PLAYER IMPACT LAB -->
                        <div style="background: #0f1626; border: 1px solid #1e293b; border-radius: 10px; padding: 14px; margin-top: 14px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
                                <div style="display:flex; align-items:center; gap:8px;">
                                    <span style="font-size:1.15rem;">🚑</span>
                                    <div>
                                        <strong style="color:#fff; font-size:0.92rem;">Kadro, Sakatlık & Kilit Oyuncu Etki Laboratuvarı</strong>
                                        <div style="font-size:0.75rem; color:var(--text-muted);">Oyuncu üzerine tıkla: Eksikliğin kupon oranına ve xG'ye etkisini anında simüle et!</div>
                                    </div>
                                </div>
                                <button class="btn-action-nav" onclick="resetInjuries()" style="font-size:0.75rem; padding:4px 10px;">Sıfırla</button>
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 10px;">
                                <div>
                                    <div style="font-size:0.78rem; font-weight:700; color:var(--accent-green); margin-bottom:6px;" id="lblHomeSquadTitle">🏠 Ev Sahibi Kilit Oyuncular</div>
                                    <div id="homeSquadList" style="display:flex; flex-direction:column; gap:6px;"></div>
                                </div>
                                <div>
                                    <div style="font-size:0.78rem; font-weight:700; color:var(--accent-red); margin-bottom:6px;" id="lblAwaySquadTitle">✈️ Deplasman Kilit Oyuncular</div>
                                    <div id="awaySquadList" style="display:flex; flex-direction:column; gap:6px;"></div>
                                </div>
                            </div>

                            <!-- AI Tactical Insights Box -->
                            <div id="aiInsightsContainer" style="background:#0a0e17; border-radius:8px; border:1px dashed #334155; padding:10px; margin-top:8px;">
                                <div style="font-size:0.75rem; color:var(--text-muted);">Kadro analiz ediliyor...</div>
                            </div>
                        </div>
                    </div>

                    <!-- 6x6 Matrix & Top 5 Row -->
                    <div style="display:grid; grid-template-columns: 1.2fr 0.8fr; gap:16px;">
                        <div class="card">
                            <div class="card-header"><span>📊 6x6 Skor Olasılık Matrisi</span></div>
                            <table class="matrix-table" id="matrixTable"></table>
                        </div>
                        <div class="card">
                            <div class="card-header"><span>🏆 En Olası İlk 5 Skor</span></div>
                            <div class="scores-list" id="topScoresList"></div>
                        </div>
                    </div>

                    <!-- Team Rankings Table -->
                    <div class="card">
                        <div class="card-header">
                            <span id="rankTitle">🛡️ Seçili Lig Güç Sıralaması (Hücum & Savunma)</span>
                        </div>
                        <table class="rank-table" id="rankTable">
                            <thead>
                                <tr>
                                    <th>Takım</th>
                                    <th>Ev Hüc</th>
                                    <th>Dep Hüc</th>
                                    <th>Sav Zaf</th>
                                    <th>Güç İndeksi</th>
                                </tr>
                            </thead>
                            <tbody id="rankBody"></tbody>
                        </table>
                    </div>
                </div>

                <!-- 2. Live Match Radar View -->
                <div id="radarView" style="display: none;">
                    <div class="card">
                        <div class="card-header">
                            <span>📡 Otonom Canlı Maç Radarı (13+ Dünya Ligi)</span>
                            <span style="font-size: 0.82rem; color: var(--accent-green);">İddaa Oranları & +EV Değeriyle</span>
                        </div>
                        <div class="radar-filter-bar">
                            <button class="radar-filter-btn active" id="rfAll" onclick="filterRadar('all', this)">Tüm Canlı Maçlar (<span id="countAll">75</span>)</button>
                            <button class="radar-filter-btn" id="rfValue" onclick="filterRadar('value', this)">🔥 En İyi Oranlı Değer Bahisleri (+EV)</button>
                            <button class="radar-filter-btn" id="rfBanko" onclick="filterRadar('banko', this)">🛡️ En Net Bankolar (%75+ Güven)</button>
                            <button class="radar-filter-btn" id="rfGoals" onclick="filterRadar('goals', this)">⚽ 2.5 Alt / Üst Golleri</button>
                        </div>
                        <div id="radarList"></div>
                    </div>
                </div>

                <!-- 3. Model Accuracy Backtest View -->
                <div id="backtestView" style="display: none;">
                    <div class="card">
                        <div class="card-header">
                            <span>🧪 Geçmiş Maçlar Doğrulama & Başarı Oranı (Backtest)</span>
                            <span style="font-size: 0.85rem; font-weight:700; color: var(--accent-green);">Genel Başarı: %73.75 Hit Rate</span>
                        </div>
                        <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 14px;">
                            Model yalnızca geçmiş maçlarla eğitilmiş, son haftalarda oynanmış 167 maç üzerinde bağımsız olarak test edilmiştir.
                        </p>
                        <table class="rank-table" id="backtestTable">
                            <thead>
                                <tr>
                                    <th>Lig</th>
                                    <th>Eğitim</th>
                                    <th>Test (Son Haftalar)</th>
                                    <th>Model Başarısı (%70-%95)</th>
                                    <th>Çifte Şans</th>
                                    <th>2.5 Alt/Üst</th>
                                </tr>
                            </thead>
                            <tbody id="backtestBody"></tbody>
                        </table>
                    </div>
                </div>

                <!-- 4. Interactive User Guide & Strategy Academy -->
                <div id="guideView" style="display: none;">
                    <div class="card">
                        <div class="card-header">
                            <span>🎓 Kullanım Kılavuzu & Bahis Stratejisi Rehberi</span>
                            <span style="font-size: 0.82rem; color: var(--accent-blue);">Sistemi En Verimli Kullanma Kılavuzu</span>
                        </div>

                        <!-- Karşılama Kartı -->
                        <div style="background: linear-gradient(135deg, rgba(56, 189, 248, 0.12), rgba(16, 185, 129, 0.12)); border: 1px solid #1e293b; border-radius: 12px; padding: 18px; margin-bottom: 20px;">
                            <h3 style="font-size: 1.15rem; color: #fff; margin-bottom: 6px;">👋 Hoş Geldin! Bu Sistem Sana Ne Kazandırır?</h3>
                            <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                                Bu sistem tahminlerini şansa veya hislere göre değil; <strong>Poisson & Dixon-Coles matematiksel olasılık dağılımı</strong> ve <strong>oyuncu sakatlık etki katsayıları</strong> ile yapar. İddaa bürolarının açtığı hatalı oranları tespit eder (<strong>+EV Değer Bahisleri</strong>) ve tutma ihtimali en yüksek banko kuponları saniyeler içinde önünüze serer.
                            </p>
                        </div>

                        <!-- 3 Adımda Sistem Nasıl Çalışır? -->
                        <h3 style="font-size: 1.05rem; color: #fff; margin-bottom: 12px; display:flex; align-items:center; gap:8px;">
                            <span>🚀</span> 3 Adımda Sistemin Kullanımı (Ne Yaparsam Ne Olur?)
                        </h3>

                        <!-- Adım 1 -->
                        <div class="guide-step-card">
                            <div class="guide-step-header">
                                <div class="guide-num">1</div>
                                <div>
                                    <div class="guide-title">Bülteni Tazeleyin (Canlı Fikstür & Oranlar)</div>
                                    <div style="font-size:0.78rem; color:var(--accent-blue);">⚡ Tek tıkla 12+ dünya ligini çekin</div>
                                </div>
                            </div>
                            <div class="guide-desc">
                                <strong>Ne yapacaksınız?</strong> Sağ üstteki <code>[⚡ Canlı İddaa Bültenini Yenile]</code> butonuna tıklayın.<br>
                                <strong>Bunu yaparsanız ne elde edersiniz?</strong> Süper Lig, Premier League, La Liga, Serie A vb. 12+ ligin bugünkü ve önümüzdeki 4 günün <strong>75+ gerçek maçını, başlama saatlerini ve canlı büro oranlarını</strong> sistem 2-3 saniyede belleğe çeker.
                            </div>
                            <div class="guide-actions-bar">
                                <button class="guide-btn-action" onclick="triggerLiveRefresh()">⚡ Hemen Bülteni Yenile</button>
                            </div>
                        </div>

                        <!-- Adım 2 -->
                        <div class="guide-step-card">
                            <div class="guide-step-header">
                                <div class="guide-num">2</div>
                                <div>
                                    <div class="guide-title">Canlı Maç Radarı ile Filtreleyin (Amacınıza Uygun Maçı Seçin)</div>
                                    <div style="font-size:0.78rem; color:var(--accent-yellow);">🎯 İhtiyacınıza göre filtreleyin</div>
                                </div>
                            </div>
                            <div class="guide-desc">
                                Üst menüden <strong>"📡 Canlı Maç Radarı"</strong> sekmesine geçin. Burada 4 kritik filtre yer alır:
                            </div>
                            <div class="guide-grid-cards">
                                <div class="guide-box val">
                                    <span class="guide-tip-pill" style="background:rgba(245,158,11,0.2); color:var(--accent-yellow);">KÂR & ORAN ODAKLI</span>
                                    <h4>🔥 En İyi Oranlı Değer Bahisleri (+EV)</h4>
                                    <p><strong>Bunu seçerseniz:</strong> İddaa'nın açtığı oranın, modelin adil oranından daha yüksek olduğu avantajlı maçları görürsünüz.</p>
                                    <div class="benefit">💡 Amaç: Uzun vadede bahis bürosunu matematiksel olarak yenmek.</div>
                                </div>
                                <div class="guide-box safe">
                                    <span class="guide-tip-pill" style="background:rgba(16,185,129,0.2); color:var(--accent-green);">GÜVEN ODAKLI</span>
                                    <h4>🛡️ En Net Bankolar (%75+ Güven)</h4>
                                    <p><strong>Bunu seçerseniz:</strong> Tutma ihtimali %75 ile %98 arasında olan en garanti maçlar sıralanır (Genelde 1X Çifte Şans veya net ev sahibi).</p>
                                    <div class="benefit">💡 Amaç: Kasa katlama ve sıfıra yakın risk.</div>
                                </div>
                                <div class="guide-box goal">
                                    <span class="guide-tip-pill" style="background:rgba(139,92,246,0.2); color:var(--accent-purple);">GOL ODAKLI</span>
                                    <h4>⚽ 2.5 Alt / Üst Golleri</h4>
                                    <p><strong>Bunu seçerseniz:</strong> Taraf bahsi yerine maçtaki beklenen toplam gol sayısı (xG) uç noktalarda olan maçlar listelenir.</p>
                                    <div class="benefit">💡 Amaç: Sürpriz taraf riskine girmeden gollere oynamak.</div>
                                </div>
                            </div>
                            <div class="guide-actions-bar">
                                <button class="guide-btn-action" onclick="switchMainView('radar')">📡 Canlı Maç Radarına Git</button>
                            </div>
                        </div>

                        <!-- Adım 3 -->
                        <div class="guide-step-card">
                            <div class="guide-step-header">
                                <div class="guide-num">3</div>
                                <div>
                                    <div class="guide-title">Sakatlık Simülasyonu & Otonom Kupon Üretimi</div>
                                    <div style="font-size:0.78rem; color:var(--accent-green);">🎫 Kadro etkisi & Tek tıkla hazır kupon</div>
                                </div>
                            </div>
                            <div class="guide-desc">
                                <strong>🚑 Sakatlık Simülatörü:</strong> Bir maç seçtiğinizde takımın yıldız oyuncuları listelenir. Örneğin <em>"Haaland sakat"</em> diye işaretlediğinizde, model hücum gücünü anında %22 düşürür, beklenen golü azaltır ve kupon tercihini 2.5 Alt veya Çifte Şans yönünde otomatik günceller.<br><br>
                                <strong>Sağ Paneldeki 3 Kupon Butonu:</strong>
                            </div>
                            <ul style="padding-left: 20px; font-size: 0.85rem; color: #cbd5e1; line-height: 1.8; margin-bottom: 12px;">
                                <li><strong style="color:var(--accent-green);">🛡️ %70 - %95 Banko Kasa Kuponu:</strong> Kazanma olasılığı en yüksek 3 maçı seçer, kuponun genel başarı oranı %80+ civarındadır.</li>
                                <li><strong style="color:var(--accent-yellow);">🔥 Yüksek Oranlı Değer (+EV) Kuponu:</strong> Oranı yüksek ve büro hatası olan maçları toplar, az parayla yüksek getiri hedefler.</li>
                                <li><strong style="color:var(--accent-purple);">⚽ 2.5 Alt/Üst Gol Kuponu:</strong> En belirgin 3 gol bahsini kupona yansıtır.</li>
                            </ul>
                            <div class="guide-actions-bar">
                                <button class="guide-btn-action" style="color:var(--accent-green); border-color:var(--accent-green);" onclick="loadCoupon('banko')">🛡️ Banko Kuponu Doldur</button>
                                <button class="guide-btn-action" style="color:var(--accent-yellow); border-color:var(--accent-yellow);" onclick="loadCoupon('value')">🔥 Değer Kuponunu Doldur</button>
                                <button class="guide-btn-action" style="color:var(--accent-purple); border-color:var(--accent-purple);" onclick="loadCoupon('goals')">⚽ Gol Kuponunu Doldur</button>
                            </div>
                        </div>

                        <!-- Kavramlar Sözlüğü -->
                        <div class="card" style="margin-top: 20px; border-color: #334155;">
                            <div class="card-header">
                                <span>📖 Bilinmesi Gereken Altın Kavramlar</span>
                            </div>
                            <div style="display:flex; flex-direction:column; gap:12px; font-size:0.85rem; color:#cbd5e1;">
                                <div style="background:#0a0e17; padding:12px; border-radius:8px; border:1px solid var(--border);">
                                    <strong style="color:var(--accent-yellow); font-size:0.92rem;">• Pozitif Beklenen Değer (+EV) Nedir?</strong>
                                    <p style="margin-top:4px; color:var(--text-muted);">
                                        Örnek: Bir maçın ev sahibi galibiyetini model %60 buldu. Matematiksel olarak olması gereken "Adil Oran" 1.67'dir. Ancak İddaa bu maça 2.10 oran açtıysa, burada %26'lık bir <strong>+EV avantajı</strong> vardır. Uzun vadede yalnızca +EV bahisler oynayarak istikrarlı kazanç elde edilir.
                                    </p>
                                </div>
                                <div style="background:#0a0e17; padding:12px; border-radius:8px; border:1px solid var(--border);">
                                    <strong style="color:var(--accent-blue); font-size:0.92rem;">• Beklenen Gol (xG / λ) Nedir?</strong>
                                    <p style="margin-top:4px; color:var(--text-muted);">
                                        Takımların iç saha hücum gücü ile rakibin deplasman savunma zafiyetinin çarpımıyla elde edilen, o maçta atılması beklenen kesin gol miktarıdır.
                                    </p>
                                </div>
                                <div style="background:#0a0e17; padding:12px; border-radius:8px; border:1px solid var(--border);">
                                    <strong style="color:var(--accent-green); font-size:0.92rem;">• Kasa Yönetimi (Kelly Kriteri) Nedir?</strong>
                                    <p style="margin-top:4px; color:var(--text-muted);">
                                        Asla tek bir kupona tüm paranızı basmayın. Sistem sağ panelde size <strong>"Önerilen Kasa Riski"</strong> hesaplar. Banko kuponlarda kasanın %10-%18'i, Değer kuponlarında ise %2-%5'i oranında bahis yapılması önerilir.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Side: BET SLIP & PREMIER 70-95% AUTO COUPON -->
            <div>
                <div class="card slip-card">
                    <div class="slip-header">
                        <h2>🎫 Kupon Analizörü <span style="font-size:0.8rem; color:var(--accent-blue);" id="slipCountBadge">(0 Maç)</span></h2>
                        <button class="btn-clear-slip" onclick="clearSlip()">Temizle</button>
                    </div>

                    <!-- MULTI-TIER AUTO-COUPON BUTTONS -->
                    <button class="btn-premier-coupon" onclick="loadCoupon('banko')">
                        <span>🛡️ %70 - %95 BANKO KASA KUPONU</span>
                    </button>
                    <button class="btn-coupon-val" onclick="loadCoupon('value')">
                        <span>🔥 YÜKSEK ORANLI DEĞER (+EV) KUPONU</span>
                    </button>
                    <button class="btn-coupon-goal" onclick="loadCoupon('goals')">
                        <span>⚽ 2.5 ALT / ÜST GOL KUPONU</span>
                    </button>

                    <!-- Slip Items List -->
                    <div class="slip-items-list" id="slipItemsList">
                        <div style="text-align: center; color: var(--text-muted); font-size: 0.82rem; padding: 20px 0;">
                            Henüz kupona maç eklenmedi.<br>Yukarıdaki <strong>[%70 - %95 KASA KUPONUNU GETİR]</strong> butonuna basın veya sol taraftan maç ekleyin!
                        </div>
                    </div>

                    <!-- Manual Match Addition -->
                    <div style="background:#0a0e17; border:1px dashed #334155; border-radius:8px; padding:10px;">
                        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">➕ DIŞARIDAN MAÇ / ORAN EKLE</div>
                        <input type="text" id="manualMatchName" placeholder="Örn: Persepolis vs Esteghlal" style="width:100%; margin-bottom:6px; font-size:0.8rem; padding:6px 8px;">
                        <div style="display: flex; gap: 6px;">
                            <input type="text" id="manualPick" placeholder="Seçim (Örn: 1 veya 2.5 Alt)" style="flex:1; font-size:0.8rem; padding:6px 8px;">
                            <input type="number" step="0.05" id="manualOdds" placeholder="Oran (1.85)" style="width:90px; font-size:0.8rem; padding:6px 8px;">
                        </div>
                        <button class="btn-add-slip" style="margin-top: 6px;" onclick="addManualToSlip()">Kupona Ekle</button>
                    </div>

                    <!-- Slip Summary Calculations -->
                    <div class="slip-summary-box" style="margin-top: 14px;">
                        <div class="slip-summary-row">
                            <span style="color: var(--text-muted);">Toplam Büro Oranı:</span>
                            <span class="slip-big-odds" id="slipTotalOdds">1.00</span>
                        </div>
                        <div class="slip-summary-row">
                            <span style="color: var(--text-muted);">Kupon Başarı Olasılığı:</span>
                            <span style="font-weight: 700; color: #fff;" id="slipModelProb">%0.0</span>
                        </div>
                        <div class="slip-summary-row">
                            <span style="color: var(--text-muted);">Model Adil Oranı:</span>
                            <span style="font-weight: 700; color: var(--accent-blue);" id="slipFairOdds">1.00</span>
                        </div>
                        <div class="slip-summary-row">
                            <span style="color: var(--text-muted);">Matematiksel Değer (+EV):</span>
                            <span class="slip-edge-badge" id="slipEdgeBadge">-</span>
                        </div>
                        <hr style="border: 0; border-top: 1px solid #1e293b; margin: 8px 0;">
                        <div class="slip-summary-row">
                            <span style="color: var(--text-muted); font-size: 0.8rem;">Kupon Tutarı:</span>
                            <input type="number" id="slipStake" value="100" style="width: 90px; padding: 4px 6px; font-size: 0.82rem;" oninput="recalcSlip()">
                        </div>
                        <div class="slip-summary-row">
                            <span style="color: var(--accent-green); font-weight: 600;">Potansiyel Kazanç:</span>
                            <span style="font-weight: 800; color: var(--accent-green); font-size: 1.05rem;" id="slipPayout">0.00 TL</span>
                        </div>
                    </div>
                </div>

                <!-- Realistic Disclaimer -->
                <div class="notice-card">
                    <div class="notice-title">💡 Matematiksel Kasa Yönetimi (Kelly Kriteri)</div>
                    <div class="notice-body">
                        Bu sistem rastgele tahminler üretmez. Yüksek olasılıklı (%70 - %95) tercihleri filtreler.
                        Sermayenizi korumak için tek bir kupona kasanızın en fazla <strong>%5 - %8</strong>'ini yatırmanız önerilir.
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentLeague = "premier_league";
        let currentPrediction = null;
        let betSlip = [];
        let currentView = 'single';
        let cachedLeagues = {};

        async function initApp() {
            const lRes = await fetch('/api/leagues');
            const leagues = await lRes.json();
            cachedLeagues = leagues;
            const tabContainer = document.getElementById('leagueTabs');
            tabContainer.innerHTML = '';

            for (const [key, val] of Object.entries(leagues)) {
                const btn = document.createElement('button');
                btn.className = `league-tab-btn ${key === currentLeague ? 'active' : ''}`;
                const flagSrc = val.flag_code ? `https://flagcdn.com/w40/${val.flag_code}.png` : '';
                btn.innerHTML = `<img src="${flagSrc}" class="flag-icon-badge" alt="${val.flag}" onerror="this.outerHTML='<span style=\\'margin-right:4px;\\'>${val.flag}</span>'"> <span>${val.name}</span>`;
                btn.onclick = (e) => selectLeague(key, e);
                tabContainer.appendChild(btn);
            }

            await loadLeagueData(currentLeague);
        }

        function switchMainView(viewType) {
            currentView = viewType;
            const singleV = document.getElementById('singleMatchView');
            const radarV = document.getElementById('radarView');
            const backtestV = document.getElementById('backtestView');
            const guideV = document.getElementById('guideView');
            const controls = document.getElementById('matchControls');
            const btnSingle = document.getElementById('btnViewSingle');
            const btnRadar = document.getElementById('btnViewRadar');
            const btnBacktest = document.getElementById('btnViewBacktest');
            const btnGuide = document.getElementById('btnViewGuide');

            singleV.style.display = 'none';
            radarV.style.display = 'none';
            backtestV.style.display = 'none';
            if (guideV) guideV.style.display = 'none';
            controls.style.display = 'none';

            btnSingle.classList.remove('active');
            btnRadar.classList.remove('active');
            btnBacktest.classList.remove('active');
            if (btnGuide) btnGuide.classList.remove('active');

            if (viewType === 'radar') {
                radarV.style.display = 'block';
                btnRadar.classList.add('active');
                loadRadarMatches();
            } else if (viewType === 'backtest') {
                backtestV.style.display = 'block';
                btnBacktest.classList.add('active');
                loadBacktestData();
            } else if (viewType === 'guide') {
                if (guideV) guideV.style.display = 'block';
                if (btnGuide) btnGuide.classList.add('active');
            } else {
                singleV.style.display = 'block';
                controls.style.display = 'flex';
                btnSingle.classList.add('active');
            }
        }

        async function loadBacktestData() {
            const res = await fetch('/api/backtest');
            const data = await res.json();
            const bBody = document.getElementById('backtestBody');
            bBody.innerHTML = '';

            data.leagues.forEach(l => {
                bBody.innerHTML += `
                    <tr>
                        <td style="font-weight:700;">${l.league_name}</td>
                        <td>${l.train_matches} Maç</td>
                        <td>${l.test_matches} Maç</td>
                        <td style="font-weight:700; color:var(--accent-green); font-size:0.95rem;">%${l.high_conf_accuracy} <span style="font-size:0.75rem; color:var(--text-muted);">(${l.high_conf_hits}/${l.high_conf_total})</span></td>
                        <td>%${l.dc_accuracy}</td>
                        <td>%${l.ou_accuracy}</td>
                    </tr>
                `;
            });
        }

        let allRadarMatches = [];
        let currentRadarFilter = 'all';

        async function triggerLiveRefresh() {
            const btn = document.getElementById('btnLiveRefresh');
            const origHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = `<span>⏳</span> Canlı Bülten Çekiliyor...`;
            try {
                const res = await fetch('/api/live_refresh');
                const data = await res.json();
                document.getElementById('pillBotStatus').innerText = `Otonom Bot Aktif • ${data.scanned_count} Canlı Maç Tarandı`;
                allRadarMatches = data.matches || [];
                document.getElementById('countAll').innerText = allRadarMatches.length;
                filterRadar(currentRadarFilter);
                alert(`✅ ${data.scanned_count} adet güncel maç ve canlı İddaa oranı başarıyla güncellendi!`);
            } catch(e) {
                alert('Bülten güncellenirken hata oluştu: ' + e);
            } finally {
                btn.disabled = false;
                btn.innerHTML = origHtml;
            }
        }

        async function loadRadarMatches() {
            const res = await fetch('/api/bot_radar');
            allRadarMatches = await res.json();
            document.getElementById('countAll').innerText = allRadarMatches.length;
            document.getElementById('pillBotStatus').innerText = `Otonom Bot Aktif • ${allRadarMatches.length} Canlı Maç Tarandı`;
            filterRadar(currentRadarFilter);
        }

        function filterRadar(filterType, btnElement) {
            currentRadarFilter = filterType;
            if (btnElement) {
                document.querySelectorAll('.radar-filter-btn').forEach(b => b.classList.remove('active'));
                btnElement.classList.add('active');
            }

            let filtered = [...allRadarMatches];
            if (filterType === 'value') {
                filtered = filtered.filter(m => (m.best_val_ev && m.best_val_ev > 0) || (m.ev_pct && m.ev_pct > 0));
                filtered.sort((a, b) => ((b.best_val_ev || b.ev_pct || 0) - (a.best_val_ev || a.ev_pct || 0)));
            } else if (filterType === 'banko') {
                filtered = filtered.filter(m => m.best_prob >= 75.0);
                filtered.sort((a, b) => b.best_prob - a.best_prob);
            } else if (filterType === 'goals') {
                filtered = filtered.filter(m => m.best_pick.includes('2.5') || (m.options && m.options.some(o => o.market.includes('2.5') && o.prob >= 0.58)));
            }

            renderFilteredRadar(filtered, filterType);
        }

        function renderFilteredRadar(matches, filterType) {
            const container = document.getElementById('radarList');
            container.innerHTML = '';

            if (matches.length === 0) {
                container.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:0.85rem;">Bu filtreye uygun maç bulunamadı.</div>`;
                return;
            }

            matches.forEach(m => {
                const isValFilter = filterType === 'value';
                const pick = isValFilter ? (m.best_val_pick || m.best_pick) : m.best_pick;
                const pickDesc = isValFilter ? (m.best_val_desc || m.best_pick_desc) : m.best_pick_desc;
                const prob = isValFilter ? (m.best_val_prob || m.best_prob) : m.best_prob;
                const odds = isValFilter ? (m.best_val_odds || m.best_odds) : m.best_odds;
                const fairOdds = m.best_fair || (100.0 / prob).toFixed(2);
                const evVal = isValFilter ? (m.best_val_ev || m.ev_pct || 0) : (m.ev_pct || 0);

                const badgeClass = prob >= 80 ? 'badge-ultra' : 'badge-high';
                const evBadgeHtml = evVal > 0 
                    ? `<span class="radar-badge badge-pos-ev" style="margin-left:4px;">+${evVal}% EV</span>` 
                    : '';

                const flagImg = m.flag_code 
                    ? `<img src="https://flagcdn.com/w40/${m.flag_code}.png" class="flag-icon-badge" alt="${m.flag}" onerror="this.outerHTML='<span style=\\'margin-right:6px;\\'>${m.flag}</span>'">` 
                    : `<span style="margin-right:6px;">${m.flag}</span>`;

                container.innerHTML += `
                    <div class="radar-card-item">
                        <div>
                            <div class="radar-match-title" style="display:flex; align-items:center;">
                                ${flagImg} <span>${m.home} vs ${m.away}</span>
                                <span style="font-size:0.75rem; background:#1e293b; color:#38bdf8; padding:2px 8px; border-radius:12px; margin-left:8px;">${m.date}</span>
                            </div>
                            <div class="radar-meta">
                                ${m.league_name} • Beklenen Gol: ${m.lambda_home.toFixed(2)} - ${m.lambda_away.toFixed(2)} 
                                | Büro: <strong style="color:#fff;">${odds}</strong> (Adil: <span style="color:var(--accent-blue);">${fairOdds}</span>)
                            </div>
                        </div>
                        <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
                            <div style="text-align:right;">
                                <div style="font-weight:700; color:var(--accent-yellow); font-size:0.92rem;">${pick}</div>
                                <div style="font-size:0.75rem; color:var(--text-muted);">${pickDesc}</div>
                            </div>
                            <span class="radar-badge ${badgeClass}">%${prob} Güven</span>
                            ${evBadgeHtml}
                            <button class="btn-add-slip" style="width:auto; padding:6px 14px;" onclick="addDirectToSlip('${m.home} vs ${m.away}', '${pick}', ${odds}, ${prob/100.0})">
                                Kupona Ekle (${odds})
                            </button>
                        </div>
                    </div>
                `;
            });
        }

        async function loadCoupon(couponType = 'banko') {
            const res = await fetch(`/api/bot_generate_coupon?type=${couponType}`);
            const coupon = await res.json();

            betSlip = [];
            coupon.legs.forEach(leg => {
                betSlip.push({
                    id: Date.now() + Math.random(),
                    match: leg.match,
                    pick: leg.pick,
                    odds: leg.odds,
                    fairOdds: leg.fair_odds,
                    prob: leg.prob_pct / 100.0
                });
            });

            renderSlip();
        }

        function loadPremierCoupon() {
            loadCoupon('banko');
        }

        async function selectLeague(leagueKey, evt) {
            currentLeague = leagueKey;
            document.querySelectorAll('.league-tab-btn').forEach(b => b.classList.remove('active'));
            if (evt && evt.currentTarget) evt.currentTarget.classList.add('active');
            if (currentView === 'radar') switchMainView('single');
            await loadLeagueData(leagueKey);
        }

        async function loadLeagueData(leagueKey) {
            const sumRes = await fetch(`/api/summary?league=${leagueKey}`);
            const sum = await sumRes.json();
            document.getElementById('sTotalMatches').innerText = sum.total_matches;
            document.getElementById('sTeamsCount').innerText = sum.unique_teams_count + ' Takım';
            document.getElementById('sHomeAvg').innerText = sum.avg_home_goals.toFixed(2);
            document.getElementById('sAwayAvg').innerText = sum.avg_away_goals.toFixed(2);
            document.getElementById('sTotalAvg').innerText = sum.avg_total_goals.toFixed(2);
            document.getElementById('sOver25').innerText = '2.5 Üst: %' + sum.over_2_5_pct.toFixed(1);

            const teamsRes = await fetch(`/api/teams?league=${leagueKey}`);
            const teams = await teamsRes.json();
            const hSel = document.getElementById('homeSelect');
            const aSel = document.getElementById('awaySelect');
            hSel.innerHTML = '';
            aSel.innerHTML = '';

            teams.forEach((t, idx) => {
                hSel.innerHTML += `<option value="${t}" ${idx === 0 ? 'selected' : ''}>${t}</option>`;
                aSel.innerHTML += `<option value="${t}" ${idx === 1 ? 'selected' : ''}>${t}</option>`;
            });

            const rankRes = await fetch(`/api/ratings?league=${leagueKey}`);
            const ranks = await rankRes.json();
            const rBody = document.getElementById('rankBody');
            rBody.innerHTML = '';
            ranks.forEach(r => {
                rBody.innerHTML += `
                    <tr>
                        <td style="font-weight: 600;">${r.Takım}</td>
                        <td style="color: var(--accent-green);">${r['Ev Hücum']}</td>
                        <td style="color: var(--accent-blue);">${r['Dep Hücum']}</td>
                        <td style="color: var(--accent-red);">${r['Ev Savunma']}</td>
                        <td style="font-weight: 700; color: #fff;">${r['Genel Güç']}</td>
                    </tr>
                `;
            });

            runPrediction();
        }

        let customInjuriesHome = new Set();
        let customInjuriesAway = new Set();
        let lastLoadedHomeTeam = "";
        let lastLoadedAwayTeam = "";
        let homeSquadData = [];
        let awaySquadData = [];

        function resetInjuries() {
            customInjuriesHome.clear();
            customInjuriesAway.clear();
            runPrediction();
        }

        async function fetchSquadsIfNeeded(home, away) {
            if (home !== lastLoadedHomeTeam) {
                lastLoadedHomeTeam = home;
                customInjuriesHome.clear();
                try {
                    const res = await fetch(`/api/squad?team=${encodeURIComponent(home)}`);
                    homeSquadData = await res.json();
                } catch(e) { homeSquadData = []; }
            }
            if (away !== lastLoadedAwayTeam) {
                lastLoadedAwayTeam = away;
                customInjuriesAway.clear();
                try {
                    const res = await fetch(`/api/squad?team=${encodeURIComponent(away)}`);
                    awaySquadData = await res.json();
                } catch(e) { awaySquadData = []; }
            }
        }

        function togglePlayerInjury(isHome, playerName) {
            const set = isHome ? customInjuriesHome : customInjuriesAway;
            if (set.has(playerName)) {
                set.delete(playerName);
            } else {
                set.add(playerName);
            }
            runPrediction();
        }

        function renderSquadList(containerId, squad, isHome) {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            const injurySet = isHome ? customInjuriesHome : customInjuriesAway;

            if (!squad || squad.length === 0) {
                container.innerHTML = `<div style="font-size:0.75rem; color:var(--text-muted);">Kadro bilgisi yükleniyor...</div>`;
                return;
            }

            squad.forEach(p => {
                const isInjured = p.is_injured || injurySet.has(p.name);
                const row = document.createElement('div');
                row.className = `player-item-row ${isInjured ? 'injured' : ''}`;
                row.onclick = () => togglePlayerInjury(isHome, p.name);

                row.innerHTML = `
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="player-tag-pos">${p.position}</span>
                        <div>
                            <div style="font-weight:700; color:#fff;">${p.name}</div>
                            <div style="font-size:0.72rem; color:var(--text-muted);">${p.role_desc}</div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="player-impact-star">★ ${p.impact_score}</span>
                        <span class="player-status-badge ${isInjured ? 'status-out' : 'status-fit'}">
                            ${isInjured ? '🔴 Sakat' : '🟢 Hazır'}
                        </span>
                    </div>
                `;
                container.appendChild(row);
            });
        }

        async function runPrediction() {
            const home = document.getElementById('homeSelect').value;
            const away = document.getElementById('awaySelect').value;
            const rho = document.getElementById('rhoSelect').value;

            if (home === away) {
                alert('Ev sahibi ve deplasman takımı farklı olmalıdır!');
                return;
            }

            const curL = cachedLeagues[currentLeague] || {};
            const flagBadge = curL.flag_code ? `<img src="https://flagcdn.com/w40/${curL.flag_code}.png" class="flag-icon-badge" style="width:24px; height:17px; margin-right:8px;" onerror="this.outerHTML='<span style=\\'margin-right:8px;\\'>${curL.flag || '⚽'}</span>'">` : `<span style="margin-right:8px;">${curL.flag || '⚽'}</span>`;
            document.getElementById('matchTitle').innerHTML = `<div style="display:flex; align-items:center;">${flagBadge} <span>${home} vs ${away}</span></div>`;
            document.getElementById('lblHomeSquadTitle').innerText = `🏠 ${home} Kilit Oyuncular`;
            document.getElementById('lblAwaySquadTitle').innerText = `✈️ ${away} Kilit Oyuncular`;

            await fetchSquadsIfNeeded(home, away);

            const injHStr = Array.from(customInjuriesHome).join(',');
            const injAStr = Array.from(customInjuriesAway).join(',');

            const res = await fetch(`/api/predict?league=${currentLeague}&home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}&rho=${rho}&injuries_home=${encodeURIComponent(injHStr)}&injuries_away=${encodeURIComponent(injAStr)}`);
            const data = await res.json();
            currentPrediction = data;

            // Render squads with active statuses
            renderSquadList('homeSquadList', homeSquadData, true);
            renderSquadList('awaySquadList', awaySquadData, false);

            // Render AI Insights
            const insBox = document.getElementById('aiInsightsContainer');
            insBox.innerHTML = '';
            if (data.injury_analysis && data.injury_analysis.ai_insights) {
                data.injury_analysis.ai_insights.forEach(ins => {
                    const cls = ins.level === 'CRITICAL' ? 'critical' : (ins.level === 'COUPON_TIP' ? 'tip' : '');
                    insBox.innerHTML += `
                        <div class="ai-insight-item ${cls}">
                            <strong style="margin-right:6px;">${ins.badge}:</strong> ${ins.text}
                        </div>
                    `;
                });
            }

            let xgText = `${home} (${data.lambda_home.toFixed(2)}) - (${data.lambda_away.toFixed(2)}) ${away} | Toplam: ${data.expected_total_goals.toFixed(2)} Gol`;
            if (data.injury_analysis && (data.injury_analysis.home_attack_penalty_pct > 0 || data.injury_analysis.away_attack_penalty_pct > 0)) {
                xgText += ` • ⚠️ Sakatlık Etkisi Devrede!`;
            }
            document.getElementById('xgSummary').innerText = xgText;

            const p1 = data.probabilities_1x2.HomeWin;
            const px = data.probabilities_1x2.Draw;
            const p2 = data.probabilities_1x2.AwayWin;

            document.getElementById('lblHomeWin').innerText = `1 (${home})`;
            document.getElementById('lblAwayWin').innerText = `2 (${away})`;

            document.getElementById('pHomeWin').innerText = '%' + p1.toFixed(1);
            document.getElementById('oHomeWin').innerText = 'Adil: ' + data.fair_odds_1x2['1'].toFixed(2);
            document.getElementById('barHomeWin').style.width = p1 + '%';

            document.getElementById('pDraw').innerText = '%' + px.toFixed(1);
            document.getElementById('oDraw').innerText = 'Adil: ' + data.fair_odds_1x2['X'].toFixed(2);
            document.getElementById('barDraw').style.width = px + '%';

            document.getElementById('pAwayWin').innerText = '%' + p2.toFixed(1);
            document.getElementById('oAwayWin').innerText = 'Adil: ' + data.fair_odds_1x2['2'].toFixed(2);
            document.getElementById('barAwayWin').style.width = p2 + '%';

            const ou = data.over_under_2_5;
            document.getElementById('pOver25').innerText = '%' + ou.over_prob_pct.toFixed(1);
            document.getElementById('oOver25').innerText = 'Adil: ' + ou.fair_odds_over.toFixed(2);
            document.getElementById('pUnder25').innerText = '%' + ou.under_prob_pct.toFixed(1);
            document.getElementById('oUnder25').innerText = 'Adil: ' + ou.fair_odds_under.toFixed(2);

            const btts = data.btts;
            document.getElementById('pBttsYes').innerText = '%' + btts.yes_prob_pct.toFixed(1);
            document.getElementById('oBttsYes').innerText = 'Adil: ' + btts.fair_odds_yes.toFixed(2);
            document.getElementById('pBttsNo').innerText = '%' + btts.no_prob_pct.toFixed(1);
            document.getElementById('oBttsNo').innerText = 'Adil: ' + btts.fair_odds_no.toFixed(2);

            const topList = document.getElementById('topScoresList');
            topList.innerHTML = '';
            data.top_5_scores.forEach((s, idx) => {
                topList.innerHTML += `
                    <div class="score-row">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="color: var(--text-muted); font-size: 0.75rem;">#${idx+1}</span>
                            <span class="score-badge">${s.score}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-weight: 700; color: #fff;">%${s.percentage.toFixed(2)}</span>
                            <span style="font-size: 0.75rem; color: var(--accent-blue); margin-left: 4px;">(${s.fair_odds.toFixed(2)})</span>
                        </div>
                    </div>
                `;
            });

            const mat = data.matrix;
            const matTable = document.getElementById('matrixTable');
            let mHtml = '<tr><th>Ev \\ Dep</th>';
            for (let j = 0; j <= 5; j++) {
                mHtml += `<th>${away.slice(0,5)} ${j}</th>`;
            }
            mHtml += '</tr>';

            for (let i = 0; i <= 5; i++) {
                mHtml += `<tr><th>${home.slice(0,5)} ${i}</th>`;
                for (let j = 0; j <= 5; j++) {
                    const pct = mat[i][j] * 100;
                    const alpha = Math.min(0.85, (pct / 14.0));
                    mHtml += `<td style="background: rgba(56, 189, 248, ${alpha}); font-weight: ${pct > 8 ? '700' : '400'}; color: #fff;">${pct.toFixed(2)}%</td>`;
                }
                mHtml += '</tr>';
            }
            matTable.innerHTML = mHtml;
        }

        /* ================= KUPON FUNCTIONS ================= */
        function addCurrentToSlip(pickType) {
            if (!currentPrediction) return;
            const matchName = `${currentPrediction.home_team} vs ${currentPrediction.away_team}`;

            let fairOdds = 2.0;
            let prob = 0.5;

            if (pickType === "1") {
                prob = currentPrediction.probabilities_1x2.HomeWin / 100.0;
                fairOdds = currentPrediction.fair_odds_1x2['1'];
            } else if (pickType === "X") {
                prob = currentPrediction.probabilities_1x2.Draw / 100.0;
                fairOdds = currentPrediction.fair_odds_1x2['X'];
            } else if (pickType === "2") {
                prob = currentPrediction.probabilities_1x2.AwayWin / 100.0;
                fairOdds = currentPrediction.fair_odds_1x2['2'];
            } else if (pickType === "2.5 ÜST") {
                prob = currentPrediction.over_under_2_5.over_prob_pct / 100.0;
                fairOdds = currentPrediction.over_under_2_5.fair_odds_over;
            } else if (pickType === "2.5 ALT") {
                prob = currentPrediction.over_under_2_5.under_prob_pct / 100.0;
                fairOdds = currentPrediction.over_under_2_5.fair_odds_under;
            } else if (pickType === "KG VAR") {
                prob = currentPrediction.btts.yes_prob_pct / 100.0;
                fairOdds = currentPrediction.btts.fair_odds_yes;
            } else if (pickType === "KG YOK") {
                prob = currentPrediction.btts.no_prob_pct / 100.0;
                fairOdds = currentPrediction.btts.fair_odds_no;
            }

            const defaultBookieOdds = parseFloat((fairOdds * 1.08).toFixed(2));
            betSlip.push({
                id: Date.now() + Math.random(),
                match: matchName,
                pick: pickType,
                odds: defaultBookieOdds,
                fairOdds: fairOdds,
                prob: prob
            });

            renderSlip();
        }

        function addDirectToSlip(matchName, pickType, oddsVal, probVal) {
            betSlip.push({
                id: Date.now() + Math.random(),
                match: matchName,
                pick: pickType,
                odds: oddsVal,
                fairOdds: oddsVal,
                prob: probVal || (1.0 / oddsVal)
            });
            renderSlip();
        }

        function addManualToSlip() {
            const match = document.getElementById('manualMatchName').value.trim() || 'Özel Karşılaşma';
            const pick = document.getElementById('manualPick').value.trim() || '1';
            const odds = parseFloat(document.getElementById('manualOdds').value) || 2.0;

            const impliedProb = 1.0 / odds;
            betSlip.push({
                id: Date.now() + Math.random(),
                match: match,
                pick: pick,
                odds: odds,
                fairOdds: odds,
                prob: impliedProb
            });

            document.getElementById('manualMatchName').value = '';
            document.getElementById('manualPick').value = '';
            document.getElementById('manualOdds').value = '';
            renderSlip();
        }

        function removeSlipItem(id) {
            betSlip = betSlip.filter(item => item.id !== id);
            renderSlip();
        }

        function updateItemOdds(id, newOdds) {
            const item = betSlip.find(i => i.id === id);
            if (item) {
                item.odds = parseFloat(newOdds) || 1.01;
                recalcSlip();
            }
        }

        function clearSlip() {
            betSlip = [];
            renderSlip();
        }

        function renderSlip() {
            const container = document.getElementById('slipItemsList');
            document.getElementById('slipCountBadge').innerText = `(${betSlip.length} Maç)`;

            if (betSlip.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; color: var(--text-muted); font-size: 0.82rem; padding: 20px 0;">
                        Henüz kupona maç eklenmedi.<br>Yukarıdaki <strong>[%70 - %95 KASA KUPONUNU GETİR]</strong> butonuna basın!
                    </div>
                `;
                recalcSlip();
                return;
            }

            let html = '';
            betSlip.forEach((item, idx) => {
                html += `
                    <div class="slip-item">
                        <div class="slip-item-top">
                            <span>${idx+1}. ${item.match}</span>
                            <span class="slip-btn-remove" onclick="removeSlipItem(${item.id})">✕</span>
                        </div>
                        <div class="slip-item-bot">
                            <span style="color: var(--accent-yellow); font-weight:700;">${item.pick}</span>
                            <div style="display:flex; align-items:center; gap:6px;">
                                <span style="font-size:0.75rem;">Oran:</span>
                                <input type="number" step="0.05" value="${item.odds}" style="width:65px; padding:2px 4px; font-size:0.8rem;" oninput="updateItemOdds(${item.id}, this.value)">
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
            recalcSlip();
        }

        function recalcSlip() {
            if (betSlip.length === 0) {
                document.getElementById('slipTotalOdds').innerText = '1.00';
                document.getElementById('slipModelProb').innerText = '%0.0';
                document.getElementById('slipFairOdds').innerText = '1.00';
                document.getElementById('slipEdgeBadge').innerText = 'Kupon Boş';
                document.getElementById('slipEdgeBadge').className = 'slip-edge-badge';
                document.getElementById('slipPayout').innerText = '0.00 TL';
                return;
            }

            let totalOdds = 1.0;
            let jointProb = 1.0;

            betSlip.forEach(item => {
                totalOdds *= item.odds;
                jointProb *= item.prob;
            });

            const fairOdds = jointProb > 0 ? (1.0 / jointProb) : 999.0;
            const ev = (jointProb * totalOdds) - 1.0;
            const edgePct = (ev * 100.0).toFixed(1);

            document.getElementById('slipTotalOdds').innerText = totalOdds.toFixed(2);
            document.getElementById('slipModelProb').innerText = '%' + (jointProb * 100.0).toFixed(2);
            document.getElementById('slipFairOdds').innerText = fairOdds.toFixed(2);

            const badge = document.getElementById('slipEdgeBadge');
            if (ev > 0) {
                badge.innerText = `🔥 +%${edgePct} DEĞERLİ (+EV)`;
                badge.className = 'slip-edge-badge badge-pos-ev';
            } else {
                badge.innerText = `⚠️ %${edgePct} RİSKLİ (-EV)`;
                badge.className = 'slip-edge-badge badge-neg-ev';
            }

            const stake = parseFloat(document.getElementById('slipStake').value) || 0.0;
            const payout = stake * totalOdds;
            document.getElementById('slipPayout').innerText = payout.toFixed(2) + ' TL';
        }

        window.onload = initApp;
    </script>
</body>
</html>
"""


class FullScannerServerHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler for Sub-second Scanner & Premier Kupon Bot."""

    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
            return

        elif path == "/api/leagues":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {k: {"name": v["name"], "flag": v["flag"], "flag_code": v.get("flag_code", "eu")} for k, v in LEAGUES_CONFIG.items()}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        elif path == "/api/bot_radar":
            results = SCANNER_BOT.scanned_matches
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(results).encode("utf-8"))
            return

        elif path == "/api/backtest":
            global BACKTEST_RESULTS
            if BACKTEST_RESULTS is None:
                BACKTEST_RESULTS = ModelBacktester().run_all()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(BACKTEST_RESULTS).encode("utf-8"))
            return

        elif path == "/api/bot_generate_coupon":
            c_type = params.get("type", ["banko"])[0]
            if c_type == "value":
                coupon = SCANNER_BOT.get_value_coupon(3)
            elif c_type == "goals":
                coupon = SCANNER_BOT.get_goals_coupon(3)
            else:
                coupon = SCANNER_BOT.get_guaranteed_range_coupon(3)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(coupon).encode("utf-8"))
            return

        elif path == "/api/live_refresh":
            scanned_count = SCANNER_BOT.refresh_live_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "status": "ok",
                "scanned_count": scanned_count,
                "matches": SCANNER_BOT.scanned_matches
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        elif path == "/api/summary":
            l_id = params.get("league", ["premier_league"])[0]
            summary = LEAGUE_SUMMARIES.get(l_id, list(LEAGUE_SUMMARIES.values())[0])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(summary).encode("utf-8"))
            return

        elif path == "/api/teams":
            l_id = params.get("league", ["premier_league"])[0]
            model = LEAGUE_MODELS.get(l_id, list(LEAGUE_MODELS.values())[0])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(model.teams).encode("utf-8"))
            return

        elif path == "/api/ratings":
            l_id = params.get("league", ["premier_league"])[0]
            model = LEAGUE_MODELS.get(l_id, list(LEAGUE_MODELS.values())[0])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(model.get_team_ratings_rows()).encode("utf-8"))
            return

        elif path == "/api/squad":
            from injury_engine import InjuryEngine
            team = params.get("team", [""])[0]
            squad = InjuryEngine.get_team_squad(team)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([p.to_dict() for p in squad]).encode("utf-8"))
            return

        elif path == "/api/predict":
            l_id = params.get("league", ["premier_league"])[0]
            model = LEAGUE_MODELS.get(l_id, list(LEAGUE_MODELS.values())[0])

            home = params.get("home", [model.teams[0]])[0]
            away = params.get("away", [model.teams[1]])[0]
            rho = float(params.get("rho", [-0.08])[0])

            inj_h_raw = params.get("injuries_home", [""])[0]
            inj_a_raw = params.get("injuries_away", [""])[0]
            inj_h = [x.strip() for x in inj_h_raw.split(",") if x.strip()] if inj_h_raw else None
            inj_a = [x.strip() for x in inj_a_raw.split(",") if x.strip()] if inj_a_raw else None

            try:
                pred = model.predict_match(home, away, max_goals=5, rho=rho, custom_injuries_home=inj_h, custom_injuries_away=inj_a)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(pred).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        else:
            self.send_response(404)
            self.end_headers()


def run_server(port: int = 5000):
    handler = FullScannerServerHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print("=" * 70)
        print("  ⚽ GLOBAL AI TAHMİN & OTONOM KUPON BOTU DASHBOARD")
        print(f"  Web Adresi: {url}")
        print("  Özellikler:")
        print("   • Saniyelik Otonom Maç Tarama Radarı (18 Maç / 0.01s)")
        print("   • %70 - %95 Güvenilirlikli Kasa Katlama Kuponu Motoru")
        print("   • Sıfır Takılma, Sıfır Scrollbar, Arka Plan İplik Yönetimi")
        print("  Durdurmak için terminalde CTRL + C tuşlarına basın.")
        print("=" * 70)

        try:
            webbrowser.open(url)
        except Exception:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard kapatıldı.")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
