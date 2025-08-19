from __future__ import annotations
import random
import math
import string
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# =====================================================
# ⚙️  LEAGUE CORE — DATA, RANKS, SIM, PATCHES, OFFSEASON, MEDIA, AWARDS
# Expanded version: includes All-Star, media/tweets, trades, playoffs, accessors
# =====================================================

# -------------------------
# RANK SYSTEM & POINTS (exact values)
# -------------------------
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
    tags: List[str] = field(default_factory=list)  # e.g., aggressive, tank, retired
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


PERSONALITIES = [
    ("Showman", [
        "We packed the arena. Bright lights, big dubs.",
        "Mic's hot. We hoop AND talk." ,
        "We don't rebuild. We rebrand to W's.",
    ]),
    ("Silent Killer", [
        "No tweets. Just wins.",
        "Clocked in. Another day, another sweep.",
        "Talk less, crown more.",
    ]),
    ("Troll", [
        "Imagine losing to THIS lineup 😂", 
        "Patch notes buffed our comedy tier too.",
        "Rent free since preseason.",
    ]),
    ("Analyst", [
        "Per 36 crowns, our ORtg is elite.",
        "Small sample, large brain moves.",
        "Regression? Not on my spreadsheet.",
    ]),
    ("Hype", [
        "LOCKED IN 🔒🔥", "City behind us.", "We up, no cap.",
    ]),
]


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

    def post_tweet(self, msg: Optional[str] = None):
        if msg is None:
            pool = dict(PERSONALITIES).get(self.personality, ["We up."])
            msg = pick(pool)
        tag = f"[{self.rank}]"
        self.tweets.append(f"{tag} {msg}")
        # Keep last 25
        self.tweets = self.tweets[-25:]


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

    @property
    def wins(self) -> int:
        return self.gm.record_w

    @property
    def losses(self) -> int:
        return self.gm.record_l

    def compute_power(self) -> float:
        # Auto-pick starters if not set
        if not self.starters:
            picks = sorted(self.roster, key=lambda c: c.overall, reverse=True)[:3]
            self.starters = [c.id for c in picks]
            if len(self.roster) > 3:
                self.backup = self.roster[3].id
        cards = [c for c in self.roster if c.id in self.starters]
        base = sum(c.overall for c in cards) / max(1, len(cards))
        # lightweight synergy detection
        tags = set(sum([c.tags for c in cards], []))
        synergy_boost = 1.0
        if "aggressive" in tags:
            synergy_boost *= 1.02
        if "tank" in tags:
            synergy_boost *= 1.02
        chem = 1.0 + self.chemistry
        fatigue_penalty = 1.0 - clamp(self.fatigue, 0, 0.30)
        gm_buff = 1.0 + self.gm.get_active_buff_pct()
        return base * chem * fatigue_penalty * gm_buff * synergy_boost

    def lineup_stats(self) -> List[Dict]:
        out = []
        for cid in self.starters:
            c = next((x for x in self.roster if x.id == cid), None)
            if c:
                out.append(c.as_row())
        return out


@dataclass
class GameResult:
    home_id: str
    away_id: str
    home_crowns: int
    away_crowns: int
    winner_id: str
    contribution: Dict[str, float]
    recap: str
    playoff: bool = False


@dataclass
class ScheduleGame:
    week: int
    home_id: str
    away_id: str
    date: datetime
    result: Optional[GameResult] = None


