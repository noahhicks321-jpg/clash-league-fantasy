# === league.py ===
# Fantasy Clash Royale League - Core Engine (Home-ready)

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ---------- Data Models ----------

@dataclass
class Card:
    id: int
    name: str
    ovr: int
    archetype: str
    atk_type: str
    stats: Dict[str, int] = field(default_factory=dict)
    rookie: bool = False   # rookie badge


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

    def record(self) -> str:
        return f"{self.wins}-{self.losses}"


# ---------- League Engine ----------

class League:
    def __init__(self, seed: int = 1337, human_team_name: Optional[str] = "User Team"):
        self.rng = random.Random(seed)

        # Season meta
        self.season: int = 1
        self.current_week: int = 1  # 1..29 (each team plays 29 games in RR)

        # Pools / state
        self.cards: Dict[int, Card] = {}
        self.teams: Dict[int, Team] = {}
        self.human_team_name: Optional[str] = human_team_name
        self.user_team_id: int = 1  # human is team 1 by default

        # Schedule: week -> List[(home_id, away_id)]
        self.schedule_by_week: Dict[int, List[Tuple[int, int]]] = {}
        # Quick lookup for a team's ordered opponents (week-aligned)
        self.team_schedule_index: Dict[int, List[int]] = {}

        # Results log, news, history
        self.results: List[Dict] = []
        self.news_feed: List[str] = []
        self.history: List[str] = []

        # Initialize
        self._init_cards()
        self._init_teams()
        self._init_schedule_round_robin()
        self._seed_preseason_rosters_for_home_display()
        self._seed_preseason_tweets()

    # ---------- Initialization ----------

    def _init_cards(self):
        """Generate ~165 cards with varied archetypes and attack types."""
        archetypes = ["Tank", "Healer", "Burst", "Control", "Utility", "Balanced"]
        atk_types = ["Melee", "Ranged", "Spell"]

        # Aim between 160-170; pick 165
        total_cards = 165
        rookie_count = 4  # rookies per season

        for cid in range(1, total_cards + 1):
            rookie_flag = (cid > total_cards - rookie_count)
            name = self._gen_card_name(cid)
            ovr = self.rng.randint(62, 96)
            archetype = self.rng.choice(archetypes)
            atk_type = self.rng.choice(atk_types)
            stats = {
                "atk": self.rng.randint(50, 100),
                "def": self.rng.randint(50, 100),
                "speed": self.rng.randint(45, 100),
                "hit_speed": self.rng.randint(45, 100),
                "stamina": self.rng.randint(50, 100),
            }
            self.cards[cid] = Card(
                id=cid, name=name, ovr=ovr,
                archetype=archetype, atk_type=atk_type,
                stats=stats, rookie=rookie_flag
            )

    def _init_teams(self):
        """Create 30 unique teams with GM names. Human is team 1."""
        team_names = [
            "Phoenix", "Wyrms", "Valkyries", "Titans", "Spectres", "Sentinels",
            "Drakes", "Ronin", "Warlocks", "Samurai", "Lancers", "Gladiators",
            "Marauders", "Stalkers", "Aces", "Blitz", "Nightfall", "Embers",
            "Cyclones", "Stormbreak", "Invictus", "Onyx", "Eclipse", "Aurora",
            "Nebula", "Tempest", "Rampage", "Genesis", "Revenant"
        ]
        # Guarantee 30 unique names by adding a city prefix
        cities = [
            "Argent", "Blackrock", "Celestia", "Dawnspire", "Emberfall", "Frostgate",
            "Gloomcrest", "Highridge", "Ironvale", "Jadeport", "Kingswatch", "Luminor",
            "Moonreach", "Northwall", "Oakfort", "Pyrestone", "Queensguard", "Rivenshore",
            "Stormhold", "Thornfield", "Umbral", "Valewind", "Westcliff", "Xyra",
            "Yellowspire", "Zephyr", "Ashmar", "Brighthaven", "Cinderbay", "Dreadmoor"
        ]

        for tid in range(1, 31):
            base = team_names[tid - 1]
            city = cities[tid - 1]
            name = f"{city} {base}"
            if tid == self.user_team_id and self.human_team_name:
                name = self.human_team_name  # user override

            gm = self._gen_gm_name(tid)
            self.teams[tid] = Team(id=tid, name=name, gm=gm)

    def _init_schedule_round_robin(self):
        """Create a simple single round-robin schedule (29 weeks)."""
        team_ids = list(self.teams.keys())  # 1..30
        n = len(team_ids)                    # n = 30

        # Round-robin (circle method)
        fixed = team_ids[0]
        others = team_ids[1:]
        weeks = n - 1  # 29 weeks

        self.schedule_by_week = {w: [] for w in range(1, weeks + 1)}
        self.team_schedule_index = {tid: [] for tid in team_ids}

        for w in range(1, weeks + 1):
            pairings = []
            # Current order = [fixed] + others
            order = [fixed] + others
            # Pair 1: fixed vs last of others (to avoid repeats)
            if len(order) % 2 == 1:
                home = order[0]
                away = order[-1]
                pairings.append((home, away))
                # Remaining pairs
                left = order[1: (len(order) - 1) // 2 + 1]
                right = order[(len(order) - 1) // 2 + 1: -1]
                right = list(reversed(right))
            else:
                left = order[: len(order) // 2]
                right = list(reversed(order[len(order) // 2:]))

            # Pair up remaining teams
            if len(order) % 2 == 0:
                for a, b in zip(left, right):
                    pairings.append((a, b))
            else:
                for a, b in zip(left, right):
                    pairings.append((a, b))

            # Save week pairings
            self.schedule_by_week[w] = pairings
            # Fill team index
            for home, away in pairings:
                self.team_schedule_index[home].append(away)
                self.team_schedule_index[away].append(home)

            # Rotate "others"
            if len(others) > 1:
                others = [others[-1]] + others[:-1]

    def _seed_preseason_rosters_for_home_display(self):
        """
        Give the user's team a small preseason roster so Home tab shows data
        even before implementing the draft.
        """
        user_team = self.teams.get(self.user_team_id)
        if not user_team:
            return

        # Pick 4 distinct cards as placeholders (3 starters + 1 backup)
        available = list(self.cards.keys())
        self.rng.shuffle(available)
        picks = available[:4]
        user_team.roster = picks

    def _seed_preseason_tweets(self):
        """Add a handful of GM/fan tweets for the Home news feed."""
        t = self.teams
        sample = [
            f"GM {t[2].gm}: 'This is our year.'",
            f"Fan: 'Did you see {t[5].name} scrim? Nasty!'",
            f"Insider: 'Rookies look sharp in camp.'",
            f"GM {t[10].gm}: 'Respect to {t[1].name}, but we're coming.'",
            f"Analyst: 'Meta may favor Control + Spell this season.'",
        ]
        self.news_feed.extend(sample)

    # ---------- Name Generators ----------

    def _gen_card_name(self, cid: int) -> str:
        # Procedurally generate cool names from syllables
        syll = ["sha", "dor", "wyr", "val", "kai", "zen", "ran", "qua",
                "ion", "dra", "sil", "ark", "lix", "kor", "pyre", "nox",
                "vela", "zho", "ra", "myr"]
        parts = [self.rng.choice(syll).capitalize() for _ in range(self.rng.randint(2, 3))]
        # Add a short suffix based on id to avoid too many duplicates
        suffix = "" if self.rng.random() < 0.6 else f"-{cid%97}"
        return "".join(parts) + suffix

    def _gen_gm_name(self, tid: int) -> str:
        firsts = ["Aiden", "Blake", "Cora", "Dante", "Eira", "Felix", "Gwen", "Hale",
                  "Iris", "Jax", "Kira", "Luca", "Mira", "Nash", "Orin", "Pia",
                  "Quinn", "Rhea", "Soren", "Tess", "Ulric", "Vera", "Wren", "Xane",
                  "Yara", "Zane", "Ayla", "Bryn", "Cael", "Dara"]
        lasts = ["Night", "Storm", "Ash", "Vale", "Wolfe", "Reign", "Frost", "Hale",
                 "Rook", "Dusk", "Blight", "Quell", "Flint", "Locke", "Voss", "Shade",
                 "Cross", "Grimm", "Ryder", "Stone", "Hart", "Crow", "Sable", "Knox",
                 "Fate", "Thorne", "Rayne", "Steel", "Wraith", "Hunt"]
        return f"{firsts[(tid - 1) % len(firsts)]} {lasts[(tid - 1) % len(lasts)]}"

    # ---------- Public API: Home Tab Needs ----------

    def get_season_info(self) -> Dict[str, int]:
        """Return season number and current week pointer."""
        return {"season": self.season, "week": self.current_week}

    def get_quick_news(self, n: int = 8) -> List[str]:
        """Most recent n news lines."""
        return self.news_feed[-n:] if self.news_feed else ["No news yet."]

    def get_user_cards(self) -> List[Card]:
        """Cards currently on the human team (IDs -> Card objects)."""
        team = self.teams.get(self.user_team_id)
        if not team or not team.roster:
            return []
        return [self.cards[cid] for cid in team.roster if cid in self.cards]

    def get_user_team_chemistry(self) -> float:
        """
        Simple chemistry proxy: mean of (atk+def)/2 across roster.
        Returns 0 if no cards yet.
        """
        cards = self.get_user_cards()
        if not cards:
            return 0.0
        vals = [(c.stats["atk"] + c.stats["def"]) / 2 for c in cards]
        return float(statistics.mean(vals))

    def get_upcoming_games(self, n: int = 5) -> List[Tuple[str, str, int]]:
        """
        Next n games for human team starting from current_week.
        Returns list of (user_team_name, opponent_name, week_no).
        """
        uid = self.user_team_id
        user = self.teams[uid]
        if uid not in self.team_schedule_index:
            return []
        opps = self.team_schedule_index[uid]
        start = max(1, self.current_week)
        out: List[Tuple[str, str, int]] = []
        for w in range(start, min(start + n, len(opps) + 1)):
            opp_id = opps[w - 1]
            out.append((user.name, self.teams[opp_id].name, w))
        return out

    def get_standings(self) -> List[Team]:
        """Teams sorted by wins, then crowns differential."""
        return sorted(
            self.teams.values(),
            key=lambda t: (t.wins, t.crowns_for - t.crowns_against),
            reverse=True,
        )

    # ---------- (Optional) Sim Hooks ----------

    def sim_week(self, week: int) -> None:
        """
        Simulate all games in a given week with simple random scoring.
        Updates standings and results.
        """
        if week not in self.schedule_by_week:
            return
        games = self.schedule_by_week[week]
        for home_id, away_id in games:
            h = self.teams[home_id]
            a = self.teams[away_id]
            # lightweight random crowns 0..3
            hs = self.rng.randint(0, 3)
            as_ = self.rng.randint(0, 3)
            # no ties; nudge if equal
            if hs == as_:
                if self.rng.random() < 0.5:
                    hs += 1
                else:
                    as_ += 1
            if hs > as_:
                h.wins += 1
                a.losses += 1
            else:
                a.wins += 1
                h.losses += 1
            h.crowns_for += hs
            h.crowns_against += as_
            a.crowns_for += as_
            a.crowns_against += hs
            self.results.append({
                "week": week,
                "home": h.name, "away": a.name,
                "score": f"{hs}-{as_}"
            })

        # advance pointer if we just simulated the current week
        if week == self.current_week and self.current_week < 29:
            self.current_week += 1

    # ---------- String ----------

    def __str__(self):
        return f"League S{self.season} W{self.current_week}: {len(self.teams)} teams, {len(self.cards)} cards"
