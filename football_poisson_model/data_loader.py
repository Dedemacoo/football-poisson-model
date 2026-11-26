"""
Data Loader Module for Football Match Prediction Model
Handles CSV loading, column normalization, data validation, and basic statistics.
Supports both Pandas and pure-Python fallback (for environments where C-extension DLLs
are restricted by OS Application Control / WDAC policies).
"""

from typing import Union, Tuple, Dict, Any, List
import os
import csv

# Attempt to import pandas, fallback to Pure Python if blocked by OS DLL policy
try:
    import pandas as pd
    HAS_PANDAS = True
except BaseException:
    HAS_PANDAS = False
    pd = None


class SimpleSeries:
    """Lightweight pure-python series fallback."""
    def __init__(self, data: List[Any]):
        self.data = data

    def sum(self):
        return sum(self.data)

    def mean(self):
        return sum(self.data) / len(self.data) if self.data else 0.0

    def unique(self):
        return list(dict.fromkeys(self.data))

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


class SimpleDataFrame:
    """Lightweight pure-python DataFrame fallback with essential methods."""
    def __init__(self, records: List[Dict[str, Any]]):
        self.records = records

    def __len__(self):
        return len(self.records)

    def __getitem__(self, col_name: str):
        if isinstance(col_name, str):
            return SimpleSeries([r[col_name] for r in self.records])
        raise KeyError(f"Unsupported key: {col_name}")

    def filter_equal(self, col: str, val: Any) -> "SimpleDataFrame":
        return SimpleDataFrame([r for r in self.records if r.get(col) == val])

    @property
    def columns(self):
        return list(self.records[0].keys()) if self.records else []

    def to_dict_records(self) -> List[Dict[str, Any]]:
        return self.records


class DataLoader:
    """
    Loads, normalizes, and validates football match datasets.
    Supports English (Home, Away, HomeGoals, AwayGoals) and
    Turkish (EvSahibi, Deplasman, EvGol, DepGol) header formats.
    """

    COLUMN_MAPPING = {
        "home": "Home",
        "hometeam": "Home",
        "home_team": "Home",
        "away": "Away",
        "awayteam": "Away",
        "away_team": "Away",
        "fthg": "HomeGoals",
        "homegoals": "HomeGoals",
        "home_goals": "HomeGoals",
        "ftag": "AwayGoals",
        "awaygoals": "AwayGoals",
        "away_goals": "AwayGoals",
        "evsahibi": "Home",
        "ev_sahibi": "Home",
        "ev": "Home",
        "deplasman": "Away",
        "dep": "Away",
        "evgol": "HomeGoals",
        "ev_gol": "HomeGoals",
        "atilangol": "HomeGoals",
        "atilan_gol": "HomeGoals",
        "depgol": "AwayGoals",
        "dep_gol": "AwayGoals",
        "yenilengol": "AwayGoals",
        "yenilen_gol": "AwayGoals",
    }

    REQUIRED_COLS = ["Home", "Away", "HomeGoals", "AwayGoals"]

    @classmethod
    def load(cls, source: Union[str, Any]) -> Any:
        """
        Loads match data. Uses Pandas if available, otherwise pure Python.
        """
        if isinstance(source, str):
            if not os.path.exists(source):
                raise FileNotFoundError(f"Veri dosyası bulunamadı: {source}")

            # Read CSV lines
            records = []
            with open(source, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if not headers:
                    raise ValueError("CSV dosyası boş!")

                # Map headers
                clean_headers = []
                for h in headers:
                    clean = str(h).strip().lower().replace(" ", "_")
                    clean_headers.append(cls.COLUMN_MAPPING.get(clean, h))

                for row in reader:
                    if not row or len(row) < len(clean_headers):
                        continue
                    row_dict = {}
                    for h, val in zip(clean_headers, row):
                        row_dict[h] = val.strip()
                    
                    # Validate row
                    try:
                        home = str(row_dict["Home"]).strip()
                        away = str(row_dict["Away"]).strip()
                        hg = int(row_dict["HomeGoals"])
                        ag = int(row_dict["AwayGoals"])
                        if home and away and home != away and hg >= 0 and ag >= 0:
                            records.append({
                                "Home": home,
                                "Away": away,
                                "HomeGoals": hg,
                                "AwayGoals": ag
                            })
                    except (KeyError, ValueError):
                        continue

            if not records:
                raise ValueError("Yüklenen CSV dosyasında geçerli maç kaydı bulunamadı!")

            if HAS_PANDAS:
                try:
                    return pd.DataFrame(records)
                except Exception:
                    pass
            return SimpleDataFrame(records)

        # If already a DataFrame
        elif HAS_PANDAS and isinstance(source, pd.DataFrame):
            df = source.copy()
            new_cols = {}
            for col in df.columns:
                c = str(col).strip().lower().replace(" ", "_")
                if c in cls.COLUMN_MAPPING:
                    new_cols[col] = cls.COLUMN_MAPPING[c]
            df = df.rename(columns=new_cols)
            return df[cls.REQUIRED_COLS]
        elif isinstance(source, SimpleDataFrame):
            return source
        else:
            raise TypeError("Kaynak bir dosya yolu (str) veya DataFrame olmalıdır.")

    @classmethod
    def get_summary_stats(cls, df: Any) -> Dict[str, Any]:
        """Calculates basic league-wide summary statistics."""
        total_matches = len(df)
        total_home_goals = int(df["HomeGoals"].sum())
        total_away_goals = int(df["AwayGoals"].sum())
        total_goals = total_home_goals + total_away_goals

        avg_home_goals = total_home_goals / total_matches
        avg_away_goals = total_away_goals / total_matches
        avg_total_goals = total_goals / total_matches

        home_goals = list(df["HomeGoals"])
        away_goals = list(df["AwayGoals"])

        home_wins = sum(1 for h, a in zip(home_goals, away_goals) if h > a)
        draws = sum(1 for h, a in zip(home_goals, away_goals) if h == a)
        away_wins = sum(1 for h, a in zip(home_goals, away_goals) if h < a)
        over_2_5 = sum(1 for h, a in zip(home_goals, away_goals) if (h + a) > 2)

        teams_home = set(df["Home"].unique())
        teams_away = set(df["Away"].unique())
        unique_teams = sorted(list(teams_home.union(teams_away)))

        return {
            "total_matches": total_matches,
            "unique_teams_count": len(unique_teams),
            "teams": unique_teams,
            "total_home_goals": total_home_goals,
            "total_away_goals": total_away_goals,
            "total_goals": total_goals,
            "avg_home_goals": avg_home_goals,
            "avg_away_goals": avg_away_goals,
            "avg_total_goals": avg_total_goals,
            "home_win_pct": (home_wins / total_matches) * 100,
            "draw_pct": (draws / total_matches) * 100,
            "away_win_pct": (away_wins / total_matches) * 100,
            "over_2_5_pct": (over_2_5 / total_matches) * 100,
        }
