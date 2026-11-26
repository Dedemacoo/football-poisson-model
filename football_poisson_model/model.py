"""
Poisson & Dixon-Coles Football Match Prediction Model
Calculates team attack/defense ratings, expected goals (lambdas),
bivariate score probability matrices, 1X2 fair odds, Over/Under 2.5,
and value betting / Kelly criterion metrics.

Supports scipy.stats.poisson with automatic pure-math fallback if C-extension DLLs
are blocked by OS Application Control / WDAC policies.
"""

from typing import Dict, Any, List, Tuple, Optional
import math

# Try importing scipy and numpy, fallback to native math functions
try:
    from scipy.stats import poisson as scipy_poisson
    import numpy as np
    HAS_SCIPY = True
except BaseException:
    HAS_SCIPY = False
    scipy_poisson = None
    np = None


def native_poisson_pmf(k: int, lambda_param: float) -> float:
    """
    Exact mathematical Poisson PMF: P(X = k) = (lambda^k * e^(-lambda)) / k!
    Numerically identical to scipy.stats.poisson.pmf(k, lambda).
    """
    if lambda_param <= 0:
        return 1.0 if k == 0 else 0.0
    if k < 0:
        return 0.0
    try:
        return (math.pow(lambda_param, k) * math.exp(-lambda_param)) / math.factorial(k)
    except OverflowError:
        return 0.0


def calculate_poisson_pmf(k: int, lambda_param: float) -> float:
    """Uses scipy if available, otherwise native math."""
    if HAS_SCIPY:
        try:
            return float(scipy_poisson.pmf(k, lambda_param))
        except Exception:
            pass
    return native_poisson_pmf(k, lambda_param)


