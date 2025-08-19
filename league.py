# === league.py (Milestone 1A foundation) ===
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ---------- constants ----------
NUM_TEAMS = 30
CARD_POOL_SIZE = 165  # between 160–170
SEED_DEFAULT = 1337

# ---------- data models ----------
@dataclass
class Card:
    id: int
    name: str
    ovr: int

@dataclass
class Team:
    name: str
    gm: str
    roster: List[int] = field(default_factory=list)
    wins: int = 0
    losses: int = 0

    def record(self) -> str:
        return f"{self.wins}-{self.losses}"

# ---------- league ----------
class League:
    def __init__(self, seed: int = SEED_DEFAULT, human_team_name: Optional[str] = "Your Team"):
        self.rng = random.Random(seed)
        self.season = 1

        # store cards + teams
        self.cards: Dict[int, Card] = {}
        self.teams: List[Team] = []

        self._init_cards()
        self._init_teams(human_team_name)

    # --- init ---
    def _init_cards(self):
        for cid in range(1, CARD_POOL_SIZE + 1):
            name = f"Card{cid}"
            ovr = self.rng.randint(60, 99)
            self.cards[cid] = Card(id=cid, name=name, ovr=ovr)

    def _init_teams(self, human_team_name: Optional[str]):
        for i in range(NUM_TEAMS):
            gm = "You" if i == 0 else f"GM {i}"
            name = human_team_name if i == 0 else f"Team {i+1}"
            self.teams.append(Team(name=name, gm=gm))

    # --- simulate one random game ---
    def play_game(self, t1: Team, t2: Team):
        # pick winner randomly for now
        if self.rng.random() < 0.5:
            t1.wins += 1
            t2.losses += 1
            return f"{t1.name} beat {t2.name}"
        else:
            t2.wins += 1
            t1.losses += 1
            return f"{t2.name} beat {t1.name}"

    # --- standings ---
    def standings(self) -> List[Team]:
        return sorted(self.teams, key=lambda t: t.wins, reverse=True)

    def __str__(self):
        return f"League S{self.season}: {len(self.teams)} teams, {len(self.cards)} cards"
