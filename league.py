# === league.py ===
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Dict, Optional

# ---------- Card & Team Models ----------
@dataclass
class Card:
    id: int
    name: str
    ovr: int

@dataclass
class Team:
    name: str
    gm: str
    roster: List[Card]

# ---------- Draft Manager ----------
class DraftManager:
    def __init__(self, teams: List[Team], cards: List[Card]):
        self.teams = teams
        self.cards = {c.id: c for c in cards}
        self.available_ids = list(self.cards.keys())

        self.round_num = 1
        self.pick_num = 1
        self.max_rounds = 4
        self.current_index = 0

        self.log: List[str] = []
        self.finished = False

    @property
    def current_gm(self) -> str:
        return self.teams[self.current_index].gm

    def pick_card(self, gm: str, card_id: int):
        if self.finished:
            return
        if card_id not in self.available_ids:
            return

        team = self.teams[self.current_index]
        if team.gm != gm:
            return  # not your turn

        card = self.cards[card_id]
        team.roster.append(card)
        self.available_ids.remove(card_id)

        self.log.append(f"Round {self.round_num}, Pick {self.pick_num}: {gm} drafted {card.name} (OVR {card.ovr})")

        # advance draft
        self.pick_num += 1
        self.current_index += 1
        if self.current_index >= len(self.teams):
            self.current_index = 0
            self.round_num += 1
            self.pick_num = 1
        if self.round_num > self.max_rounds:
            self.finished = True

    def auto_pick(self, gm: str):
        if not self.available_ids:
            return
        best_id = max(self.available_ids, key=lambda cid: self.cards[cid].ovr)
        self.pick_card(gm, best_id)

# ---------- League ----------
class League:
    def __init__(self, seed: int = 1337, human_team_name: Optional[str] = "You"):
        self.rng = random.Random(seed)

        # --- generate cards ---
        self.cards: Dict[int, Card] = {}
        for cid in range(1, 171):  # 170 cards
            name = f"Card{cid}"
            ovr = self.rng.randint(60, 99)
            self.cards[cid] = Card(id=cid, name=name, ovr=ovr)

        # --- generate teams ---
        self.teams: List[Team] = []
        for i in range(30):
            gm_name = human_team_name if i == 0 else f"GM{i}"
            self.teams.append(Team(name=f"Team {i+1}", gm=gm_name, roster=[]))

        # draft state
        self.draft: Optional[DraftManager] = None
        self.draft_in_progress = False

    def __str__(self):
        return f"League: {len(self.teams)} teams, {len(self.cards)} cards"

    # ---------- Draft API ----------
    def start_draft(self):
        self.draft = DraftManager(self.teams, list(self.cards.values()))
        self.draft_in_progress = True

    def draft_pick(self, gm: str, card_id: int):
        if self.draft:
            self.draft.pick_card(gm, card_id)
            if self.draft.finished:
                self.draft_in_progress = False

    def draft_auto_pick(self, gm: str):
        if self.draft:
            self.draft.auto_pick(gm)
            if self.draft.finished:
                self.draft_in_progress = False

    def get_available_cards(self) -> List[Card]:
        if not self.draft:
            return []
        return [self.cards[cid] for cid in self.draft.available_ids]

    def get_draft_log(self) -> List[str]:
        if not self.draft:
            return []
        return self.draft.log

    def get_draft_results(self):
        results = []
        grades: Dict[str, str] = {}
        if not self.draft:
            return results, grades

        for team in self.teams:
            total_ovr = sum(c.ovr for c in team.roster)
            avg_ovr = total_ovr / len(team.roster) if team.roster else 0
            grade = self._grade_from_ovr(avg_ovr)
            grades[team.gm] = grade
            for c in team.roster:
                results.append(f"{team.gm} drafted {c.name} (OVR {c.ovr})")

        return results, grades

    def _grade_from_ovr(self, avg: float) -> str:
        if avg >= 90: return "A"
        if avg >= 80: return "B"
        if avg >= 70: return "C"
        if avg >= 60: return "D"
        return "F"
