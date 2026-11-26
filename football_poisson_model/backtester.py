"""
Quantitative Backtesting & Model Accuracy Verification Engine
Performs out-of-sample walk-forward historical validation across all leagues.
Splits matches into Train (earlier matches) and Test (recent played matches),
predicts unseen match results, and verifies actual hit rates (70% - 95% target).
"""

import os
import sys
from typing import Dict, Any, List, Tuple
from tabulate import tabulate

from data_loader import DataLoader
from model import FootballPoissonModel

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")


class ModelBacktester:
    """
    Simulates real-world quantitative performance using chronological out-of-sample testing.
    """

    def __init__(self, data_directory: str = DATA_DIR):
        self.data_directory = data_directory

    def backtest_league(self, league_name: str, csv_path: str, train_ratio: float = 0.70) -> Dict[str, Any]:
        """
        Backtests a specific league:
        - Trains model on first 70% of matches.
        - Evaluates predictions on remaining 30% unseen recent matches.
        """
        if not os.path.exists(csv_path):
            return None

        # Load raw records
        raw_df = DataLoader.load(csv_path)
        if hasattr(raw_df, "to_dict_records"):
            records = raw_df.to_dict_records()
        else:
            records = [
                {"Home": h, "Away": a, "HomeGoals": hg, "AwayGoals": ag}
                for h, a, hg, ag in zip(raw_df["Home"], raw_df["Away"], raw_df["HomeGoals"], raw_df["AwayGoals"])
            ]

        total_matches = len(records)
        split_idx = int(total_matches * train_ratio)

        train_records = records[:split_idx]
        test_records = records[split_idx:]

        if len(test_records) == 0:
            return None

        # Train model ONLY on training matches (zero lookahead bias)
        from data_loader import SimpleDataFrame
        train_df = SimpleDataFrame(train_records)

        model = FootballPoissonModel(default_rho=-0.08)
        model.fit(train_df)

        # Evaluate on unseen recent test matches
        high_conf_hits = 0
        high_conf_total = 0

        dc_hits = 0
        dc_total = 0

        ou_hits = 0
        ou_total = 0

        match_outcome_hits = 0
        match_outcome_total = 0

        detailed_logs = []

        for match in test_records:
            h = match["Home"]
            a = match["Away"]
            act_hg = match["HomeGoals"]
            act_ag = match["AwayGoals"]

            # Must exist in training model
            if h not in model.team_ratings or a not in model.team_ratings:
                continue

            try:
                pred = model.predict_match(h, a, max_goals=5, rho=-0.08)
            except Exception:
                continue

            # Actual match outcomes
            act_home_win = act_hg > act_ag
            act_draw = act_hg == act_ag
            act_away_win = act_hg < act_ag
            act_under_25 = (act_hg + act_ag) <= 2
            act_over_25 = not act_under_25
            act_btts = (act_hg > 0) and (act_ag > 0)

            # 1. High-Confidence Pick Evaluation (Target: 70% - 95% threshold)
            # Find candidate with highest model probability
            candidates = [
                {"pick": "1X", "prob": pred["double_chance"]["1X"]["prob_pct"], "won": (act_home_win or act_draw)},
                {"pick": "X2", "prob": pred["double_chance"]["X2"]["prob_pct"], "won": (act_draw or act_away_win)},
                {"pick": "12", "prob": pred["double_chance"]["12"]["prob_pct"], "won": (act_home_win or act_away_win)},
                {"pick": "2.5 ALT", "prob": pred["over_under_2_5"]["under_prob_pct"], "won": act_under_25},
                {"pick": "2.5 ÜST", "prob": pred["over_under_2_5"]["over_prob_pct"], "won": act_over_25},
                {"pick": "1 (Ev)", "prob": pred["probabilities_1x2"]["HomeWin"], "won": act_home_win},
                {"pick": "2 (Dep)", "prob": pred["probabilities_1x2"]["AwayWin"], "won": act_away_win},
            ]
            candidates.sort(key=lambda x: x["prob"], reverse=True)
            top_pick = candidates[0]

            # We measure when the model assigns high confidence (>= 72%)
            if top_pick["prob"] >= 72.0:
                high_conf_total += 1
                if top_pick["won"]:
                    high_conf_hits += 1

            # 2. Double Chance Best Pick
            best_dc = max([
                {"pick": "1X", "prob": pred["double_chance"]["1X"]["prob_pct"], "won": (act_home_win or act_draw)},
                {"pick": "X2", "prob": pred["double_chance"]["X2"]["prob_pct"], "won": (act_draw or act_away_win)}
            ], key=lambda x: x["prob"])
            dc_total += 1
            if best_dc["won"]:
                dc_hits += 1

            # 3. 2.5 Over / Under Best Pick
            ou_pick = "ALT" if pred["over_under_2_5"]["under_prob_pct"] > pred["over_under_2_5"]["over_prob_pct"] else "ÜST"
            ou_won = act_under_25 if ou_pick == "ALT" else act_over_25
            ou_total += 1
            if ou_won:
                ou_hits += 1

            # 4. Outright 1X2 Highest Probability Pick
            p_1x2 = pred["probabilities_1x2"]
            if p_1x2["HomeWin"] >= p_1x2["AwayWin"] and p_1x2["HomeWin"] >= p_1x2["Draw"]:
                pred_1x2 = "1"
                won_1x2 = act_home_win
            elif p_1x2["AwayWin"] >= p_1x2["HomeWin"] and p_1x2["AwayWin"] >= p_1x2["Draw"]:
                pred_1x2 = "2"
                won_1x2 = act_away_win
            else:
                pred_1x2 = "X"
                won_1x2 = act_draw

            match_outcome_total += 1
            if won_1x2:
                match_outcome_hits += 1

            detailed_logs.append({
                "match": f"{h} vs {a}",
                "score": f"{act_hg}-{act_ag}",
                "best_pick": top_pick["pick"],
                "model_prob": f"%{top_pick['prob']:.1f}",
                "result": "✅ TUTTU" if top_pick["won"] else "❌ YATTI"
            })

        high_conf_acc = (high_conf_hits / high_conf_total * 100.0) if high_conf_total > 0 else 0.0
        dc_acc = (dc_hits / dc_total * 100.0) if dc_total > 0 else 0.0
        ou_acc = (ou_hits / ou_total * 100.0) if ou_total > 0 else 0.0

        return {
            "league_name": league_name,
            "train_matches": len(train_records),
            "test_matches": len(test_records),
            "evaluated_matches": match_outcome_total,
            "high_conf_total": high_conf_total,
            "high_conf_hits": high_conf_hits,
            "high_conf_accuracy": round(high_conf_acc, 2),
            "dc_accuracy": round(dc_acc, 2),
            "ou_accuracy": round(ou_acc, 2),
            "logs": detailed_logs
        }

    def run_all(self) -> Dict[str, Any]:
        """Runs backtest across all available league datasets."""
        leagues = {
            "İngiltere Premier League": os.path.join(self.data_directory, "premier_league.csv"),
            "İspanya La Liga": os.path.join(self.data_directory, "la_liga.csv"),
            "İtalya Serie A": os.path.join(self.data_directory, "serie_a.csv"),
            "Almanya Bundesliga": os.path.join(self.data_directory, "bundesliga.csv"),
            "Fransa Ligue 1": os.path.join(self.data_directory, "ligue_1.csv"),
            "Türkiye Süper Lig": os.path.join(self.data_directory, "super_lig.csv"),
            "İran Pro Ligi": os.path.join(self.data_directory, "iran.csv"),
            "Arjantin Primera": os.path.join(self.data_directory, "argentina.csv"),
            "UEFA Şampiyonlar Ligi": os.path.join(self.data_directory, "champions_league.csv")
        }

        league_results = []
        tot_high_conf_hits = 0
        tot_high_conf_attempts = 0
        tot_test_matches = 0

        for name, path in leagues.items():
            res = self.backtest_league(name, path)
            if res:
                league_results.append(res)
                tot_high_conf_hits += res["high_conf_hits"]
                tot_high_conf_attempts += res["high_conf_total"]
                tot_test_matches += res["evaluated_matches"]

        overall_high_conf_acc = (tot_high_conf_hits / tot_high_conf_attempts * 100.0) if tot_high_conf_attempts > 0 else 0.0

        return {
            "leagues": league_results,
            "total_test_matches": tot_test_matches,
            "total_high_conf_attempts": tot_high_conf_attempts,
            "total_high_conf_hits": tot_high_conf_hits,
            "overall_high_conf_accuracy": round(overall_high_conf_acc, 2)
        }


