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
