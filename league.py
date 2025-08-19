# === league.py ===
# Fantasy Clash Royale League Engine
# Master Plan v1 – Milestone 1
# Core setup: enums, constants, Card, Team, Synergy scaffolding

from __future__ import annotations

import math
import random
import statistics
import string
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
from itertools import combinations, product

# ---------- RNG seeding helper ----------
DEFAULT_SEED = 1337
def seeded_rand(seed: Optional[int] = None) -> random.Random:
    return random.Random(seed or DEFAULT_SEED)

# ---------- Enums & Constants ----------
class Archetype(Enum):
    TANK = "Tank"
    HEALER = "Healer"
    BURST = "Burst"
    CONTROL = "Control"
    UTILITY = "Utility"
    BALANCED = "Balanced"

class AtkType(Enum):
    MELEE = "Melee"
    RANGED = "Ranged"
    SPELL = "Spell"

NUM_TEAMS = 30
ROSTER_SIZE = 4            # 3 starters + 1 backup
STARTERS = 3
BACKUPS = 1
MIN_CARD_POOL = 160
MAX_CARD_POOL = 170
SEASON_MIN_LIFE = 5
SEASON_MAX_LIFE = 8

# Rivalry
RIVALRY_INITIAL = 10
RIVALRY_DECAY = 2          # per season if inactive
RIVALRY_GAIN = 6           # per meaningful game
RIVALRY_WIN_BUFF_PCT = 0.02
RIVALRY_WIN_BUFF_GAMES = 2

# Simulation weights
POWER_WEIGHT = 0.75
LUCK_WEIGHT = 0.25

# Awards weights (HOF)
AWARD_POINTS = {
    "MVP": 10,
    "ALL_STAR": 5,
    "MOTY": 3,
    "MIP": 4,
    "ALL_TEAM": 2,  # applies to First/Second/Third
}
CHAMPIONSHIP_POINTS = 5

# HOF thresholds
HOF_GUARANTEE = 85
HOF_BUBBLE_MIN = 70

# Draft grade weighting
GRADE_W_OVR = 0.45
GRADE_W_SYNERGY = 0.35
GRADE_W_VALUE = 0.20

# Regular season length (each team plays each other once -> 29 games)
REG_SEASON_GAMES = 29

# Name banks
NAME_SYLLABLES = [
    "sha", "dor", "wyr", "val", "kai", "zen", "ran", "qua", "ion", "dra",
    "sil", "ark", "lix", "kor", "pyre", "nox", "vela", "zho", "ra", "myr"
]
TEAM_WORDS = [
    "Phoenix", "Wyrms", "Valkyries", "Titans", "Spectres", "Sentinels", "Drakes",
    "Ronin", "Warlocks", "Samurai", "Lancers", "Gladiators", "Marauders", "Stalkers",
    "Aces", "Blitz", "Nightfall", "Embers", "Cyclones", "Stormbreak", "Invictus",
    "Onyx", "Eclipse", "Aurora", "Nebula", "Tempest", "Rampage", "Genesis", "Revenant"
]
GM_STYLES = ["risk_taker", "conservative", "synergy_focused", "star_chaser"]
GM_SOCIAL = ["trash", "humble", "meme", "quiet"]
GM_RIVALRY = ["grudge", "forgiver"]

# ---------- Card ----------
@dataclass
class Card:
    name: str
    archetype: Archetype
    atk_type: AtkType
    stats: Dict[str, int]         # atk, def, speed, hit speed, stamina
    ovr: int                      # overall rating
    crowns_total: int = 0         # total crowns scored in career
    games_played: int = 0         # number of games played
    contribution_pct: float = 0.0 # avg % contribution across games
    pick_history: List[int] = field(default_factory=list) # seasons picked
    seasons_remaining: int = 0    # lifespan (5–8 seasons)
    rookie: bool = False
    seasonal: bool = False        # unique seasonal card
    retired: bool = False

# ---------- Team ----------
@dataclass
class Team:
    name: str
    gm: str
    roster: List[Card] = field(default_factory=list)
    total_score: int = 0
    avg_score: float = 0.0
    wins: int = 0
    losses: int = 0
    chemistry: float = 0.5
    championships: int = 0
    rivalry_meters: Dict[str, int] = field(default_factory=dict)

    def record_game(self, crowns: int, won: bool):
        self.total_score += crowns
        self.avg_score = self.total_score / max(1, self.wins + self.losses + 1)
        if won:
            self.wins += 1
        else:
            self.losses += 1

# ---------- Synergy (scaffold) ----------
@dataclass
class Synergy:
    archetypes: Tuple[Archetype, Archetype]
    bonus: int

# scaffold of 90+ synergies will be generated dynamically later

# ---------- Helpers ----------
def gen_card_name(rng: random.Random) -> str:
    """Procedurally generate cool card names from syllables."""
    return "".join(rng.choice(NAME_SYLLABLES).capitalize() for _ in range(rng.randint(2, 3)))

