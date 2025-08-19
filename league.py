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

            self.schedule = self._make_schedule()
        self.news_feed = []  # initialize empty news feed

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

        # ---------- Public API helpers for UI ----------
    def get_user_cards(self):
        """Return list of Card objects for the human player's team."""
        if not hasattr(self, "user_team") or self.user_team is None:
            return []
        return self.user_team.roster

    def get_user_team_chemistry(self) -> float:
        """Return the human team's average chemistry (0–100)."""
        if not hasattr(self, "user_team") or self.user_team is None:
            return 0
        return statistics.mean([c.chemistry for c in self.user_team.roster])

    def get_standings(self):
        """Return standings as a DataFrame-like structure for Streamlit table."""
        import pandas as pd
        data = []
        for t in self.teams:
            data.append({
                "Team": t.name,
                "W": t.wins,
                "L": t.losses,
                "Pct": round(t.wins / max(1, (t.wins + t.losses)), 3)
            })
        return pd.DataFrame(data).sort_values(by="W", ascending=False)

    def get_upcoming_games(self, n: int = 5):
        """Return the next N scheduled games."""
        return self.schedule[:n]

    def get_recent_news(self, n: int = 5):
        """Return recent tweets/news items."""

        def _make_schedule(self):
        """Very simple round-robin schedule: each team plays every other team once."""
        schedule = []
        for i, team_a in enumerate(self.teams):
            for j, team_b in enumerate(self.teams):
                if i < j:  # avoid duplicates
                    schedule.append((team_a.name, team_b.name))
        random.shuffle(schedule)
        return schedule

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

# === Draft System: Snake, Rookies, Live Picks ===

from dataclasses import dataclass

DRAFT_ROUNDS = 4
ROOKIES_PER_SEASON = 4

@dataclass
class DraftPick:
    season: int
    round_num: int
    overall_pick: int
    team_id: int
    team_name: str
    gm_name: str
    card_id: int
    card_name: str
    ovr: int
    is_rookie: bool

def _ensure_league_defaults_for_draft(league: "League"):
    # Safe guards so old skeletons don't crash
    if not hasattr(league, "human_team_name"):
        league.human_team_name = list(league.teams.values())[0].name if league.teams else "Team1"
    if not hasattr(league, "season"):
        league.season = 1
    if not hasattr(league, "draft_manager"):
        league.draft_manager = None

    # Make sure cards have fuller stats + rookie flag
    for c in league.cards.values():
        if not hasattr(c, "stats") or not isinstance(c.stats, dict):
            c.stats = {}
        c.stats.setdefault("atk", league.rng.randint(40, 100))
        c.stats.setdefault("def", league.rng.randint(40, 100))
        c.stats.setdefault("speed", league.rng.randint(40, 100))
        c.stats.setdefault("hit_speed", league.rng.randint(40, 100))
        c.stats.setdefault("stamina", league.rng.randint(40, 100))
        # simple per-card base synergy score (0.40–0.95)
        if not hasattr(c, "synergy_score"):
            c.synergy_score = round(0.4 + league.rng.random() * 0.55, 2)
        if not hasattr(c, "is_rookie"):
            c.is_rookie = False

