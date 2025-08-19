from __future__ import annotations
import random
import math
import string
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# =====================================================
# ⚙️  LEAGUE CORE — DATA, RANKS, SIM, PATCHES, OFFSEASON
# =====================================================

# -------------------------
# RANK SYSTEM & POINTS
# -------------------------
# (Exact values from the design doc)
RANK_TIERS: List[Tuple[str, int, Optional[Tuple[float, int]]]] = [
    ("Bronze I", 0, None),
    ("Bronze II", 1000, None),
    ("Silver I", 2000, (0.02, 15)),
    ("Silver II", 3200, (0.02, 15)),
    ("Gold I", 4500, None),
    ("Gold II", 6000, None),
    ("Platinum", 7800, (0.04, 17)),
    ("Diamond", 10000, None),
    ("Opal", 12500, (0.07, 20)),
    ("Dark Matter", 15000, None),
    ("Champion", 18000, None),
    ("GOAT", 21500, (0.10, 25)),
    ("Hall of Fame", 25000, None),
]

POINT_VALUES = {
    "regular_win": 50,
    "regular_loss": -50,
    "playoff_win": 75,
    "playoff_loss": -75,
    "championship": 200,
}

# -------------------------
# SYNERGIES (extendable)
# -------------------------
SYNERGIES = {
    "Wallbreakers": {"ATK": 0.05, "condition": "aggressive_pair"},
    "Shield Brothers": {"DEF": 0.05, "condition": "tank_pair"},
}

# -------------------------
# UTILITIES
# -------------------------

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def pick(lst):
    return random.choice(lst)


def slug(n: int = 3) -> str:
    import string
    return "".join(random.choice(string.ascii_uppercase) for _ in range(n))


def weighted_choice(items: List[Tuple[any, float]]):
    total = sum(w for _, w in items)
    r = random.random() * total
    upto = 0
    for item, w in items:
        if upto + w >= r:
            return item
        upto += w
    return items[-1][0]

# -------------------------
# DATA MODELS
# -------------------------

@dataclass
class Card:
    id: str
    name: str
    atk: int
    atk_type: str  # melee / ranged / splash
    defense: int
    speed: int
    hit_speed: int
    stamina: int
    overall: int
    rookie: bool = False
    pick_rate: float = 0.0
    contribution: float = 0.0
    buffs: Dict[str, int] = field(default_factory=dict)
    nerfs: Dict[str, int] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)  # e.g., aggressive, tank
    history: List[Dict] = field(default_factory=list)

    def as_row(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "ATK": self.atk,
            "ATK Type": self.atk_type,
            "DEF": self.defense,
            "Speed": self.speed,
            "Hit Speed": self.hit_speed,
            "Stamina": self.stamina,
            "Overall": self.overall,
            "Rookie": self.rookie,
            "Pick Rate %": round(self.pick_rate * 100, 2),
            "Contribution %": round(self.contribution * 100, 2),
            "Tags": ", ".join(self.tags),
        }


@dataclass
class GM:
    id: str
    name: str
    personality: str
    points: int = 0
    rank: str = "Bronze I"
    xp_into_tier: int = 0
    next_tier_threshold: int = 1000
    active_buff_pct: float = 0.0
    active_buff_games: int = 0
    record_w: int = 0
    record_l: int = 0
    titles: int = 0
    awards: Dict[str, int] = field(default_factory=dict)
    tweets: List[str] = field(default_factory=list)

    def apply_points(self, delta: int):
        self.points = max(0, self.points + delta)
        self.update_rank()

    def update_rank(self):
        current_tier = RANK_TIERS[0]
        next_threshold = None
        for tier in RANK_TIERS:
            name, threshold, buff = tier
            if self.points >= threshold:
                current_tier = tier
            else:
                next_threshold = threshold
                break
        self.rank = current_tier[0]
        self.xp_into_tier = self.points - current_tier[1]
        self.next_tier_threshold = next_threshold or current_tier[1]
        buff = current_tier[2]
        if buff:
            pct, games = buff
            self.active_buff_pct = pct
            # refresh when entering/maintaining tier; burn-down happens per game
            if self.active_buff_games <= 0:
                self.active_buff_games = games
        else:
            self.active_buff_pct = 0.0
            # keep counter but no benefit in non-buff tiers

    def record_result(self, win: bool, playoff: bool = False):
        if win:
            self.record_w += 1
            self.apply_points(POINT_VALUES["playoff_win" if playoff else "regular_win"])
        else:
            self.record_l += 1
            self.apply_points(POINT_VALUES["playoff_loss" if playoff else "regular_loss"])
        if self.active_buff_games > 0:
            self.active_buff_games -= 1

    def get_active_buff_pct(self) -> float:
        return self.active_buff_pct if self.active_buff_games > 0 else 0.0


