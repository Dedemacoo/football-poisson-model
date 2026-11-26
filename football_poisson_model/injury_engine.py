"""
Player Intelligence & Injury Impact Analysis Engine
Tracks star players, injury/suspension statuses, player impact ratings (1-10),
and computes dynamic expected goal (lambda) penalties on attack and defense.
Answers: 'Does missing player X drastically change coupon success probability?'
"""

from typing import Dict, Any, List, Optional, Tuple


class Player:
    def __init__(self, name: str, position: str, impact_score: float, role_desc: str, attack_penalty: float = 0.0, defense_penalty: float = 0.0):
        self.name = name
        self.position = position  # Forvet, Orta Saha, Stoper, Kaleci
        self.impact_score = impact_score  # 1.0 - 10.0
        self.role_desc = role_desc
        self.attack_penalty = attack_penalty  # % reduction in attack power when missing
        self.defense_penalty = defense_penalty  # % increase in defensive vulnerability when missing
        self.is_injured = False
        self.injury_reason = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "position": self.position,
            "impact_score": self.impact_score,
            "role_desc": self.role_desc,
            "attack_penalty_pct": round(self.attack_penalty * 100, 1),
            "defense_penalty_pct": round(self.defense_penalty * 100, 1),
            "is_injured": self.is_injured,
            "injury_reason": self.injury_reason
        }