def print_backtest_report():
    backtester = ModelBacktester()
    results = backtester.run_all()

    print("\n" + "=" * 80)
    print("      🧪 AI FUTBOL POISSON & DIXON-COLES MODEL DOĞRULAMA (BACKTEST) RAPORU")
    print("      (Yalnızca Geçmiş Maçlar Üzerinden Eğitilmiş, Son Haftalarda Test Edilmiştir)")
    print("=" * 80)

    table_data = []
    for r in results["leagues"]:
        table_data.append([
            r["league_name"],
            f"{r['train_matches']} Maç",
            f"{r['test_matches']} Maç",
            f"{r['high_conf_hits']} / {r['high_conf_total']}",
            f"%{r['high_conf_accuracy']:.1f}",
            f"%{r['dc_accuracy']:.1f}",
            f"%{r['ou_accuracy']:.1f}"
        ])

    headers = [
        "Lig",
        "Eğitim Verisi",
        "Test (Son Haftalar)",
        "Yüksek Güvenilirlik",
        "Model Başarısı (%70-%95)",
        "Çifte Şans",
        "2.5 Alt/Üst"
    ]
    print(tabulate(table_data, headers=headers, tablefmt="rounded_grid"))

    print("\n" + "-" * 80)
    print("  GENEL DOĞRULAMA VE BAŞARI ÖZETİ:")
    print(f"  • Toplam Test Edilen Gerçek Karşılaşma  : {results['total_test_matches']} Maç")
    print(f"  • Yüksek Güvenilirlikli (%70-%95) Bahisler: {results['total_high_conf_attempts']} Tercih")
    print(f"  • Doğrulanan Başarılı Tahmin (Hit)     : {results['total_high_conf_hits']} İsabet")
    print(f"  • GENEL GERÇEKLEŞEN BAŞARI ORANI       : %{results['overall_high_conf_accuracy']:.2f}")
    print("-" * 80)

    if 70.0 <= results['overall_high_conf_accuracy'] <= 95.0:
        print("  ✅ DOĞRULAMA BAŞARILI: Model, hedeflenen %70 - %95 doğruluk bandını tam karşılamaktadır!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    print_backtest_report()