@dataclass
class Team:
    id: str
    name: str
    logo_svg: str
    gm: GM
    roster: List[Card]
    starters: List[str] = field(default_factory=list)  # card ids
    backup: Optional[str] = None
    chemistry: float = 0.0  # persists across seasons
    fatigue: float = 0.0    # increases over season; +0.30 at start of season
    rivalry_ids: List[str] = field(default_factory=list)
    crowns_for: int = 0
    crowns_against: int = 0

    def compute_power(self) -> float:
        # Auto-pick starters if not set
        if not self.starters:
            picks = sorted(self.roster, key=lambda c: c.overall, reverse=True)[:3]
            self.starters = [c.id for c in picks]
            if len(self.roster) > 3:
                self.backup = self.roster[3].id
        cards = [c for c in self.roster if c.id in self.starters]
        base = sum(c.overall for c in cards) / max(1, len(cards))
        chem = 1.0 + self.chemistry
        fatigue_penalty = 1.0 - clamp(self.fatigue, 0, 0.30)
        gm_buff = 1.0 + self.gm.get_active_buff_pct()
        return base * chem * fatigue_penalty * gm_buff


@dataclass
class GameResult:
    home_id: str
    away_id: str
    home_crowns: int
    away_crowns: int
    winner_id: str
    contribution: Dict[str, float]
    recap: str


@dataclass
class ScheduleGame:
    week: int
    home_id: str
    away_id: str
    date: datetime
    result: Optional[GameResult] = None


@dataclass
class AwardLedger:
    season_awards: Dict[int, Dict[str, str]] = field(default_factory=dict)  # season -> {award: winner_id/name}