# Comprehensive Key Players Database across World & Turkish Football
SQUADS_DATABASE: Dict[str, List[Player]] = {
    # Türkiye Süper Lig
    "galatasaray": [
        Player("Victor Osimhen", "Forvet", 9.4, "Dünya Çapında Golcü • As Forvet", attack_penalty=0.18),
        Player("Mauro Icardi", "Forvet", 9.0, "Kilit Bitirici • Ceza Sahası Lideri", attack_penalty=0.15),
        Player("Fernando Muslera", "Kaleci", 8.6, "Kaptan & 1. Kaleci", defense_penalty=0.14),
        Player("Lucas Torreira", "Orta Saha", 8.4, "Orta Saha Çapası & Pres Motoru", defense_penalty=0.10, attack_penalty=0.04),
        Player("Davinson Sánchez", "Stoper", 8.5, "Savunma Lideri & Hızlı Stoper", defense_penalty=0.12),
        Player("Barış Alper Yılmaz", "Kanat/Forvet", 8.2, "Dinamik Hücum Gücü", attack_penalty=0.08)
    ],
    "fenerbahce": [
        Player("Edin Dzeko", "Forvet", 8.7, "Takım Kaptanı & Hedef Santrfor", attack_penalty=0.14),
        Player("Youssef En-Nesyri", "Forvet", 8.5, "Ana Bitirici & Hava Topu Hakimi", attack_penalty=0.12),
        Player("Dusan Tadic", "Forvet/Kanat", 8.8, "Oyun Kurucu & Asist Lideri", attack_penalty=0.14),
        Player("Fred", "Orta Saha", 8.6, "Geçiş Oyunu Motoru (Kritik Eksik)", attack_penalty=0.10, defense_penalty=0.08),
        Player("Dominik Livakovic", "Kaleci", 8.4, "1. Kaleci & Milli Kaleci", defense_penalty=0.11),
        Player("Alexander Djiku", "Stoper", 8.2, "Defans Lideri", defense_penalty=0.10)
    ],
    "besiktas": [
        Player("Ciro Immobile", "Forvet", 8.8, "Altın Ayakkabılı Baş Santrfor", attack_penalty=0.18),
        Player("Rafa Silva", "Hücum/Orta", 9.0, "Takımın Yaratıcı Beyni", attack_penalty=0.16),
        Player("Gedson Fernandes", "Orta Saha", 8.4, "Box-to-box Dinamo", attack_penalty=0.07, defense_penalty=0.08),
        Player("Gabriel Paulista", "Stoper", 8.3, "Savunma Belkemiği", defense_penalty=0.13),
        Player("Mert Günok", "Kaleci", 8.2, "Milli Kaleci", defense_penalty=0.10)
    ],
    "trabzonspor": [
        Player("Simon Banza", "Forvet", 8.3, "As Santrfor & Skorer", attack_penalty=0.16),
        Player("Edin Visca", "Kanat", 8.2, "Asist & Duran Top Ustası", attack_penalty=0.11),
        Player("Uğurcan Çakır", "Kaleci", 8.7, "Kaptan & Kurtarıcı Kaleci", defense_penalty=0.16),
        Player("Stefan Savic", "Stoper", 8.2, "Tecrübeli Defans Hattı", defense_penalty=0.12)
    ],
    # İngiltere Premier League
    "manchester city": [
        Player("Erling Haaland", "Forvet", 9.8, "Dünyanın En Tehlikeli Santrforu", attack_penalty=0.22),
        Player("Kevin De Bruyne", "Orta Saha", 9.5, "Dünyanın En İyi Oyun Kurucusu", attack_penalty=0.16),
        Player("Rodri", "Ön Libero", 9.6, "Ballon d'Or Sahibi • Sistem Anahtarı", defense_penalty=0.14, attack_penalty=0.08),
        Player("Phil Foden", "Kanat/Orta", 8.9, "Yılın Oyuncusu", attack_penalty=0.10),
        Player("Rúben Dias", "Stoper", 9.0, "Savunma Komutanı", defense_penalty=0.13),
        Player("Ederson", "Kaleci", 8.8, "1. Kaleci & Ayak Hakimiyeti", defense_penalty=0.09)
    ],
    "arsenal": [
        Player("Bukayo Saka", "Kanat/Forvet", 9.4, "Hücumun 1 Numaralı Tehdidi", attack_penalty=0.18),
        Player("Martin Ødegaard", "Orta Saha", 9.2, "Kaptan & Kreatif Merkez", attack_penalty=0.15),
        Player("William Saliba", "Stoper", 9.1, "Geçilmez Stoper Lideri", defense_penalty=0.16),
        Player("Declan Rice", "Orta Saha", 9.0, "Orta Saha Kalkanı", defense_penalty=0.11, attack_penalty=0.05),
        Player("David Raya", "Kaleci", 8.7, "Altın Eldiven", defense_penalty=0.10)
    ],
    "liverpool": [
        Player("Mohamed Salah", "Forvet", 9.6, "Süperstar & Baş Golcü", attack_penalty=0.20),
        Player("Virgil van Dijk", "Stoper", 9.3, "Dünya Çapında Defans Lideri", defense_penalty=0.17),
        Player("Alisson Becker", "Kaleci", 9.0, "Dünyanın En İyi Kalecilerinden", defense_penalty=0.14),
        Player("Alexis Mac Allister", "Orta Saha", 8.7, "Oyun Yönlendirici", attack_penalty=0.07, defense_penalty=0.07)
    ],
    "chelsea": [
        Player("Cole Palmer", "Hücum/Kanat", 9.4, "Takımın Tek Başına Hücum Gücü", attack_penalty=0.22),
        Player("Nicolas Jackson", "Forvet", 8.2, "As Forvet", attack_penalty=0.10),
        Player("Moisés Caicedo", "Ön Libero", 8.6, "Orta Saha Süpürücüsü", defense_penalty=0.12)
    ],
    # İspanya La Liga
    "real madrid": [
        Player("Vinícius Júnior", "Kanat/Forvet", 9.7, "Süperstar & Hız Tehdidi", attack_penalty=0.20),
        Player("Kylian Mbappé", "Forvet", 9.7, "Dünyanın En Hızlı Bitiricisi", attack_penalty=0.20),
        Player("Jude Bellingham", "Orta Saha", 9.3, "Ceza Sahası Koşucusu", attack_penalty=0.14, defense_penalty=0.06),
        Player("Thibaut Courtois", "Kaleci", 9.1, "Dünya Devlerinin Korkusu", defense_penalty=0.15),
        Player("Antonio Rüdiger", "Stoper", 8.9, "Sert Savunma Lideri", defense_penalty=0.13)
    ],
    "barcelona": [
        Player("Robert Lewandowski", "Forvet", 9.3, "Ceza Sahası Katili", attack_penalty=0.19),
        Player("Lamine Yamal", "Kanat", 9.5, "Genç Harika & Asist Makinesi", attack_penalty=0.17),
        Player("Raphinha", "Forvet/Kanat", 9.1, "Pres & Gol Tehdidi", attack_penalty=0.13),
        Player("Pedri", "Orta Saha", 9.0, "Oyun Zekası Ustası", attack_penalty=0.10, defense_penalty=0.06)
    ],
    # Almanya Bundesliga
    "bayern munich": [
        Player("Harry Kane", "Forvet", 9.7, "Gol & Oyun Kurucu Santrfor", attack_penalty=0.24),
        Player("Jamal Musiala", "Hücum/Orta", 9.3, "Dribbling Sihirbazı", attack_penalty=0.15),
        Player("Manuel Neuer", "Kaleci", 8.6, "Efsane Kaleci", defense_penalty=0.11),
        Player("Dayot Upamecano", "Stoper", 8.4, "Fiziksel Stoper", defense_penalty=0.11)
    ],
    "bayer leverkusen": [
        Player("Florian Wirtz", "Hücum/Orta", 9.4, "Yaratıcı Deha", attack_penalty=0.18),
        Player("Victor Boniface", "Forvet", 8.6, "Güçlü Santrfor", attack_penalty=0.14),
        Player("Granit Xhaka", "Orta Saha", 8.9, "Takım Generali", attack_penalty=0.06, defense_penalty=0.10)
    ],
    # İtalya Serie A
    "inter": [
        Player("Lautaro Martínez", "Forvet", 9.4, "Kaptan & Seri Golcü", attack_penalty=0.19),
        Player("Marcus Thuram", "Forvet", 8.8, "Dinamik Hücum Partneri", attack_penalty=0.13),
        Player("Nicolò Barella", "Orta Saha", 8.9, "İtalya'nın En Dinamik Oyuncusu", attack_penalty=0.08, defense_penalty=0.08),
        Player("Yann Sommer", "Kaleci", 8.6, "Güvenilir Kaleci", defense_penalty=0.11)
    ]
}

