# === league.py ===
# Fantasy Clash Royale League - Clean Start

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ---------- Card ----------
@dataclass
class Card:
    id: int
    name: str
    ovr: int
    archetype: str
    atk_type: str
    stats: Dict[str, int] = field(default_factory=dict)


# ---------- Team ----------
@dataclass
class Team:
    id: int
    name: str
    gm: str
    roster: List[int] = field(default_factory=list)  # card IDs
    wins: int = 0
    losses: int = 0
    crowns_for: int = 0
    crowns_against: int = 0


# ---------- League ----------
class League:
    def __init__(self, seed: int = 1337, human_team_name: Optional[str] = None):
        self.rng = random.Random(seed)
        self.season = 1
        self.teams: Dict[int, Team] = {}
        self.cards: Dict[int, Card] = {}
        self.human_team_name = human_team_name

        self._init_cards()
        self._init_teams()

    def _init_cards(self):
        """Generate placeholder cards"""
        for cid in range(1, 21):  # 20 cards for now
            card = Card(
                id=cid,
                name=f"Card{cid}",
                ovr=self.rng.randint(60, 95),
                archetype=self.rng.choice(["Tank", "Healer", "Burst", "Control"]),
                atk_type=self.rng.choice(["Melee", "Ranged", "Spell"]),
                stats={
                    "atk": self.rng.randint(40, 100),
                    "def": self.rng.randint(40, 100),
                },
            )
            self.cards[cid] = card

    def _init_teams(self):
        """Generate placeholder teams"""
        for tid in range(1, 5):  # 4 teams for now
            name = self.human_team_name if tid == 1 and self.human_team_name else f"Team{tid}"
            gm_name = f"GM{tid}"
            self.teams[tid] = Team(id=tid, name=name, gm=gm_name)

    def get_standings(self) -> List[Team]:
        """Return teams sorted by wins"""
        return sorted(self.teams.values(), key=lambda t: t.wins, reverse=True)

    def __str__(self):
        return f"League S{self.season}: {len(self.teams)} teams, {len(self.cards)} cards"
