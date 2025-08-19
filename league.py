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

# === Milestone 2A: Draft foundation ===

@dataclass
class DraftPick:
    round: int
    pick_num: int
    team: str
    card: str
    ovr: int

class DraftManager:
    def __init__(self, league: League, rounds: int = 4):
        self.league = league
        self.rounds = rounds
        self.current_round = 1
        self.current_pick = 1
        self.picks: List[DraftPick] = []
        # all cards start in the pool
        self.available_cards = set(league.cards.keys())

    def next_pick(self) -> Optional[DraftPick]:
        if self.current_round > self.rounds:
            return None

        # which team is picking?
        team_idx = (self.current_pick - 1) % len(self.league.teams)
        team = self.league.teams[team_idx]

        # choose best card (simplified AI = highest OVR left)
        if len(self.available_cards) == 0:
            return None
        cid = max(self.available_cards, key=lambda c: self.league.cards[c].ovr)
        card = self.league.cards[cid]
        self.available_cards.remove(cid)

        # assign card to team
        team.roster.append(cid)

        pick = DraftPick(
            round=self.current_round,
            pick_num=self.current_pick,
            team=team.name,
            card=card.name,
            ovr=card.ovr,
        )
        self.picks.append(pick)

        # advance draft
        self.current_pick += 1
        if self.current_pick > len(self.league.teams):
            self.current_pick = 1
            self.current_round += 1

        return pick

    def is_finished(self) -> bool:
        return self.current_round > self.rounds

# === Milestone 3A: Human draft support ===

class HumanDraftManager(DraftManager):
    def __init__(self, league: League, rounds: int = 4, human_team_name: Optional[str] = None):
        super().__init__(league, rounds)
        self.human_team = None
        if human_team_name:
            for t in league.teams:
                if t.name == human_team_name:
                    self.human_team = t
                    break

    def next_pick(self, chosen_card_id: Optional[str] = None) -> Optional[DraftPick]:
        if self.current_round > self.rounds:
            return None

        # which team is picking?
        team_idx = (self.current_pick - 1) % len(self.league.teams)
        team = self.league.teams[team_idx]

        # if it's human GM
        if self.human_team and team == self.human_team and chosen_card_id is None:
            # pause so UI can let user pick
            return None

        # pick card
        if self.human_team and team == self.human_team and chosen_card_id:
            cid = chosen_card_id
        else:
            # AI auto-pick highest OVR left
            cid = max(self.available_cards, key=lambda c: self.league.cards[c].ovr)

        if cid not in self.available_cards:
            return None
        card = self.league.cards[cid]
        self.available_cards.remove(cid)

        # assign card
        team.roster.append(cid)

        pick = DraftPick(
            round=self.current_round,
            pick_num=self.current_pick,
            team=team.name,
            card=card.name,
            ovr=card.ovr,
        )
        self.picks.append(pick)

        # advance draft
        self.current_pick += 1
        if self.current_pick > len(self.league.teams):
            self.current_pick = 1
            self.current_round += 1

        return pick