# Pre-known active high-profile injuries as real-world baseline
KNOWN_INJURIES = {
    "Rodri": "Ön Çapraz Bağ (Sezonu Kapattı)",
    "Mauro Icardi": "Ön Çapraz Bağ (Sezonu Kapattı)",
    "Éder Militão": "Diz Sakatlığı",
    "Marc-André ter Stegen": "Diz Tendonu",
    "Dani Carvajal": "Çapraz Bağ",
    "Gabriel Paulista": "Uyluk Çekmesi"
}

# Apply known injuries on startup
for team_players in SQUADS_DATABASE.values():
    for p in team_players:
        if p.name in KNOWN_INJURIES:
            p.is_injured = True
            p.injury_reason = KNOWN_INJURIES[p.name]


class InjuryEngine:
    """Calculates squad injury penalties, adjusts Poisson lambda values and generates AI Insights."""

    @staticmethod
    def normalize_team_key(team_name: str) -> str:
        s = team_name.lower().strip()
        trans = {"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u"}
        for k, v in trans.items():
            s = s.replace(k, v)
        for suffix in [" fc", " fk", " sk", " a.ş.", " a.s.", " kulübü", " cf", " cd"]:
            if s.endswith(suffix):
                s = s[:-len(suffix)].strip()
        return s

    @classmethod
    def get_team_squad(cls, team_name: str) -> List[Player]:
        c_name = cls.normalize_team_key(team_name)
        for key, squad in SQUADS_DATABASE.items():
            if key in c_name or c_name in key:
                return squad
        
        # Generic fallback squad for teams not in detailed list
        return [
            Player(f"{team_name} Kilit Forvet", "Forvet", 8.0, "Ana Skorer & Gol Umudu", attack_penalty=0.14),
            Player(f"{team_name} 10 Numara", "Orta Saha", 7.8, "Oyun Kurucu & Pasör", attack_penalty=0.10),
            Player(f"{team_name} As Stoper", "Stoper", 7.7, "Savunma Lideri", defense_penalty=0.12),
            Player(f"{team_name} 1. Kaleci", "Kaleci", 7.6, "Ana Kaleci", defense_penalty=0.10)
        ]

    @classmethod
    def calculate_squad_penalties(cls, team_name: str, custom_injured_names: Optional[List[str]] = None) -> Tuple[float, float, List[Dict[str, Any]]]:
        """
        Returns (attack_penalty, defense_penalty, injured_players_list).
        Caps maximum team penalties realistically at 40%.
        """
        squad = cls.get_team_squad(team_name)
        custom_injured_set = set(custom_injured_names or [])

        total_attack_penalty = 0.0
        total_defense_penalty = 0.0
        injured_list = []

        for p in squad:
            # Check either pre-set injury or custom user toggle
            is_out = p.is_injured or (p.name in custom_injured_set)
            if is_out:
                total_attack_penalty += p.attack_penalty
                total_defense_penalty += p.defense_penalty
                injured_list.append({
                    "name": p.name,
                    "position": p.position,
                    "impact": p.impact_score,
                    "role": p.role_desc,
                    "reason": p.injury_reason or "Kadro Dışı / Sakat",
                    "attack_loss": round(p.attack_penalty * 100, 1),
                    "defense_loss": round(p.defense_penalty * 100, 1)
                })

        # Cap realistic impacts: a team cannot lose 100% of attack
        total_attack_penalty = min(0.40, total_attack_penalty)
        total_defense_penalty = min(0.40, total_defense_penalty)

        return round(total_attack_penalty, 4), round(total_defense_penalty, 4), injured_list

    @classmethod
    def generate_ai_insights(cls, home_team: str, away_team: str, h_injuries: List[Dict[str, Any]], a_injuries: List[Dict[str, Any]], delta_h: float, delta_a: float) -> List[Dict[str, str]]:
        """Generates smart AI tactical insights explaining how injuries alter the betting coupon."""
        insights = []

        # Home injuries insight
        for inj in h_injuries:
            if inj["impact"] >= 9.0:
                insights.append({
                    "level": "CRITICAL",
                    "badge": "🚨 Kilit Eksik",
                    "text": f"{home_team} tarafında süperstar <strong>{inj['name']}</strong> ({inj['role']}) eksik! Ev sahibinin gol atma gücü %{inj['attack_loss']} zayıfladı."
                })
            elif inj["position"] == "Kaleci":
                insights.append({
                    "level": "WARNING",
                    "badge": "🧤 Kaleci Eksikliği",
                    "text": f"{home_team} as kalecisi <strong>{inj['name']}</strong> yok. Savunma zafiyeti arttı; KG VAR ve Deplasman Golü ihtimali yükseldi."
                })

        # Away injuries insight
        for inj in a_injuries:
            if inj["impact"] >= 9.0:
                insights.append({
                    "level": "CRITICAL",
                    "badge": "🚨 Kilit Eksik",
                    "text": f"{away_team} tarafında kilit isim <strong>{inj['name']}</strong> eksik! Deplasman ekibinin hücum tehdidi %{inj['attack_loss']} düştü."
                })
            elif inj["position"] == "Kaleci":
                insights.append({
                    "level": "WARNING",
                    "badge": "🧤 Kaleci Eksikliği",
                    "text": f"{away_team} as kalecisi <strong>{inj['name']}</strong> yok. Ev sahibi galibiyeti ve 2.5 ÜST olasılığı belirgin güçlendi."
                })

        # Goal trend synthesis
        if delta_h < -0.25 or delta_a < -0.25:
            insights.append({
                "level": "COUPON_TIP",
                "badge": "💡 Kupon Tavsiyesi",
                "text": "Kilit golcülerin eksikliği nedeniyle beklenen gol (xG) düştü. Model bu maçta <strong>2.5 ALT</strong> ve <strong>1X / X2 Çifte Şans</strong> tercihlerini daha güvenli buluyor."
            })
        elif not insights:
            insights.append({
                "level": "INFO",
                "badge": "✅ Kadrolar Tam",
                "text": "İki takımın da kilit oyuncuları sağlam. Model saf Poisson gücünü %100 kapasiteyle uyguluyor."
            })

        return insights
