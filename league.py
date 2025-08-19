# === league.py ===
# Fantasy Clash Royale League Engine - Stable Core

import random
import statistics
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
    def __init__(self, seed=1337, human_team_name: Optional[str] = None):
        self.rng = random.Random(seed)
        self.season = 1

        # Teams and cards
        self.teams: List[Team] = []
        self.cards: Dict[int, Card] = {}
        self.human_team_name = human_team_name

        # Schedule + results
        self.schedule: Dict[str, List[str]] = {}
        self.results: List[Dict] = []

        # News feed (tweets, GM chatter, etc.)
        self.news_feed: List[str] = []

        # Generate data
        self._init_cards()
        self._init_teams()
        self._init_schedule()

    # --- Initialization ---
    def _init_cards(self):
        """Generate placeholder cards (later expand to 160+)."""
        for cid in range(1, 21):  # just 20 cards for now
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
        """Generate 30 teams (1 human + 29 AI)."""
        team_names = [
            "Royal Crushers", "Tower Titans", "Crown Hunters", "Elixir Masters",
            "Bridge Spammers", "P.E.K.K.A Smashers", "Log Lords", "Miner Mafia",
            "Balloon Squad", "Rocket Riders", "Zap Squad", "Hog Riders",
            "Ice Wizards", "Goblin Gang", "Mega Knights", "Golem Pushers",
            "X-Bow Exiles", "Royal Hogs", "Lava Lords", "Inferno Squad",
            "Skeleton Army", "Barbarian Brawlers", "Princess Archers", "Dark Princes",
            "Battle Ram Bashers", "Electro Spirits", "Cannon Carts", "Fireballers",
            "Sparky Shockers", "Magic Archers"
        ]  # 30 unique names

        gm_names = [f"GM {i}" for i in range(1, 31)]

        for tid in range(1, 31):
            name = self.human_team_name if tid == 1 and self.human_team_name else team_names[tid - 1]
            gm = gm_names[tid - 1]
            team = Team(id=tid, name=name, gm=gm)
            self.teams.append(team)

        # Reference human team
        self.user_team = self.teams[0]

    def _init_schedule(self):
        """Generate a simple round-robin schedule for testing."""
        self.schedule = {}
        for t in self.teams:
            self.schedule[t.name] = []
            opponents = [o.name for o in self.teams if o.id != t.id]
            self.rng.shuffle(opponents)
            self.schedule[t.name] = opponents[:5]  # just 5 games each for now

    # --- Standings ---
    def get_standings(self):
        return sorted(self.teams, key=lambda t: t.wins, reverse=True)

    # --- Cards ---
    def get_user_cards(self) -> List[Card]:
        """Return Card objects for the human team (first 3 assigned by default)."""
        if not self.user_team.roster:
            self.user_team.roster = list(self.cards.keys())[:3]
        return [self.cards[cid] for cid in self.user_team.roster]

    # --- Chemistry ---
    def get_user_team_chemistry(self) -> float:
        """Return fake chemistry score 0–100."""
        return self.rng.randint(50, 100)

    # --- Upcoming Games ---
    def get_upcoming_games(self, n=5) -> List[str]:
        return self.schedule.get(self.user_team.name, [])[:n]

    # --- News ---
    def get_quick_news(self, n=5) -> List[str]:
        if not self.news_feed:
            self.news_feed = [
                "GM 12: We're confident heading into the season!",
                "Fan42: Can't wait for the draft tonight!",
                "League Update: Balance patch coming soon!",
                "GM 7: Our synergy is unmatched.",
                "Fan99: Go Hog Riders!!",
            ]
        return self.news_feed[:n]

    # --- Leaders ---
    def get_league_leaders(self, stat="ovr") -> List[Card]:
        return sorted(self.cards.values(), key=lambda c: getattr(c, stat, 0), reverse=True)[:5]

    def __str__(self):
        return f"League S{self.season}: {len(self.teams)} teams, {len(self.cards)} cards"