@dataclass
class SeriesResult:
    best_of: int
    a_id: str
    b_id: str
    a_wins: int = 0
    b_wins: int = 0
    games: List[GameResult] = field(default_factory=list)

    def winner(self) -> Optional[str]:
        need = (self.best_of // 2) + 1
        if self.a_wins >= need:
            return self.a_id
        if self.b_wins >= need:
            return self.b_id
        return None


@dataclass
class AwardLedger:
    season_awards: Dict[int, Dict[str, str]] = field(default_factory=dict)  # season -> {award: winner}
    hof: List[str] = field(default_factory=list)


@dataclass
class AllStarEvent:
    season: int
    candidates: List[str] = field(default_factory=list)  # card ids
    starters: List[str] = field(default_factory=list)
    mvp_card_id: Optional[str] = None


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
    era: int = 1
    patches: List[Dict] = field(default_factory=list)
    rumors: List[str] = field(default_factory=list)
    allstar: Optional[AllStarEvent] = None

    # -------------- FACTORY --------------
    @staticmethod
    def create_default(name: str = "Clash Royale Fantasy League", n_teams: int = 30, n_cards: int = 160) -> "League":
        lg = League(name=name)
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
        # Flag 4 rookies
        for cid in random.sample(list(lg.cards.keys()), 4):
            lg.cards[cid].rookie = True

        # Teams + GMs
        for t in range(n_teams):
            gm = GM(id=f"GM{t:02d}", name=f"GM {slug(3)}", personality=pick([p[0] for p in PERSONALITIES]))
            roster = random.sample(list(lg.cards.values()), 12)
            team = Team(
                id=f"T{t:02d}",
                name=f"{pick(['Royal','Crimson','Neon','Shadow','Volt','Urban','Titan'])} {pick(['Wolves','Dragons','Kings','Ghosts','Ravens','Vipers'])}",
                logo_svg=generate_logo_svg(),
                gm=gm,
                roster=roster,
                chemistry=round(random.uniform(0.00, 0.15), 3),
                fatigue=0.30,  # start season: +30% fatigue
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
        pairings = []
        for i in range(len(team_ids)):
            for j in range(i + 1, len(team_ids)):
                pairings.append((team_ids[i], team_ids[j]))
        random.shuffle(pairings)
        # 40-ish per team → ~600 total cap
        for idx, (a, b) in enumerate(pairings[:600]):
            week = ((idx // 15) % 20) + 1  # 20 weeks
            game_date = start_date + timedelta(days=idx % (20 * 7))
            games.append(ScheduleGame(week=week, home_id=a, away_id=b, date=game_date))
        return games

    # -------------- GAME SIM --------------
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
        self._media_react_to_game(home, away, winner, hc, ac, playoff)
        return GameResult(home_id=home_id, away_id=away_id, home_crowns=hc, away_crowns=ac, winner_id=winner, contribution=contribution, recap=recap, playoff=playoff)

    def _make_recap(self, home: Team, away: Team, hc: int, ac: int, winner: str, playoff: bool) -> str:
        tag = "PLAYOFF" if playoff else "Regular"
        if winner == home.id:
            line = f"{home.name} edge {away.name} {hc}-{ac}. ({tag})"
        else:
            line = f"{away.name} edge {home.name} {ac}-{hc}. ({tag})"
        if self.is_rivalry(home.id, away.id):
            line += " Rivalry game was spicy 🔥"
        self.news.append(line)
        return line

    # -------------- MEDIA / NEWS / TWEETS --------------
    def _media_react_to_game(self, home: Team, away: Team, winner_id: str, hc: int, ac: int, playoff: bool):
        # Fan memes + GM trash talk
        wteam = self.teams[winner_id]
        lteam = away if wteam.id == home.id else home
        # Fan tweet
        mood = "🔥 hype" if (hc - ac >= 2 or playoff) else ("😴 bored" if abs(hc - ac) == 0 else "😡 angry")
        fan_lines = [
            f"Fans: {wteam.name} looking SCARY {mood}",
            f"Memes cooking for {lteam.name} rn 💀",
            f"Patch villain arc incoming? {lteam.name} blaming balance again 🤖",
        ]
        self.news.append(pick(fan_lines))
        # GM tweets (modern slang)
        wteam.gm.post_tweet(pick([
            "GGs. We don’t fumble.", "City loud tonight.", "Another bag secured."
        ]))
        lteam.gm.post_tweet(pick([
            "We’ll spin back.", "Film session loading...", "Silence the noise soon."
        ]))

    # -------------- WEEK / REGULAR SEASON --------------
    def sim_week(self, week: int):
        for g in [x for x in self.schedule if x.week == week and x.result is None]:
            g.result = self.sim_game(g.home_id, g.away_id)
        self.week = max(self.week, week + 1)

    # -------------- PLAYOFFS --------------
    def seed_playoffs(self):
        table = sorted(self.teams.values(), key=lambda t: (t.gm.record_w - t.gm.record_l, t.compute_power()), reverse=True)
        top16 = table[:16]
        self.playoffs_bracket = [(top16[i].id, top16[-(i+1)].id) for i in range(8)]
        self.news.append("Playoff bracket locked in. Upsets brewing.")

    def sim_series(self, a_id: str, b_id: str, best_of: int) -> SeriesResult:
        series = SeriesResult(best_of=best_of, a_id=a_id, b_id=b_id)
        need = (best_of // 2) + 1
        while series.winner() is None:
            r = self.sim_game(a_id, b_id, playoff=True)
            series.games.append(r)
            if r.winner_id == a_id:
                series.a_wins += 1
            else:
                series.b_wins += 1
            if series.a_wins == need or series.b_wins == need:
                break
        return series

    def run_playoffs(self):
        if not self.playoffs_bracket:
            self.seed_playoffs()
        # Round 1: Bo3
        r1_winners = []
        for a,b in self.playoffs_bracket:
            s = self.sim_series(a, b, 3)
            r1_winners.append(s.winner())
        # Round 2: Bo5
        r2_pairs = [(r1_winners[i], r1_winners[i+1]) for i in range(0, len(r1_winners), 2)]
        r2_winners = []
        for a,b in r2_pairs:
            s = self.sim_series(a, b, 5)
            r2_winners.append(s.winner())
        # Round 3: Bo5
        r3_pairs = [(r2_winners[i], r2_winners[i+1]) for i in range(0, len(r2_winners), 2)]
        r3_winners = []
        for a,b in r3_pairs:
            s = self.sim_series(a, b, 5)
            r3_winners.append(s.winner())
        # Finals: Bo7
        champ_series = self.sim_series(r3_winners[0], r3_winners[1], 7)
        champ_id = champ_series.winner()
        if champ_id:
            self.teams[champ_id].gm.apply_points(POINT_VALUES["championship"])
            self.teams[champ_id].gm.titles += 1
            self.news.append(f"{self.teams[champ_id].name} lift the trophy 🏆")
        # Simple Finals MVP = highest contribution in finals starters
        finals_cards = champ_series.games[-1].contribution
        if finals_cards:
            mvp_card_id = max(finals_cards.items(), key=lambda kv: kv[1])[0]
            self._give_award("Finals MVP", self.cards[mvp_card_id].name)

    # -------------- ALL-STAR WEEKEND --------------
    def run_all_star(self):
        # Candidates: top 20 by contribution + hype (pick_rate)
        top_cards = sorted(self.cards.values(), key=lambda c: (c.contribution + c.pick_rate), reverse=True)[:20]
        candidates = [c.id for c in top_cards]
        # Fans/GMs vote → weight by contribution
        weights = [(c.id, max(0.01, c.contribution + 0.1)) for c in top_cards]
        starters = []
        while len(starters) < 10 and weights:
            cid = weighted_choice(weights)
            starters.append(cid)
            weights = [(i,w) for (i,w) in weights if i != cid]
        self.allstar = AllStarEvent(season=self.season, candidates=candidates, starters=starters)
        # Exhibition first to 5 crowns (simulate bursts)
        a_team = starters[:5]
        b_team = starters[5:10]
        a_score = b_score = 0
        while a_score < 5 and b_score < 5:
            a_pow = sum(self.cards[c].overall for c in a_team) * random.uniform(0.9, 1.1)
            b_pow = sum(self.cards[c].overall for c in b_team) * random.uniform(0.9, 1.1)
            if a_pow >= b_pow:
                a_score += 1
            else:
                b_score += 1
        # MVP = highest contribution among winners
        winners = a_team if a_score > b_score else b_team
        mvp_id = max(winners, key=lambda cid: self.cards[cid].contribution)
        self.allstar.mvp_card_id = mvp_id
        self._give_award("All-Star MVP", self.cards[mvp_id].name)
        self.news.append(f"All-Star: Team {'A' if a_score>b_score else 'B'} wins {max(a_score,b_score)}-{min(a_score,b_score)}. MVP: {self.cards[mvp_id].name} ⭐")

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
        note = {"season": self.season, "nickname": nickname, "ts": datetime.utcnow().isoformat()}
        self.patches.append(note)
        self.news.append(f"{nickname}: Meta shake-up → low-pick cards buffed, patch villain clipped.")

    # -------------- TRADES (simple rumor + accept) --------------
    def generate_trade_rumors(self):
        # Pick two teams, propose swapping lowest OVR in one for need fit in other
        a, b = random.sample(list(self.teams.values()), 2)
        a_card = min(a.roster, key=lambda c: c.overall)
        b_card = min(b.roster, key=lambda c: c.overall)
        rumor = f"Rumor: {a.name} eyeing {b_card.name} for {a_card.name}. Deadline heat rising."
        self.rumors.append(rumor)
        self.rumors = self.rumors[-30:]
        self.news.append(rumor)

    def execute_random_trade(self):
        a, b = random.sample(list(self.teams.values()), 2)
        a_card = min(a.roster, key=lambda c: c.overall)
        b_card = max(b.roster, key=lambda c: c.overall)
        # swap
        a.roster.remove(a_card); b.roster.append(a_card)
        b.roster.remove(b_card); a.roster.append(b_card)
        a.starters = []; b.starters = []  # force recompute
        self.news.append(f"Trade: {a.name} acquired {b_card.name}; {b.name} get {a_card.name}.")

    # -------------- AWARDS & END OF SEASON --------------
    def _give_award(self, name: str, winner: str):
        season_dict = self.awards.season_awards.setdefault(self.season, {})
        season_dict[name] = winner

    def finalize_awards(self):
        season_awards: Dict[str, str] = {}
        # MVP = highest contribution
        mvp_card = max(self.cards.values(), key=lambda c: c.contribution, default=None)
        if mvp_card:
            season_awards["MVP"] = mvp_card.name
        # Rookie of the Year
        rookies = [c for c in self.cards.values() if c.rookie]
        if rookies:
            roty = max(rookies, key=lambda c: c.contribution)
            season_awards["Rookie of the Year"] = roty.name
        # Most Improved = largest delta from baseline history
        improved = max(self.cards.values(), key=lambda c: (c.buffs.get("Overall", 0) - c.nerfs.get("Overall", 0)), default=None)
        if improved:
            season_awards["Most Improved"] = improved.name
        # GM of the Year = best W-L diff
        best_gm_team = max(self.teams.values(), key=lambda t: (t.gm.record_w - t.gm.record_l), default=None)
        if best_gm_team:
            season_awards["GM of the Year"] = best_gm_team.gm.name
        # All-League Teams (1st/2nd/3rd) = top 15 by contribution
        top15 = sorted(self.cards.values(), key=lambda c: c.contribution, reverse=True)[:15]
        names = [c.name for c in top15]
        season_awards["All-League 1st Team"] = ", ".join(names[:5])
        season_awards["All-League 2nd Team"] = ", ".join(names[5:10])
        season_awards["All-League 3rd Team"] = ", ".join(names[10:15])

        self.awards.season_awards[self.season] = season_awards
        self.news.append(
            f"Season {self.season} awards: " + ", ".join([f"{k}: {v}" for k,v in season_awards.items()])
        )
        # Simple HOF tick: MVPs & Finals MVPs get tracked
        for key in ("MVP", "Finals MVP"):
            if key in season_awards:
                self.awards.hof.append(season_awards[key])
        self.awards.hof = self.awards.hof[-50:]

    # -------------- OFFSEASON / ERA --------------
    def offseason_reset(self):
        # Start-of-season fatigue bump (+30% cap), rookies/retirements, patch
        for t in self.teams.values():
            t.fatigue = clamp(t.fatigue + 0.30, 0, 0.30)
        # Clear rookie flags
        for c in self.cards.values():
            c.rookie = False
        # 4 rookies
        for cid in random.sample(list(self.cards.keys()), 4):
            self.cards[cid].rookie = True
        # Up to 3 retirements (soft)
        for cid in random.sample(list(self.cards.keys()), 3):
            self.cards[cid].overall = max(50, self.cards[cid].overall - 5)
            if "retired" not in self.cards[cid].tags:
                self.cards[cid].tags.append("retired")
        # Patch & schedule
        self.apply_patch(nickname=f"Patch S{self.season} Wrap-Up")
        self.season += 1
        if self.season % random.randint(5,8) == 0:
            self.era += 1
            self.news.append(f"New Era begins: Era {self.era} ✨")
        self.week = 1
        self.schedule = self.generate_schedule()
        self.generate_trade_rumors()
        self.news.append(f"Season {self.season} draft board is live. Rookies incoming ⭐.")

    # -------------- ACCESSORS FOR UI (used by app.py) --------------
    def get_standings(self) -> List[Dict]:
        rows = []
        for t in self.teams.values():
            rows.append({
                "Team": t.name,
                "GM": t.gm.name,
                "W": t.wins,
                "L": t.losses,
                "Rank": t.gm.rank,
                "Points": t.gm.points,
                "Buff%": f"{int(t.gm.get_active_buff_pct()*100)}%",
                "Power": round(t.compute_power(), 1),
            })
        rows.sort(key=lambda r: (r["W"] - r["L"], r["Power"]), reverse=True)
        return rows

    def get_news(self) -> List[str]:
        return self.news[-10:][::-1]

    def get_team(self, team_name: str) -> Team:
        for t in self.teams.values():
            if t.name == team_name or t.id == team_name:
                return t
        raise KeyError("Team not found")

    def get_all_cards(self) -> List[Dict]:
        return [c.as_row() for c in self.cards.values()]

    def get_stat_leaders(self) -> List[Dict]:
        leaders = []
        top_contrib = sorted(self.cards.values(), key=lambda c: c.contribution, reverse=True)[:10]
        for c in top_contrib:
            leaders.append({"Card": c.name, "Contribution %": round(c.contribution*100,2), "Pick Rate %": round(c.pick_rate*100,2), "OVR": c.overall})
        return leaders

    def get_gm_leaderboard(self) -> List[Dict]:
        rows = []
        for t in self.teams.values():
            rows.append({
                "GM": t.gm.name,
                "Team": t.name,
                "Rank": t.gm.rank,
                "XP": t.gm.points,
                "Record": f"{t.wins}-{t.losses}",
                "Active Buff": f"{int(t.gm.get_active_buff_pct()*100)}% for {max(0,t.gm.active_buff_games)}",
            })
        rows.sort(key=lambda r: r["XP"], reverse=True)
        return rows

    def get_rivalries(self) -> List[Dict]:
        out = []
        for (a,b), heat in self.rivalries.items():
            out.append({"Home": self.teams[a].name, "Away": self.teams[b].name, "Heat": heat})
        return out

    def get_awards(self) -> List[Dict]:
        season = self.season
        awards = self.awards.season_awards.get(season, {})
        return [{"Award": k, "Winner": v} for k,v in awards.items()]

    def get_hof(self) -> List[Dict]:
        return [{"Name": n} for n in self.awards.hof]

    def get_history(self) -> List[Dict]:
        out = []
        for s, data in sorted(self.awards.season_awards.items()):
            out.append({"season_num": s, "summary": ", ".join([f"{k}: {v}" for k,v in data.items()])})
        return out

    def get_news_feed(self) -> List[str]:
        # Recent GM tweets + news
        feed = []
        for t in self.teams.values():
            feed.extend([f"{t.gm.name}: {tw}" for tw in t.gm.tweets[-3:]])
        feed.extend(self.get_news())
        return feed[-30:][::-1]

    def get_trade_rumors(self) -> List[Dict]:
        return [{"Rumor": r} for r in self.rumors[-10:][::-1]]

    def get_patches(self) -> List[Dict]:
        return self.patches[-10:][::-1]


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
