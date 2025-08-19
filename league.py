# === league.py ===
# Fantasy Clash Royale League - Skeleton

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
        self.cards: Dict[int, Card] = {}
        self.teams: Dict[int, Team] = {}
        self.history: List[Dict] = []

        # init
        self._init_cards()
        self._init_teams(human_team_name)

    # --- Initialization ---
    def _init_cards(self):
        """Generate placeholder cards for now"""
        for cid in range(1, 21):  # just 20 to test UI, later 160+
            card = Card(
                id=cid,
                name=f"Card{cid}",
                ovr=self.rng.randint(60, 95),
                archetype=self.rng.choice(["Tank", "Healer", "Burst", "Control"]),
                atk_type=self.rng.choice(["Melee", "Ranged", "Spell"]),
                stats={"atk": self.rng.randint(40, 100), "def": self.rng.randint(40, 100)},
            )
            self.cards[cid] = card

    def _init_teams(self, human_team_name: Optional[str]):
        """Generate placeholder teams for now"""
        for tid in range(1, 5):  # just 4 teams for now, later 30
            name = human_team_name if tid == 1 and human_team_name else f"Team{tid}"
            gm_name = f"GM{tid}"
            self.teams[tid] = Team(id=tid, name=name, gm=gm_name)

    # --- Draft ---
    def run_draft(self):
        """Stub for draft logic"""
        return {"draft_results": "Not implemented yet"}

    # --- Simcast ---
    def sim_game(self, team1: int, team2: int):
        """Stub for game simulation"""
        return {"result": f"Simulated {self.teams[team1].name} vs {self.teams[team2].name}"}

    # --- Standings ---
    def get_standings(self):
        return sorted(self.teams.values(), key=lambda t: t.wins, reverse=True)

    # --- Leaders & Awards ---
    def get_league_leaders(self, stat="ovr"):
        """Return top 5 cards by stat (placeholder)"""
        return sorted(self.cards.values(), key=lambda c: c.ovr, reverse=True)[:5]

    # --- Cards & Synergies ---
    def get_synergies(self):
        return {"synergies": "Not implemented yet"}

    # --- Patch Notes ---
    def get_patch_notes(self):
        return {"patch": "No buffs/nerfs yet"}

    # --- Playoffs ---
    def get_playoff_bracket(self):
        return {"bracket": "Not implemented yet"}

    # --- Rivalries ---
    def get_rivalries(self):
        return {"rivalries": "Not implemented yet"}

    # --- History & HOF ---
    def get_history(self):
        return self.history

    # --- Twitter Feed ---
    def get_twitter_feed(self):
        return ["No tweets yet"]

    def __str__(self):
        return f"League S{self.season}: {len(self.teams)} teams, {len(self.cards)} cards"

    # ------------------------
    # Home Page Helpers
    # ------------------------

    def get_team_chemistry(self, team_name: str) -> float:
        """Return team chemistry as percentage based on synergies of drafted cards."""
        team = self.teams.get(team_name)
        if not team or not team.roster:
            return 0.0
        # super simple formula: avg synergy bonus across roster
        total = 0
        count = 0
        for card in team.roster:
            total += card.synergy_score
            count += 1
        return (total / max(1, count)) * 100

    def get_standings(self):
        """Return quick standings as a DataFrame."""
        import pandas as pd
        data = []
        for t in self.teams.values():
            data.append({
                "Team": t.name,
                "W": t.wins,
                "L": t.losses,
                "Pct": round(t.wins / max(1, (t.wins + t.losses)), 3)
            })
        df = pd.DataFrame(data).sort_values(["W", "Pct"], ascending=[False, False])
        return df

    def get_team_cards(self, team_name: str):
        """Return list of card objects on a team."""
        team = self.teams.get(team_name)
        return team.roster if team else []

    def get_recent_tweets(self, limit: int = 8):
        """Return a mixed list of GM + fan tweets (recent chatter)."""
        # right now just stub random text
        posts = []
        for _ in range(limit):
            gm = self.rng.choice(list(self.teams.values())).gm
            fan_msg = self.rng.choice([
                "That draft was wild!",
                "No way we lose next game 😤",
                "Buff incoming??",
                "This synergy is broken lol",
                "Trust the process.",
                "We run the league!"
            ])
            if self.rng.random() < 0.5:
                posts.append(f"GM {gm}: {fan_msg}")
            else:
                posts.append(f"Fan: {fan_msg}")
        return posts

    def get_upcoming_games(self, team_name: str, num: int = 3):
        """Return list of upcoming games for a team."""
        schedule = self.schedule.get(team_name, [])
        upcoming = []
        for g in schedule:
            if g["game_num"] >= self.current_game:
                upcoming.append(g)
            if len(upcoming) >= num:
                break
        return upcoming