def gen_team_name(rng: random.Random, idx: int) -> str:
    word = rng.choice(TEAM_WORDS)
    return f"{word} {idx+1}"

# ---------- Synergy Generation ----------
def generate_synergy_pool(rng: random.Random) -> List[Synergy]:
    """Generate a pool of 90+ possible synergies across archetypes."""
    synergies: List[Synergy] = []
    archetypes = list(Archetype)
    for a1, a2 in combinations(archetypes, 2):
        bonus = rng.randint(1, 10)
        synergies.append(Synergy(archetypes=(a1, a2), bonus=bonus))
    # Ensure we hit at least 90 by duplicating with varied bonus
    while len(synergies) < 95:
        a1, a2 = rng.sample(archetypes, 2)
        bonus = rng.randint(1, 10)
        synergies.append(Synergy(archetypes=(a1, a2), bonus=bonus))
    return synergies

# ---------- Draft System ----------
class Draft:
    def __init__(self, rng: random.Random, season: int, teams: List[Team], card_pool: List[Card]):
        self.rng = rng
        self.season = season
        self.teams = teams
        self.card_pool = card_pool
        self.draft_order: List[Team] = []
        self.grades: Dict[str, str] = {}

    def run_lottery(self):
        """Simple random shuffle for draft order (lottery style)."""
        self.draft_order = self.teams[:]
        self.rng.shuffle(self.draft_order)

    def run_draft(self):
        """Each team drafts 4 cards: 3 starters + 1 backup."""
        if not self.draft_order:
            self.run_lottery()

        available = self.card_pool[:]
        self.rng.shuffle(available)

        for team in self.draft_order:
            picks = []
            for _ in range(ROSTER_SIZE):
                if not available:
                    break
                choice = available.pop()
                choice.pick_history.append(self.season)
                if self.season == 1 and _ == 0:
                    choice.rookie = True
                picks.append(choice)
            team.roster = picks
            self.grades[team.name] = self.grade_team(team)

    def grade_team(self, team: Team) -> str:
        """Assign draft grade based on OVR, synergy, value."""
        if not team.roster:
            return "F"
        avg_ovr = statistics.mean(c.ovr for c in team.roster)
        synergy_bonus = self.eval_synergy(team.roster)
        value_score = avg_ovr + synergy_bonus
        grade_score = (
            avg_ovr * GRADE_W_OVR +
            synergy_bonus * GRADE_W_SYNERGY +
            value_score * GRADE_W_VALUE
        )
        if grade_score >= 85:
            return "A"
        elif grade_score >= 75:
            return "B"
        elif grade_score >= 65:
            return "C"
        elif grade_score >= 55:
            return "D"
        else:
            return "F"

    def eval_synergy(self, roster: List[Card]) -> float:
        """Simple synergy eval based on archetype overlap."""
        score = 0
        for c1, c2 in combinations(roster, 2):
            if c1.archetype == c2.archetype:
                score += 5
        return score

# ---------- League Class (Milestone 3) ----------

class League:
    def __init__(self, seed: int = DEFAULT_SEED, human_team_name: Optional[str] = None):
        self.rng = random.Random(seed)
        self.season = 1
        self.cards: Dict[int, Card] = {}
        self.teams: Dict[int, Team] = {}

        # Generate pool + teams
        self._init_cards()
        self._init_teams(human_team_name)

    # ---------- Init helpers ----------
    def _gen_card_name(self) -> str:
        return "".join(self.rng.choice(NAME_SYLLABLES).capitalize()
                       for _ in range(self.rng.randint(2, 3)))

    def _gen_team_name(self, idx: int) -> str:
        word = self.rng.choice(TEAM_WORDS)
        return f"{word} {idx+1}"

    def _gen_gm_name(self, idx: int) -> str:
        return f"GM_{idx+1}"

    def _init_cards(self):
        pool_size = self.rng.randint(MIN_CARD_POOL, MAX_CARD_POOL)
        for cid in range(pool_size):
            name = self._gen_card_name()
            archetype = self.rng.choice(list(Archetype))
            atk_type = self.rng.choice(list(AtkType))
            stats = {
                "atk": self.rng.randint(40, 100),
                "def": self.rng.randint(40, 100),
                "speed": self.rng.randint(40, 100),
                "hit_speed": self.rng.randint(40, 100),
                "stamina": self.rng.randint(40, 100),
            }
            ovr = round(statistics.mean(stats.values()))
            card = Card(name=name, archetype=archetype, atk_type=atk_type,
                        stats=stats, ovr=ovr, id=cid)
            self.cards[cid] = card

    def _init_teams(self, human_team_name: Optional[str]):
        for tid in range(NUM_TEAMS):
            team_name = human_team_name if (human_team_name and tid == 0) else self._gen_team_name(tid)
            gm_name = self._gen_gm_name(tid)
            team = Team(name=team_name, gm=gm_name)
            self.teams[tid] = team

    def __str__(self):
        return f"League S{self.season}: {len(self.teams)} teams, {len(self.cards)} cards"