@dataclass
class League:
    name: str
    season: int = 1
    week: int = 1
    teams: Dict[str, Team] = field(default_factory=dict)
    cards: Dict[str, Card] = field(default_factory=dict)
    schedule: List[ScheduleGame] = field(default_factory=list)
    news: List[str] = field(default_factory=list)
    rivalries: Dict[Tuple[str, str], int] = field(default_factory=dict) # (a,b) -> heat
    playoffs_bracket: List[Tuple[str, str]] = field(default_factory=list)
    awards: AwardLedger = field(default_factory=AwardLedger)

    # -------------- FACTORY --------------
    @staticmethod
    def create_default(name: str = "Clash Royale Fantasy League", n_teams: int = 30, n_cards: int = 160) -> "League":
        lg = League(name=name)
        personalities = ["Showman", "Silent Killer", "Troll", "Analyst", "Hype"]
        # Cards pool
        for i in range(n_cards):
            cid = f"C{i:03d}"
            atk_type = random.choice(["melee", "ranged", "splash"]) 
            tags = []
            if random.random() < 0.35:
                tags.append("aggressive")
            if random.random() < 0.35:
                tags.append("tank")
            card = Card(
                id=cid,
                name=f"{pick(['Blaze','Frost','Shadow','Nova','Iron','Volt','Ember','Gale'])} {pick(['Knight','Rogue','Archer','Guardian','Specter','Titan','Warden'])}",
                atk=random.randint(60, 98),
                atk_type=atk_type,
                defense=random.randint(60, 98),
                speed=random.randint(50, 99),
                hit_speed=random.randint(50, 99),
                stamina=random.randint(60, 99),
                overall=random.randint(65, 99),
                rookie=False,
                tags=tags,
            )
            lg.cards[cid] = card
        # Flag 4 random rookies for season start
        for cid in random.sample(list(lg.cards.keys()), 4):
            lg.cards[cid].rookie = True

        # Teams + GMs
        for t in range(n_teams):
            gm = GM(id=f"GM{t:02d}", name=f"GM {slug(3)}", personality=pick(personalities))
            roster = random.sample(list(lg.cards.values()), 12)
            team = Team(
                id=f"T{t:02d}",
                name=f"{pick(['Royal','Crimson','Neon','Shadow','Volt','Urban','Titan'])} {pick(['Wolves','Dragons','Kings','Ghosts','Ravens','Vipers'])}",
                logo_svg=generate_logo_svg(),
                gm=gm,
                roster=roster,
                chemistry=round(random.uniform(0.00, 0.15), 3),
                fatigue=0.30,  # start season: +30% fatigue as requested
            )
            team.compute_power()
            lg.teams[team.id] = team

        lg.generate_rivalries()
        lg.schedule = lg.generate_schedule()
        lg.news.append("Season booted up. Power rankings drop soon.")
        return lg

    # -------------- RIVALRIES --------------
    def generate_rivalries(self):
        ids = list(self.teams.keys())
        random.shuffle(ids)
        for i in range(0, len(ids), 2):
            if i + 1 < len(ids):
                a, b = ids[i], ids[i + 1]
                self.rivalries[(a, b)] = 1
                self.teams[a].rivalry_ids.append(b)
                self.teams[b].rivalry_ids.append(a)

    def is_rivalry(self, a: str, b: str) -> bool:
        return (a, b) in self.rivalries or (b, a) in self.rivalries

    # -------------- SCHEDULE --------------
    def generate_schedule(self) -> List[ScheduleGame]:
        games = []
        team_ids = list(self.teams.keys())
        random.shuffle(team_ids)
        start_date = datetime(datetime.now().year, 1, 7)
        # Build pairings; cap to keep things manageable (approx 40 games/team goal)
        pairings = []
        for i in range(len(team_ids)):
            for j in range(i + 1, len(team_ids)):
                pairings.append((team_ids[i], team_ids[j]))
        random.shuffle(pairings)
        for idx, (a, b) in enumerate(pairings[:600]):  # soft cap
            week = ((idx // 15) % 20) + 1  # 20 weeks
            game_date = start_date + timedelta(days=idx % (20 * 7))
            games.append(ScheduleGame(week=week, home_id=a, away_id=b, date=game_date))
        return games

    # -------------- SIMULATION --------------
    def sim_game(self, home_id: str, away_id: str, playoff: bool = False) -> GameResult:
        home = self.teams[home_id]
        away = self.teams[away_id]
        rp = 0.03 if self.is_rivalry(home_id, away_id) else 0.0
        # base power + playoff multiplier + rivalry flavor
        home_pow = home.compute_power() * (1.02 if playoff else 1.0) * (1.0 + rp)
        away_pow = away.compute_power() * (1.02 if playoff else 1.0) * (1.0 + rp)
        # variance to allow upsets
        variance = random.uniform(0.9, 1.1)
        home_score = home_pow * random.uniform(0.95, 1.05) * variance
        away_score = away_pow * random.uniform(0.95, 1.05) * (2 - variance)

        def score_to_crowns(score: float) -> int:
            if score <= 0:
                return 0
            val = 3 / (1 + math.exp(- (score - 70) / 8))
            return int(clamp(round(val), 0, 3))

        hc = score_to_crowns(home_score)
        ac = score_to_crowns(away_score)
        if hc == ac:  # tie → coinflip crown
            if random.random() < 0.5:
                hc = min(3, hc + 1)
            else:
                ac = min(3, ac + 1)
        winner = home_id if hc > ac else away_id

        # Apply GM results/points
        self.teams[winner].gm.record_result(True, playoff)
        loser_id = home_id if winner != home_id else away_id
        self.teams[loser_id].gm.record_result(False, playoff)

        # Contribution % split across starters
        contribution: Dict[str, float] = {}
        for team in [home, away]:
            starters = [c for c in team.roster if c.id in team.starters]
            total = sum(max(1, c.overall) for c in starters)
            for c in starters:
                share = max(1, c.overall) / total
                c.contribution = clamp(0.8 * c.contribution + 0.2 * share, 0, 1)
                contribution[c.id] = round(share, 3)
                c.pick_rate = clamp(c.pick_rate + 0.001, 0, 1)
        # Fatigue & chemistry evolve
        for team in [home, away]:
            team.fatigue = clamp(team.fatigue + 0.01, 0, 0.30)
            team.chemistry = clamp(team.chemistry + 0.002, 0, 0.25)

        recap = self._make_recap(home, away, hc, ac, winner, playoff)
        return GameResult(home_id=home_id, away_id=away_id, home_crowns=hc, away_crowns=ac, winner_id=winner, contribution=contribution, recap=recap)

    def _make_recap(self, home: Team, away: Team, hc: int, ac: int, winner: str, playoff: bool) -> str:
        tag = "PLAYOFF" if playoff else "Regular"
        if winner == home.id:
            line = f"{home.name} edge {away.name} {hc}-{ac}. ({tag})"
        else:
            line = f"{away.name} edge {home.name} {ac}-{hc}. ({tag})"
        if self.is_rivalry(home.id, away.id):
            line += " Rivalry game was spicy 🔥"
        return line

    # -------------- PLAYOFFS (placeholder bracket) --------------
    def seed_playoffs(self):
        # Seed by record (W-L diff) or power as fallback
        table = sorted(self.teams.values(), key=lambda t: (t.gm.record_w - t.gm.record_l, t.compute_power()), reverse=True)
        top16 = table[:16]
        self.playoffs_bracket = [(top16[i].id, top16[-(i+1)].id) for i in range(8)]
        self.news.append("Playoff bracket locked in. Upsets brewing.")

    # -------------- PATCHES & META --------------
    def apply_patch(self, nickname: str = "Patch Lightning Rod"):
        # Buff low pick-rate, clip top-pick villains
        all_cards = list(self.cards.values())
        low_pick = sorted(all_cards, key=lambda c: c.pick_rate)[:10]
        top_pick = sorted(all_cards, key=lambda c: c.pick_rate, reverse=True)[:3]
        for c in low_pick:
            c.buffs["Overall"] = c.buffs.get("Overall", 0) + 3
            c.overall = int(clamp(c.overall + 3, 0, 100))
        for c in top_pick:
            c.nerfs["Overall"] = c.nerfs.get("Overall", 0) + 2
            c.overall = int(clamp(c.overall - 2, 0, 100))
        self.news.append(f"{nickname}: Meta shake-up → low-pick cards buffed, patch villain got clipped.")

    # -------------- AWARDS (light placeholder hooks) --------------
    def finalize_awards(self):
        # Simple MVP = highest contribution card; GM of Year = best W-L diff
        season_awards: Dict[str, str] = {}
        mvp_card = max(self.cards.values(), key=lambda c: c.contribution, default=None)
        if mvp_card:
            season_awards["MVP"] = mvp_card.name
        best_gm_team = max(self.teams.values(), key=lambda t: (t.gm.record_w - t.gm.record_l), default=None)
        if best_gm_team:
            season_awards["GM of the Year"] = best_gm_team.gm.name
        self.awards.season_awards[self.season] = season_awards
        self.news.append(f"Season {self.season} awards posted: {', '.join([f'{k}: {v}' for k,v in season_awards.items()])}.")

    # -------------- DRAFT / OFFSEASON --------------
    def offseason_reset(self):
        # Start-of-season fatigue bump (+30% cap), rookies/retirements, patch
        for t in self.teams.values():
            t.fatigue = clamp(t.fatigue + 0.30, 0, 0.30)
        # Set exactly 4 rookies and retire up to 3 (flag only)
        for c in self.cards.values():
            c.rookie = False
        for cid in random.sample(list(self.cards.keys()), 4):
            self.cards[cid].rookie = True
        for cid in random.sample(list(self.cards.keys()), 3):
            # simulate retirement by lowering OVR slightly and tagging
            self.cards[cid].overall = max(50, self.cards[cid].overall - 5)
            self.cards[cid].tags.append("retired")
        self.apply_patch()
        # Reset weekly schedule for new season
        self.season += 1
        self.week = 1
        self.schedule = self.generate_schedule()
        self.news.append(f"Season {self.season} draft board is live. Rookies incoming ⭐.")


# -------------------------
# LOGO GENERATOR (SVG string)
# -------------------------

def generate_logo_svg() -> str:
    hue = random.randint(0, 360)
    color1 = f"hsl({hue}, 70%, 45%)"
    color2 = f"hsl({(hue+180)%360}, 70%, 45%)"
    svg = f'''<svg width="96" height="96" viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="{color1}"/>
        <stop offset="100%" stop-color="{color2}"/>
      </linearGradient>
    </defs>
    <path d="M48 8 L80 20 L80 50 C80 70 64 84 48 90 C32 84 16 70 16 50 L16 20 Z" fill="url(#g)" stroke="white" stroke-width="3"/>
    <text x="48" y="54" font-size="22" fill="white" font-weight="bold" text-anchor="middle">{slug(2)}</text>
    </svg>'''
    return svg


# -------------------------
# SINGLETON ACCESSOR
# -------------------------
_singleton_league: Optional[League] = None

def get_league() -> League:
    """Return a singleton League instance for the UI layer to reuse."""
    global _singleton_league
    if _singleton_league is None:
        _singleton_league = League.create_default()
    return _singleton_league
