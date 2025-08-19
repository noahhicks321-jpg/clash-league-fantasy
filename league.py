# === league.py ===
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---------- Constants ----------
NUM_TEAMS = 30
ROSTER_SIZE = 4            # 3 starters + 1 backup
STARTERS = 3
BACKUPS = 1
MIN_CARD_POOL = 160
MAX_CARD_POOL = 170

# ---------- Data Classes ----------
@dataclass
class Card:
    id: int
    name: str
    ovr: int

@dataclass
class Team:
    name: str
    roster: List[int]  # card IDs

# ---------- Draft Manager ----------
class DraftManager:
    def __init__(self, league: League, max_rounds: int = 4):
        self.league = league
        self.round = 1
        self.max_rounds = max_rounds
        self.pick_no = 1
        self.total_picks = league.num_teams * max_rounds
        self.log: List[str] = []
        self.done = False

        # Random draft order each season
        self.order = list(league.teams.keys())
        random.shuffle(self.order)
        self.cur_idx = 0

    def current_gm(self) -> str:
        return self.order[self.cur_idx]

    def advance_pick(self):
        """Move to next pick, round, or finish draft."""
        self.cur_idx += 1
        self.pick_no += 1
        if self.cur_idx >= len(self.order):
            self.cur_idx = 0
            self.round += 1
        if self.pick_no > self.total_picks:
            self.done = True
            self.league.draft = None

    def record_pick(self, gm: str, card: Card):
        self.log.append(f"Round {self.round}, Pick {self.pick_no}: {gm} drafted {card.name} (OVR {card.ovr})")

    def auto_pick(self):
        gm = self.current_gm()
        available = self.league.get_available_cards()
        if not available:
            self.advance_pick()
            return
        card = random.choice(available)
        self.league.teams[gm].roster.append(card.id)
        self.record_pick(gm, card)
        self.advance_pick()

    def user_pick(self, card_id: int):
        gm = self.current_gm()
        card = self.league.cards[card_id]
        self.league.teams[gm].roster.append(card.id)
        self.record_pick(gm, card)
        self.advance_pick()

# ---------- League ----------
class League:
    def __init__(self, seed: int = 1337, human_team_name: Optional[str] = "Your Team"):
        random.seed(seed)
        self.season = 1
        self.num_teams = NUM_TEAMS
        self.cards: Dict[int, Card] = {}
        self.teams: Dict[str, Team] = {}
        self.human_team_name = human_team_name
        self.draft: Optional[DraftManager] = None

        self._init_cards()
        self._init_teams()

    # ----- Initialization -----
    def _init_cards(self):
        for cid in range(MIN_CARD_POOL):
            name = f"Card {cid+1}"
            ovr = random.randint(60, 99)
            self.cards[cid] = Card(id=cid, name=name, ovr=ovr)

    def _init_teams(self):
        for i in range(self.num_teams):
            name = self.human_team_name if (i == 0 and self.human_team_name) else f"Team {i+1}"
            self.teams[name] = Team(name=name, roster=[])

    # ----- Draft Controls -----
    def start_draft(self):
        self.draft = DraftManager(self, max_rounds=4)

    def draft_pick(self, card_id: int):
        if self.draft and not self.draft.done:
            self.draft.user_pick(card_id)

    def draft_auto_pick(self):
        if self.draft and not self.draft.done:
            self.draft.auto_pick()

    def get_draft_log(self) -> List[str]:
        if self.draft:
            return self.draft.log
        return []

    def get_available_cards(self) -> List[Card]:
        drafted = {cid for t in self.teams.values() for cid in t.roster}
        return [c for c in self.cards.values() if c.id not in drafted]

    # ----- String -----
    def __str__(self):
        return f"League S{self.season}: {len(self.teams)} teams, {len(self.cards)} cards"