class DraftManagerSnake:
    """
    4-round snake order draft with user control and live pick feed.
    - Adds 4 rookies to the pool each season with rookie badge.
    - Snake order: R1 1..N, R2 N..1, R3 1..N, R4 N..1
    - Human team can pick; AI picks best by simple heuristic (OVR + fit).
    """

    def __init__(self, league: "League", rounds: int = DRAFT_ROUNDS):
        _ensure_league_defaults_for_draft(league)
        self.league = league
        self.rounds = rounds
        self.round_num = 1
        self.pick_index_in_round = 0  # 0-based within current round
        self.is_active = False

        # determine fixed draft order by team IDs (stable across rounds)
        self.team_order = sorted(self.league.teams.keys())  # [1,2,3,...]
        self.total_picks = self.rounds * len(self.team_order)
        self.completed_picks: list[DraftPick] = []

        # build available pool (IDs not yet on rosters)
        self.available_cards: set[int] = set(self.league.cards.keys())
        for t in self.league.teams.values():
            for cid in t.roster:
                if cid in self.available_cards:
                    self.available_cards.remove(cid)

    # ---------- rookies ----------
    def add_rookies(self, count: int = ROOKIES_PER_SEASON):
        start_id = max(self.league.cards.keys()) + 1 if self.league.cards else 1
        for i in range(count):
            cid = start_id + i
            name = self._gen_rookie_name()
            ovr = self.league.rng.randint(62, 95)
            stats = {
                "atk": self.league.rng.randint(45, 100),
                "def": self.league.rng.randint(45, 100),
                "speed": self.league.rng.randint(45, 100),
                "hit_speed": self.league.rng.randint(45, 100),
                "stamina": self.league.rng.randint(45, 100),
            }
            archetype = self.league.rng.choice(["Tank", "Healer", "Burst", "Control"])
            atk_type = self.league.rng.choice(["Melee", "Ranged", "Spell"])
            card = Card(
                id=cid,
                name=f"{name} (R)",
                ovr=ovr,
                archetype=archetype,
                atk_type=atk_type,
                stats=stats,
            )
            card.is_rookie = True
            card.synergy_score = round(0.45 + self.league.rng.random() * 0.5, 2)
            self.league.cards[cid] = card
            self.available_cards.add(cid)

    def _gen_rookie_name(self):
        # fun-ish generator: two syllables + suffix
        syll = ["sha", "dor", "wyr", "val", "kai", "zen", "ran", "qua", "ion", "dra", "sil", "ark", "lix", "kor"]
        suf = ["ix", "on", "ar", "os", "en", "um", "eth", "orn", "ir", "ae"]
        return self.league.rng.choice(syll).capitalize() + self.league.rng.choice(syll) + self.league.rng.choice(suf)

    # ---------- flow ----------
    def start(self):
        if self.is_active:
            return
        # add rookies at draft start
        self.add_rookies(ROOKIES_PER_SEASON)
        self.is_active = True
        self.round_num = 1
        self.pick_index_in_round = 0

    def reset(self):
        self.completed_picks.clear()
        self.is_active = False
        self.round_num = 1
        self.pick_index_in_round = 0
        # rebuild pool (keep rookies that were added for this season)
        self.available_cards = set(self.league.cards.keys())
        for t in self.league.teams.values():
            for cid in t.roster:
                self.available_cards.discard(cid)

    def current_team_id(self) -> Optional[int]:
        if not self.is_active or self.round_num > self.rounds:
            return None
        n = len(self.team_order)
        if (self.round_num % 2) == 1:
            # odd rounds: 0..n-1
            idx = self.pick_index_in_round
        else:
            # even rounds: n-1..0
            idx = (n - 1) - self.pick_index_in_round
        return self.team_order[idx]

    def is_human_turn(self) -> bool:
        tid = self.current_team_id()
        if tid is None:
            return False
        team = self.league.teams[tid]
        return team.name == self.league.human_team_name

    def remaining_picks_in_round(self) -> int:
        return len(self.team_order) - self.pick_index_in_round

    def _advance(self):
        # move to next pick / round
        self.pick_index_in_round += 1
        if self.pick_index_in_round >= len(self.team_order):
            self.pick_index_in_round = 0
            self.round_num += 1
        # done?
        if self.round_num > self.rounds:
            self.is_active = False

    # ---------- selection ----------
    def _score_for_team(self, team: "Team", cid: int) -> float:
        """Simple AI score: OVR + small synergy fit with existing roster."""
        card = self.league.cards[cid]
        base = card.ovr
        # synergy: +2 per already owned same archetype (very simple)
        same_arch = 0
        for rcid in team.roster:
            if self.league.cards[rcid].archetype == card.archetype:
                same_arch += 1
        return base + same_arch * 2.0

    def ai_pick_best(self, team: "Team") -> Optional[DraftPick]:
        if not self.available_cards:
            return None
        cid = max(self.available_cards, key=lambda x: self._score_for_team(team, x))
        return self._complete_pick(team, cid)

    def human_pick(self, cid: int) -> Optional[DraftPick]:
        tid = self.current_team_id()
        if tid is None:
            return None
        team = self.league.teams[tid]
        if team.name != self.league.human_team_name:
            return None
        if cid not in self.available_cards:
            return None
        return self._complete_pick(team, cid)

    def _complete_pick(self, team: "Team", cid: int) -> DraftPick:
        self.available_cards.discard(cid)
        team.roster.append(cid)
        card = self.league.cards[cid]
        overall_pick = len(self.completed_picks) + 1
        pick = DraftPick(
            season=self.league.season,
            round_num=self.round_num,
            overall_pick=overall_pick,
            team_id=team.id,
            team_name=team.name,
            gm_name=team.gm,
            card_id=cid,
            card_name=card.name,
            ovr=card.ovr,
            is_rookie=getattr(card, "is_rookie", False),
        )
        self.completed_picks.append(pick)
        self._advance()
        return pick

    # ---------- info for UI ----------
    def available_cards_table(self) -> list[dict]:
        rows = []
        for cid in sorted(self.available_cards, key=lambda i: self.league.cards[i].ovr, reverse=True):
            c = self.league.cards[cid]
            rows.append({
                "id": cid,
                "name": c.name,
                "ovr": c.ovr,
                "rookie": getattr(c, "is_rookie", False),
                "archetype": c.archetype,
                "atk_type": c.atk_type,
                "atk": c.stats.get("atk", 0),
                "def": c.stats.get("def", 0),
                "speed": c.stats.get("speed", 0),
                "hit_speed": c.stats.get("hit_speed", 0),
                "stamina": c.stats.get("stamina", 0),
                "base_synergy": getattr(c, "synergy_score", 0.0),
            })
        return rows

    def last_picks_table(self, limit: int = 20) -> list[dict]:
        out = []
        for p in self.completed_picks[-limit:]:
            out.append({
                "Round": p.round_num,
                "Pick": p.overall_pick,
                "Team": p.team_name,
                "GM": p.gm_name,
                "Card": p.card_name,
                "OVR": p.ovr,
                "Rookie": "🟢" if p.is_rookie else "",
            })
        return out