class FootballPoissonModel:
    """
    Advanced Poisson Distribution and Dixon-Coles model for football match forecasting.
    """

    def __init__(self, default_rho: float = -0.06):
        """
        Args:
            default_rho: Dixon-Coles low-score correlation parameter (typically -0.15 to -0.05).
                         Set to 0.0 for pure independent Poisson.
        """
        self.default_rho = default_rho
        self.is_fitted = False
        self.league_home_avg: float = 0.0
        self.league_away_avg: float = 0.0
        self.league_total_avg: float = 0.0
        self.team_ratings: Dict[str, Dict[str, float]] = {}
        self.teams: List[str] = []
        self.total_matches: int = 0

    def fit(self, df: Any) -> "FootballPoissonModel":
        """
        Calculates league average goals and team-specific attack and defense strength indexes.
        Works with both Pandas DataFrames and SimpleDataFrame.
        """
        self.total_matches = len(df)
        if self.total_matches == 0:
            raise ValueError("Eğitim için boş veri seti verilemez.")

        # 1. League-wide goal averages
        total_h_goals = sum(df["HomeGoals"])
        total_a_goals = sum(df["AwayGoals"])
        self.league_home_avg = total_h_goals / self.total_matches
        self.league_away_avg = total_a_goals / self.total_matches
        self.league_total_avg = (total_h_goals + total_a_goals) / self.total_matches

        # Prevent zero division
        if self.league_home_avg <= 0:
            self.league_home_avg = 1.0
        if self.league_away_avg <= 0:
            self.league_away_avg = 1.0

        # Unique teams
        home_teams = set(df["Home"].unique())
        away_teams = set(df["Away"].unique())
        self.teams = sorted(list(home_teams.union(away_teams)))

        # Extract all records
        if hasattr(df, "to_dict_records"):
            records = df.to_dict_records()
        elif hasattr(df, "to_dict"):
            records = df.to_dict(orient="records")
        else:
            records = [
                {"Home": h, "Away": a, "HomeGoals": hg, "AwayGoals": ag}
                for h, a, hg, ag in zip(df["Home"], df["Away"], df["HomeGoals"], df["AwayGoals"])
            ]

        # Aggregate stats per team
        ratings = {}
        for team in self.teams:
            home_games = [r for r in records if r["Home"] == team]
            away_games = [r for r in records if r["Away"] == team]

            n_home = len(home_games)
            n_away = len(away_games)

            # Home Attack & Defense
            if n_home > 0:
                h_scored = sum(r["HomeGoals"] for r in home_games)
                h_conceded = sum(r["AwayGoals"] for r in home_games)
                h_scored_avg = h_scored / n_home
                h_conceded_avg = h_conceded / n_home
                home_attack = h_scored_avg / self.league_home_avg
                home_defense = h_conceded_avg / self.league_away_avg
            else:
                home_attack = 1.0
                home_defense = 1.0

            # Away Attack & Defense
            if n_away > 0:
                a_scored = sum(r["AwayGoals"] for r in away_games)
                a_conceded = sum(r["HomeGoals"] for r in away_games)
                a_scored_avg = a_scored / n_away
                a_conceded_avg = a_conceded / n_away
                away_attack = a_scored_avg / self.league_away_avg
                away_defense = a_conceded_avg / self.league_home_avg
            else:
                away_attack = 1.0
                away_defense = 1.0

            ratings[team] = {
                "home_matches": n_home,
                "away_matches": n_away,
                "total_matches": n_home + n_away,
                "home_attack": round(home_attack, 4),
                "home_defense": round(home_defense, 4),
                "away_attack": round(away_attack, 4),
                "away_defense": round(away_defense, 4),
                "overall_attack": round((home_attack + away_attack) / 2.0, 4),
                "overall_defense": round((home_defense + away_defense) / 2.0, 4),
            }

        self.team_ratings = ratings
        self.is_fitted = True
        return self

    def get_team_ratings_rows(self) -> List[Dict[str, Any]]:
        """Returns list of team rating dictionaries sorted by overall strength."""
        if not self.is_fitted:
            raise RuntimeError("Model henüz eğitilmedi. Lütfen önce .fit(df) çalıştırın.")

        rows = []
        for team, stats in self.team_ratings.items():
            power = round(stats["overall_attack"] / (stats["overall_defense"] + 1e-6), 2)
            rows.append({
                "Takım": team,
                "Maç": stats["total_matches"],
                "Ev Hücum": f"{stats['home_attack']:.2f}",
                "Ev Savunma": f"{stats['home_defense']:.2f}",
                "Dep Hücum": f"{stats['away_attack']:.2f}",
                "Dep Savunma": f"{stats['away_defense']:.2f}",
                "Genel Güç": power
            })
        rows.sort(key=lambda x: x["Genel Güç"], reverse=True)
        return rows

    def get_team_ratings_df(self) -> Any:
        """Returns DataFrame if pandas available, else list of dicts."""
        rows = self.get_team_ratings_rows()
        try:
            import pandas as pd
            return pd.DataFrame(rows)
        except Exception:
            return rows

    def resolve_team_name(self, raw_name: str) -> Optional[str]:
        """
        Resolves team name using exact matching, normalization (case, accents, suffixes),
        common football club aliases, and substring search.
        """
        if not self.is_fitted or not self.team_ratings:
            return None
        if raw_name in self.team_ratings:
            return raw_name

        def clean(s: str) -> str:
            s = s.lower().strip()
            # Turkish and European accents normalization
            trans = {
                "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
                "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n",
                "ã": "a", "õ": "o", "â": "a", "ê": "e", "î": "i", "ô": "o"
            }
            for k, v in trans.items():
                s = s.replace(k, v)
            for suffix in [" fc", " fk", " sk", " a.ş.", " a.s.", " kulübü", " kulubu", " cf", " cd", " afc"]:
                if s.endswith(suffix):
                    s = s[:-len(suffix)].strip()
            return s.strip()

        # Known common aliases map
        ALIASES = {
            "manchester city": ["man city", "mancity"],
            "manchester united": ["man united", "man utd"],
            "nottingham forest": ["nott'm forest", "nottingham"],
            "tottenham hotspur": ["tottenham", "spurs"],
            "wolverhampton wanderers": ["wolves", "wolverhampton"],
            "brighton & hove albion": ["brighton", "brighton and hove"],
            "newcastle united": ["newcastle"],
            "west ham united": ["west ham"],
            "atletico madrid": ["atlético madrid", "atl madrid"],
            "athletic club": ["athletic bilbao", "ath bilbao"],
            "paris saint-germain": ["psg", "paris sg"],
            "bayern munich": ["bayern münchen", "bayern"],
            "borussia dortmund": ["dortmund", "bvb"],
            "borussia mönchengladbach": ["m'gladbach", "monchengladbach", "borussia monchengladbach"],
            "bayer leverkusen": ["leverkusen"],
            "inter milan": ["inter", "internazionale"],
            "ac milan": ["milan"],
            "sporting cp": ["sporting", "sporting lisbon"],
            "galatasaray": ["galatasaray a.s.", "gs"],
            "fenerbahce": ["fenerbahce sk", "fb"],
            "besiktas": ["besiktas jk", "bjk"],
            "trabzonspor": ["trabzonspor a.s.", "ts"]
        }

        c_raw = clean(raw_name)

        # Check existing teams after clean
        for existing in self.team_ratings:
            if c_raw == clean(existing):
                return existing

        # Check aliases
        for canonical, alias_list in ALIASES.items():
            all_names = [canonical] + alias_list
            if any(clean(a) == c_raw for a in all_names):
                for existing in self.team_ratings:
                    if clean(existing) in [clean(a) for a in all_names]:
                        return existing

        # Substring / partial word match
        for existing in self.team_ratings:
            c_ex = clean(existing)
            if len(c_raw) >= 4 and len(c_ex) >= 4:
                if c_raw in c_ex or c_ex in c_raw:
                    return existing

        return None

    def calculate_expected_goals(self, home_team: str, away_team: str) -> Tuple[float, float]:
        """
        Derives lambda_home and lambda_away for a given matchup.
        Formula:
          lambda_home = Home_Attack(home) * Away_Defense(away) * League_Home_Avg
          lambda_away = Away_Attack(away) * Home_Defense(home) * League_Away_Avg
        Gracefully resolves team name aliases and uses baseline ratings for newly-promoted/unknown teams.
        """
        if not self.is_fitted:
            raise RuntimeError("Model eğitilmeden tahmin yapılamaz.")

        h_resolved = self.resolve_team_name(home_team)
        a_resolved = self.resolve_team_name(away_team)

        # Baseline ratings for unknown / promoted teams relative to the league
        default_home_stats = {
            "home_attack": 0.88,
            "home_defense": 1.12,
            "away_attack": 0.78,
            "away_defense": 1.22
        }
        default_away_stats = {
            "home_attack": 0.82,
            "home_defense": 1.18,
            "away_attack": 0.74,
            "away_defense": 1.26
        }

        home_stats = self.team_ratings.get(h_resolved, default_home_stats) if h_resolved else default_home_stats
        away_stats = self.team_ratings.get(a_resolved, default_away_stats) if a_resolved else default_away_stats

        lambda_home = home_stats["home_attack"] * away_stats["away_defense"] * self.league_home_avg
        lambda_away = away_stats["away_attack"] * home_stats["home_defense"] * self.league_away_avg

        lambda_home = max(0.15, float(lambda_home))
        lambda_away = max(0.15, float(lambda_away))

        return round(lambda_home, 4), round(lambda_away, 4)

    @staticmethod
    def _dixon_coles_tau(x: int, y: int, lambda_h: float, lambda_a: float, rho: float) -> float:
        """
        Dixon-Coles adjustment factor tau(x, y, lambda_h, lambda_a, rho)
        Corrects correlation for low scoring results (0-0, 1-0, 0-1, 1-1).
        """
        if rho == 0.0:
            return 1.0

        if x == 0 and y == 0:
            return max(0.0, 1.0 - (lambda_h * lambda_a * rho))
        elif x == 0 and y == 1:
            return max(0.0, 1.0 + (lambda_h * rho))
        elif x == 1 and y == 0:
            return max(0.0, 1.0 + (lambda_a * rho))
        elif x == 1 and y == 1:
            return max(0.0, 1.0 - rho)
        else:
            return 1.0

    def generate_score_matrix(
        self,
        lambda_home: float,
        lambda_away: float,
        max_goals: int = 5,
        rho: Optional[float] = None
    ) -> List[List[float]]:
        """
        Generates a bivariate probability matrix of shape (max_goals + 1, max_goals + 1).
        By default, max_goals=5 yields a 6x6 matrix (scores 0 to 5 for each team).
        Uses scipy.stats.poisson (or exact native equivalent) and applies Dixon-Coles tau.
        """
        if rho is None:
            rho = self.default_rho

        matrix_size = max_goals + 1
        matrix = [[0.0 for _ in range(matrix_size)] for _ in range(matrix_size)]

        p_home = [calculate_poisson_pmf(i, lambda_home) for i in range(matrix_size)]
        p_away = [calculate_poisson_pmf(j, lambda_away) for j in range(matrix_size)]

        total_grid_prob = 0.0
        for i in range(matrix_size):
            for j in range(matrix_size):
                tau = self._dixon_coles_tau(i, j, lambda_home, lambda_away, rho)
                val = tau * p_home[i] * p_away[j]
                matrix[i][j] = val
                total_grid_prob += val

        # Normalize matrix so grid probabilities sum to 1.0
        if total_grid_prob > 0:
            for i in range(matrix_size):
                for j in range(matrix_size):
                    matrix[i][j] /= total_grid_prob

        return matrix

    def predict_match(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = 5,
        rho: Optional[float] = None,
        custom_injuries_home: Optional[List[str]] = None,
        custom_injuries_away: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive prediction engine for a given match.
        Incorporates real-world squad injuries, star player impact ratings,
        and generates AI Tactical Insights.
        """
        base_lambda_h, base_lambda_a = self.calculate_expected_goals(home_team, away_team)

        # Apply Injury & Squad Intelligence
        from injury_engine import InjuryEngine
        h_att_pen, h_def_pen, h_inj_list = InjuryEngine.calculate_squad_penalties(home_team, custom_injuries_home)
        a_att_pen, a_def_pen, a_inj_list = InjuryEngine.calculate_squad_penalties(away_team, custom_injuries_away)

        # Adjusted lambdas:
        # If home has attack penalty -> lambda_home decreases
        # If away has defense penalty -> away concedes more -> lambda_home increases
        adj_lambda_h = base_lambda_h * (1.0 - h_att_pen) * (1.0 + a_def_pen)
        adj_lambda_a = base_lambda_a * (1.0 - a_att_pen) * (1.0 + h_def_pen)

        lambda_home = max(0.15, round(adj_lambda_h, 4))
        lambda_away = max(0.15, round(adj_lambda_a, 4))

        matrix = self.generate_score_matrix(lambda_home, lambda_away, max_goals=max_goals, rho=rho)

        # Generate tactical insights
        ai_insights = InjuryEngine.generate_ai_insights(
            home_team, away_team, h_inj_list, a_inj_list,
            round(lambda_home - base_lambda_h, 2), round(lambda_away - base_lambda_a, 2)
        )

        # 1. Match Outcome 1X2 Probabilities
        prob_home_win = 0.0
        prob_draw = 0.0
        prob_away_win = 0.0

        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                p = matrix[i][j]
                if i > j:
                    prob_home_win += p
                elif i == j:
                    prob_draw += p
                else:
                    prob_away_win += p

        # Fair odds calculation (1 / probability)
        fair_odds_home = round(1.0 / prob_home_win, 2) if prob_home_win > 0 else 999.0
        fair_odds_draw = round(1.0 / prob_draw, 2) if prob_draw > 0 else 999.0
        fair_odds_away = round(1.0 / prob_away_win, 2) if prob_away_win > 0 else 999.0

        # Double Chance
        prob_1x = prob_home_win + prob_draw
        prob_x2 = prob_draw + prob_away_win
        prob_12 = prob_home_win + prob_away_win

        fair_odds_1x = round(1.0 / prob_1x, 2) if prob_1x > 0 else 999.0
        fair_odds_x2 = round(1.0 / prob_x2, 2) if prob_x2 > 0 else 999.0
        fair_odds_12 = round(1.0 / prob_12, 2) if prob_12 > 0 else 999.0

        # 2. Top 5 Most Likely Scores
        score_candidates = []
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                p = matrix[i][j]
                score_candidates.append({
                    "score": f"{i}-{j}",
                    "home_goals": i,
                    "away_goals": j,
                    "probability": p,
                    "percentage": round(p * 100, 2),
                    "fair_odds": round(1.0 / p, 2) if p > 0 else 999.0
                })

        score_candidates.sort(key=lambda x: x["probability"], reverse=True)
        top_5_scores = score_candidates[:5]

        # 3. 2.5 Goals Over / Under
        prob_under_2_5 = sum(
            matrix[i][j]
            for i in range(max_goals + 1)
            for j in range(max_goals + 1)
            if i + j <= 2
        )
        prob_over_2_5 = max(0.0, 1.0 - prob_under_2_5)

        fair_odds_under_2_5 = round(1.0 / prob_under_2_5, 2) if prob_under_2_5 > 0 else 999.0
        fair_odds_over_2_5 = round(1.0 / prob_over_2_5, 2) if prob_over_2_5 > 0 else 999.0

        # 4. Both Teams to Score (KG Var / Yok)
        prob_btts_no = 0.0
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                if i == 0 or j == 0:
                    prob_btts_no += matrix[i][j]
        prob_btts_yes = max(0.0, 1.0 - prob_btts_no)

        fair_odds_btts_yes = round(1.0 / prob_btts_yes, 2) if prob_btts_yes > 0 else 999.0
        fair_odds_btts_no = round(1.0 / prob_btts_no, 2) if prob_btts_no > 0 else 999.0

        return {
            "home_team": home_team,
            "away_team": away_team,
            "lambda_home": lambda_home,
            "lambda_away": lambda_away,
            "expected_total_goals": round(lambda_home + lambda_away, 2),
            "probabilities_1x2": {
                "HomeWin": round(prob_home_win * 100, 2),
                "Draw": round(prob_draw * 100, 2),
                "AwayWin": round(prob_away_win * 100, 2)
            },
            "fair_odds_1x2": {
                "1": fair_odds_home,
                "X": fair_odds_draw,
                "2": fair_odds_away
            },
            "double_chance": {
                "1X": {"prob_pct": round(prob_1x * 100, 2), "fair_odds": fair_odds_1x},
                "X2": {"prob_pct": round(prob_x2 * 100, 2), "fair_odds": fair_odds_x2},
                "12": {"prob_pct": round(prob_12 * 100, 2), "fair_odds": fair_odds_12},
            },
            "top_5_scores": top_5_scores,
            "over_under_2_5": {
                "under_prob_pct": round(prob_under_2_5 * 100, 2),
                "over_prob_pct": round(prob_over_2_5 * 100, 2),
                "fair_odds_under": fair_odds_under_2_5,
                "fair_odds_over": fair_odds_over_2_5
            },
            "btts": {
                "yes_prob_pct": round(prob_btts_yes * 100, 2),
                "no_prob_pct": round(prob_btts_no * 100, 2),
                "fair_odds_yes": fair_odds_btts_yes,
                "fair_odds_no": fair_odds_btts_no
            },
            "matrix": matrix,
            "max_goals": max_goals,
            "injury_analysis": {
                "base_lambda_home": base_lambda_h,
                "base_lambda_away": base_lambda_a,
                "home_injuries": h_inj_list,
                "away_injuries": a_inj_list,
                "home_attack_penalty_pct": round(h_att_pen * 100, 1),
                "away_attack_penalty_pct": round(a_att_pen * 100, 1),
                "ai_insights": ai_insights
            }
        }

    @staticmethod
    def calculate_value_edge(model_prob: float, bookmaker_odds: float) -> Dict[str, Any]:
        """
        Quantitative Value Betting & Kelly Criterion Analysis.
        Calculates whether a bookmaker quote offers positive expected value (+EV).
        """
        if bookmaker_odds <= 1.0 or model_prob <= 0.0:
            return {
                "is_value": False,
                "edge_pct": 0.0,
                "kelly_stake_pct": 0.0,
                "quarter_kelly_pct": 0.0,
                "explanation": "Geçersiz oran veya olasılık."
            }

        implied_prob = 1.0 / bookmaker_odds
        ev = (model_prob * bookmaker_odds) - 1.0
        edge_pct = ev * 100.0

        b = bookmaker_odds - 1.0
        p = model_prob
        q = 1.0 - p

        # Kelly fraction: f* = (bp - q) / b
        kelly_fraction = (b * p - q) / b
        kelly_stake_pct = max(0.0, kelly_fraction * 100.0)
        quarter_kelly_pct = kelly_stake_pct / 4.0

        is_value = ev > 0.0

        return {
            "model_prob_pct": round(model_prob * 100, 2),
            "implied_prob_pct": round(implied_prob * 100, 2),
            "bookmaker_odds": bookmaker_odds,
            "fair_odds": round(1.0 / model_prob, 2),
            "is_value": is_value,
            "edge_pct": round(edge_pct, 2),
            "kelly_stake_pct": round(kelly_stake_pct, 2),
            "quarter_kelly_pct": round(quarter_kelly_pct, 2),
        }