# -------- League convenience API to control the draft --------
def league_start_draft(self: "League"):
    _ensure_league_defaults_for_draft(self)
    self.draft_manager = DraftManagerSnake(self, rounds=DRAFT_ROUNDS)
    self.draft_manager.start()

def league_reset_draft(self: "League"):
    _ensure_league_defaults_for_draft(self)
    if self.draft_manager:
        self.draft_manager.reset()

def league_sim_next_pick(self: "League"):
    _ensure_league_defaults_for_draft(self)
    dm = self.draft_manager
    if not dm or not dm.is_active:
        return None
    tid = dm.current_team_id()
    if tid is None:
        return None
    team = self.teams[tid]
    # if it's human's turn, don't sim (UI will handle)
    if team.name == self.human_team_name:
        return None
    return dm.ai_pick_best(team)

def league_human_pick(self: "League", card_id: int):
    _ensure_league_defaults_for_draft(self)
    dm = self.draft_manager
    if not dm or not dm.is_active:
        return None
    return dm.human_pick(card_id)

def league_sim_to_user_turn(self: "League", hard_stop_if_finished: bool = True):
    _ensure_league_defaults_for_draft(self)
    dm = self.draft_manager
    if not dm or not dm.is_active:
        return
    # run AI picks until human turn or draft ends
    while dm.is_active and not dm.is_human_turn():
        tid = dm.current_team_id()
        if tid is None:
            break
        team = self.teams[tid]
        dm.ai_pick_best(team)
    if hard_stop_if_finished and not dm.is_active:
        return

def league_sim_to_end(self: "League"):
    _ensure_league_defaults_for_draft(self)
    dm = self.draft_manager
    if not dm or not dm.is_active:
        return
    while dm.is_active:
        if dm.is_human_turn():
            # if it's the human turn, stop so UI doesn't pick for them
            break
        tid = dm.current_team_id()
        if tid is None:
            break
        team = self.teams[tid]
        dm.ai_pick_best(team)

# bind helper methods onto League dynamically (so you don't have to edit the class body above)
League.start_draft = league_start_draft
League.reset_draft = league_reset_draft
League.sim_next_pick = league_sim_next_pick
League.human_pick = league_human_pick
League.sim_to_user_turn = league_sim_to_user_turn
League.sim_to_end = league_sim_to_end



