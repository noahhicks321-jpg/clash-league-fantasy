# === league.py ===
# Fantasy Clash Royale League Engine
# Spec: v14 condensed implementation
# - 30 teams (1 human GM + 29 AI)
# - Card pool 160–170, stats 0–100, OVR
# - Archetypes, 90+ synergy scaffold, seasonal synergy shifts (2–5)
# - Patch notes before draft: buff low pick/usage, nerf high pick/usage
# - Draft: lottery + combine, 4 picks/team (3 starters + 1 backup)
# - Draft grades (A–F): OVR, synergy fit, value
# - Sim: 75% power / 25% luck, crowns, contribution %, fatigue
# - Rivalries: intensity +2% boost for 2 games after rivalry win
# - Leaders, awards, All-Star (fan voting stub), playoffs/bracket
# - Hall of Legends (HOF formula), history, trends
# - Public API methods for UI

from __future__ import annotations

import math
import random
import statistics
import string
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
from itertools import combinations, product


# ---------- RNG seeding helper ----------
DEFAULT_SEED = 1337
def seeded_rand() -> random.Random:
    # For reproducibility across runs within a season; the app can reset seed each season if desired.
    return random.Random()


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

# Regular season length (each team plays each other once -> 29) or set a fixed schedule
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


# ---------- Synergy Model ----------

@dataclass
class Synergy:
    """Represents a synergy rule."""
    code: str
    name: str
    description: str
    # Simple rule: activated if (archetype or atk_type) combos are present among starters.
    requires_archetypes: Set[Archetype] = field(default_factory=set)
    requires_atktypes: Set[AtkType] = field(default_factory=set)
    # Effect: a small percentage multiplier to effective power when active
    power_mult: float = 1.0
    # Track balance history
    history: List[Tuple[int, float]] = field(default_factory=list)  # (season, power_mult)

    def active(self, starters: List["Card"]) -> bool:
        a_set = {c.archetype for c in starters}
        t_set = {c.atk_type for c in starters}
        if self.requires_archetypes and not self.requires_archetypes.issubset(a_set):
            return False
        if self.requires_atktypes and not self.requires_atktypes.issubset(t_set):
            return False
        return True


# ---------- Core Data ----------

_card_id_counter = 1
def next_card_id() -> int:
    global _card_id_counter
    cid = _card_id_counter
    _card_id_counter += 1
    return cid

@dataclass
class Card:
    id: int
    name: str
    archetype: Archetype
    atk_type: AtkType
    atk: int
    defense: int
    speed: int
    hit_speed: int
    stamina: int
    seasons_left: int
    rookie_season: int
    seasonal_special: bool = False
    legend: bool = False

    # dynamic / career
    ovr: int = 0
    games_played: int = 0
    crowns_total: int = 0
    crowns_high: int = 0
    contribution_sum: float = 0.0
    usage_games: int = 0
    teams_history: List[str] = field(default_factory=list)
    awards: Counter = field(default_factory=Counter)  # MVP, MIP, ALL_STAR, MOTY, ALL_TEAM
    all_star_appearances: int = 0
    pick_seasons: int = 0  # seasons where drafted

    # patch tracking
    ovr_history: List[Tuple[int, int]] = field(default_factory=list)  # (season, ovr)
    stat_history: List[Tuple[int, Dict[str, int]]] = field(default_factory=list)
    patch_reactions: List[str] = field(default_factory=list)

    def compute_ovr(self) -> int:
        # Weighted average, normalize to 0–100
        # Tanks value DEF+Stamina, Healer value Stamina+Hit Speed, Burst value ATK+Speed,
        # Control value Speed+Hit Speed, Utility balanced, Balanced even
        if self.archetype == Archetype.TANK:
            weights = dict(atk=0.15, defense=0.35, speed=0.15, hit_speed=0.15, stamina=0.20)
        elif self.archetype == Archetype.HEALER:
            weights = dict(atk=0.15, defense=0.15, speed=0.15, hit_speed=0.25, stamina=0.30)
        elif self.archetype == Archetype.BURST:
            weights = dict(atk=0.35, defense=0.10, speed=0.25, hit_speed=0.15, stamina=0.15)
        elif self.archetype == Archetype.CONTROL:
            weights = dict(atk=0.15, defense=0.20, speed=0.25, hit_speed=0.25, stamina=0.15)
        elif self.archetype == Archetype.UTILITY:
            weights = dict(atk=0.20, defense=0.20, speed=0.20, hit_speed=0.20, stamina=0.20)
        else:  # BALANCED
            weights = dict(atk=0.20, defense=0.20, speed=0.20, hit_speed=0.20, stamina=0.20)
        score = (
            self.atk * weights["atk"] +
            self.defense * weights["defense"] +
            self.speed * weights["speed"] +
            self.hit_speed * weights["hit_speed"] +
            self.stamina * weights["stamina"]
        )
        self.ovr = max(0, min(100, int(round(score))))
        return self.ovr

    # Convenience views
    def usage_pct(self) -> float:
        return (self.usage_games / max(1, self.games_played)) * 100.0

    def pick_rate_pct(self, seasons_elapsed: int) -> float:
        eligible = max(1, seasons_elapsed - (self.rookie_season - 1))
        eligible = min(eligible, SEASON_MAX_LIFE)
        return (self.pick_seasons / eligible) * 100.0

@dataclass
class GameResult:
    season: int
    week: int
    home: str
    away: str
    home_crowns: int
    away_crowns: int
    details: Dict[str, Dict[int, int]]  # team -> {card_id: crowns_scored}
    highlights: List[str] = field(default_factory=list)
    rivalry_proc: Optional[str] = None
    win_prob_series: List[Tuple[int, float]] = field(default_factory=list)  # (second, prob_home)

@dataclass
class DraftGrade:
    team: str
    letter: str
    score: float
    components: Dict[str, float]  # {"ovr":..., "synergy":..., "value":...}

@dataclass
class PatchChange:
    season: int
    card_id: Optional[int]
    stat_deltas: Dict[str, int]
    ovr_before: Optional[int]
    ovr_after: Optional[int]
    reason: str  # "buff_low_usage" | "nerf_high_usage" | "synergy_shift" | "discovery"
    msg: str

@dataclass
class AwardWinners:
    season: int
    mvp: Optional[int]
    most_improved: Optional[int]
    all_first: List[int]
    all_second: List[int]
    all_third: List[int]
    moty: List[Tuple[int, int]]  # [(game_id, card_id)] simplified
    all_stars: List[int]

@dataclass
class Team:
    name: str
    gm_name: str
    gm_style: str
    gm_social: str
    gm_rivalry: str
    roster: List[int] = field(default_factory=list)  # card ids
    starters: List[int] = field(default_factory=list)  # 3
    backup: Optional[int] = None
    wins: int = 0
    losses: int = 0
    crowns_for: int = 0
    crowns_against: int = 0
    rivalry_boost_games_left: int = 0
    rivals: Dict[str, int] = field(default_factory=dict)  # team_name -> intensity
    rings: int = 0
    dynasty_points: int = 0  # accumulate for dynasty tag

    # season-local stats
    season_card_crowns: Counter = field(default_factory=Counter)  # card_id -> crowns
    season_card_contrib: Counter = field(default_factory=Counter)  # card_id -> contrib sum

    def record_str(self) -> str:
        return f"{self.wins}-{self.losses}"

@dataclass
class SeasonHistory:
    season: int
    champion: Optional[str] = None
    finalists: Tuple[Optional[str], Optional[str]] = (None, None)
    awards: Optional[AwardWinners] = None
    draft_grades: List[DraftGrade] = field(default_factory=list)
    leaders: Dict[str, List[int]] = field(default_factory=dict)
    patch_notes: List[PatchChange] = field(default_factory=list)
    synergy_notes: List[PatchChange] = field(default_factory=list)


# ---------- League Engine ----------

class League:
    def __init__(self, seed: Optional[int] = None, human_team_name: Optional[str] = None):
        self.rng = random.Random(seed if seed is not None else DEFAULT_SEED)
        self.season = 1
        self.teams: Dict[str, Team] = {}
        self.cards: Dict[int, Card] = {}
        self.synergies: Dict[str, Synergy] = {}
        self.history: List[SeasonHistory] = []
        self.game_log: List[GameResult] = []
        self.playoff_bracket: List[Tuple[str, str]] = []  # pairs per round
        self.all_star_votes: Counter = Counter()

        self._generate_teams(human_team_name)
        self._generate_synergies()
        self._generate_card_pool()

    # ----- Generation -----

    def _generate_teams(self, human_team_name: Optional[str]):
        names = TEAM_WORDS.copy()
        self.rng.shuffle(names)
        for i in range(NUM_TEAMS):
            tname = names[i % len(names)]
            # Ensure unique-ish by appending city-style tag
            city = self._random_city_tag()
            full = f"{city} {tname}"
            if i == 0 and human_team_name:
                full = human_team_name
            gm = self._random_name()
            style = self.rng.choice(GM_STYLES)
            social = self.rng.choice(GM_SOCIAL)
            riv = self.rng.choice(GM_RIVALRY)
            self.teams[full] = Team(name=full, gm_name=gm, gm_style=style, gm_social=social, gm_rivalry=riv)
        # seed some rivalries
        tlist = list(self.teams.keys())
        for a, b in combinations(tlist, 2):
            if self.rng.random() < 0.06:
                self.teams[a].rivals[b] = RIVALRY_INITIAL + self.rng.randint(0, 6)
                self.teams[b].rivals[a] = RIVALRY_INITIAL + self.rng.randint(0, 6)

    def _random_city_tag(self) -> str:
        cities = ["Aether", "Drakon", "Zenith", "Onyx", "Nova", "Obsidian", "Sol", "Luna", "Orion",
                  "Helix", "Nexus", "Volt", "Ember", "Echo", "Vanta", "Nyx"]
        return self.rng.choice(cities)

    def _random_name(self) -> str:
        parts = self.rng.choice([2, 3])
        s = "".join(self.rng.choice(NAME_SYLLABLES) for _ in range(parts))
        return s.capitalize()

    def _generate_synergies(self):
        # Scaffold ~100 synergies mixing archetype and atktype requirements
        codes = []
        idx = 1
        # Archetype pair synergies
        for a1, a2 in product(list(Archetype), repeat=2):
            if a1 == a2: 
                continue
            codes.append(Synergy(
                code=f"SYN{idx:03d}",
                name=f"{a1.value}+{a2.value}",
                description=f"Combine {a1.value} and {a2.value} for tempo swing.",
                requires_archetypes={a1, a2},
                power_mult=1.03 + (0.01 * (idx % 3))
            ))
            idx += 1
            if idx > 60:
                break
        # AtkType set synergies
        for combo in [{AtkType.MELEE, AtkType.RANGED}, {AtkType.RANGED, AtkType.SPELL}, {AtkType.MELEE, AtkType.SPELL},
                      {AtkType.MELEE, AtkType.RANGED, AtkType.SPELL}]:
            codes.append(Synergy(
                code=f"SYN{idx:03d}",
                name="+".join(sorted([t.value for t in combo])),
                description="Diverse damage profile.",
                requires_atktypes=combo,
                power_mult=1.04 if len(combo) == 3 else 1.02
            ))
            idx += 1
        # A few special legendaries
        for a in Archetype:
            codes.append(Synergy(
                code=f"SYN{idx:03d}",
                name=f"Legendary {a.value} Chain",
                description=f"Two {a.value}s and any Control or Utility.",
                requires_archetypes={a},
                power_mult=1.05
            ))
            idx += 1
        # Trim to ~95
        self.synergies = {s.code: s for s in codes[:95]}

    def _generate_card_pool(self):
        total = self.rng.randint(MIN_CARD_POOL, MAX_CARD_POOL)
        for _ in range(total):
            cid = next_card_id()
            name = self._generate_card_name()
            arche = self.rng.choice(list(Archetype))
            atype = self.rng.choice(list(AtkType))
            # base stats 40–90 with small variance
            stats = {
                "atk": self.rng.randint(45, 90),
                "defense": self.rng.randint(45, 90),
                "speed": self.rng.randint(45, 90),
                "hit_speed": self.rng.randint(45, 90),
                "stamina": self.rng.randint(45, 90),
            }
            seasons_left = self.rng.randint(SEASON_MIN_LIFE, SEASON_MAX_LIFE)
            card = Card(
                id=cid, name=name, archetype=arche, atk_type=atype,
                atk=stats["atk"], defense=stats["defense"], speed=stats["speed"],
                hit_speed=stats["hit_speed"], stamina=stats["stamina"],
                seasons_left=seasons_left, rookie_season=self.season
            )
            card.compute_ovr()
            card.ovr_history.append((self.season, card.ovr))
            card.stat_history.append((self.season, dict(stats)))
            self.cards[cid] = card

        # Seasonal special
        special_id = self.rng.choice(list(self.cards.keys()))
        self.cards[special_id].seasonal_special = True

    def _generate_card_name(self) -> str:
        # cool-sounding generator
        left = self._random_name()
        right = self.rng.choice(["Wyrm", "Valkyrie", "Drake", "Spectre", "Arclight", "Nocturne", "Aegis", "Tempest", "Ember", "Nighthawk"])
        return f"{left} {right}"

    # ----- Season Flow -----

    def run_full_season(self) -> SeasonHistory:
        hist = SeasonHistory(season=self.season)

        # 1) Patch Notes (buff/nerf & synergy shifts)
        patches = self._generate_patch_notes()
        hist.patch_notes = patches["cards"]
        hist.synergy_notes = patches["synergies"]

        # 2) Draft: lottery + combine + picks + grades
        draft_grades = self._run_draft()
        hist.draft_grades = draft_grades

        # 3) Regular season schedule + games
        schedule = self._make_schedule()
        week = 1
        for (home, away) in schedule:
            result = self._simulate_game(home, away, week)
            self.game_log.append(result)
            week += 1

        # 4) Standings & Playoffs
        bracket = self._seed_playoffs()
        self.playoff_bracket = bracket.copy()
        champion, finalists = self._run_playoffs(bracket)

        # 5) Awards (MVP, MIP, All-Teams, All-Star)
        awards = self._compute_awards()
        hist.awards = awards
        hist.champion = champion
        hist.finalists = finalists

        # 6) Leaders, history, HOF / retirements / rookies
        self._update_leaders_and_history(hist)
        self._handle_retirements_and_rookies()

        # Season advance
        self.season += 1
        # Rivalry decay
        self._decay_rivalries()

        return hist

    # ----- Patch Notes & Meta -----

    def _generate_patch_notes(self) -> Dict[str, List[PatchChange]]:
        notes_cards: List[PatchChange] = []
        notes_syn: List[PatchChange] = []

        # Identify usage/pick rates (from previous seasons)
        usage_map = {cid: self.cards[cid].usage_pct() for cid in self.cards}
        # Use pick seasons as crude pick rate if seasons>1
        pick_map = {cid: self.cards[cid].pick_rate_pct(self.season) for cid in self.cards}

        # Target pools
        low_usage = sorted(self.cards.values(), key=lambda c: (pick_map[c.id], usage_map[c.id]))[:max(8, len(self.cards)//20)]
        high_usage = sorted(self.cards.values(), key=lambda c: (pick_map[c.id], usage_map[c.id]), reverse=True)[:max(8, len(self.cards)//20)]

        # Buff low usage
        for card in low_usage:
            deltas = self._buff_card(card)
            msg = f"Buffed {card.name} (+{sum(max(0, v) for v in deltas.values())} total) to encourage diversity."
            notes_cards.append(PatchChange(
                season=self.season, card_id=card.id, stat_deltas=deltas,
                ovr_before=card.ovr, ovr_after=card.compute_ovr(), reason="buff_low_usage", msg=msg
            ))
            card.ovr_history.append((self.season, card.ovr))
            card.stat_history.append((self.season, dict(
                atk=card.atk, defense=card.defense, speed=card.speed, hit_speed=card.hit_speed, stamina=card.stamina
            )))
            card.patch_reactions.append(self._gm_or_fan_reaction(card, buff=True))

        # Nerf high usage
        for card in high_usage:
            deltas = self._nerf_card(card)
            msg = f"Nerfed {card.name} (−{abs(sum(min(0, v) for v in deltas.values()))} total) to reduce dominance."
            notes_cards.append(PatchChange(
                season=self.season, card_id=card.id, stat_deltas=deltas,
                ovr_before=card.ovr, ovr_after=card.compute_ovr(), reason="nerf_high_usage", msg=msg
            ))
            card.ovr_history.append((self.season, card.ovr))
            card.stat_history.append((self.season, dict(
                atk=card.atk, defense=card.defense, speed=card.speed, hit_speed=card.hit_speed, stamina=card.stamina
            )))
            card.patch_reactions.append(self._gm_or_fan_reaction(card, buff=False))

        # 2–5 synergy shifts
        syn_list = list(self.synergies.values())
        self.rng.shuffle(syn_list)
        change_count = self.rng.randint(2, 5)
        for s in syn_list[:change_count]:
            before = s.power_mult
            shift = self.rng.choice([-0.02, -0.01, 0.01, 0.02])
            s.power_mult = max(0.95, min(1.10, round(s.power_mult + shift, 3)))
            s.history.append((self.season, s.power_mult))
            direction = "buffed" if s.power_mult > before else "nerfed"
            notes_syn.append(PatchChange(
                season=self.season, card_id=None, stat_deltas={},
                ovr_before=None, ovr_after=None, reason="synergy_shift",
                msg=f"Synergy {s.name} {direction}: {before:.2f}→{s.power_mult:.2f}"
            ))

        # Meta summary “tweet storms” can be produced by UI from notes above.
        return {"cards": notes_cards, "synergies": notes_syn}

    def _buff_card(self, c: Card) -> Dict[str, int]:
        deltas = {}
        for stat in ["atk", "defense", "speed", "hit_speed", "stamina"]:
            delta = self.rng.choice([0, 1, 2, 3])
            if delta:
                new_val = max(0, min(100, getattr(c, stat) + delta))
                setattr(c, stat, new_val)
                deltas[stat] = delta
        return deltas

    def _nerf_card(self, c: Card) -> Dict[str, int]:
        deltas = {}
        for stat in ["atk", "defense", "speed", "hit_speed", "stamina"]:
            delta = -self.rng.choice([0, 1, 2, 3])
            if delta:
                new_val = max(0, min(100, getattr(c, stat) + delta))
                setattr(c, stat, new_val)
                deltas[stat] = delta
        return deltas

    def _gm_or_fan_reaction(self, card: Card, buff: bool) -> str:
        if buff:
            return f"Fan: '{card.name} finally got love. Patch W.'"
        else:
            return f"GM: 'Can’t believe {card.name} got nerfed before draft... rigged.'"

    # ----- Draft -----

    def _run_draft(self) -> List[DraftGrade]:
        # Reset rosters & season stats
        for t in self.teams.values():
            t.roster.clear()
            t.starters.clear()
            t.backup = None
            t.wins = t.losses = 0
            t.crowns_for = t.crowns_against = 0
            t.season_card_crowns.clear()
            t.season_card_contrib.clear()
            t.rivalry_boost_games_left = 0

        order = self._draft_lottery_order()
        # Rookie class (4 rookies enter, 3 retire handled later)
        rookies = self._generate_rookies(4)

        # Draft board = all cards with seasons_left>0
        board = [c for c in self.cards.values() if c.seasons_left > 0]
        # Increase pick_seasons when drafted (will count per season at end)
        taken: Set[int] = set()
        # Combine measures (UI can display)
        combine = self._draft_combine_view(rookies + board)

        # 4 rounds snake draft
        rounds = ROSTER_SIZE
        for rnd in range(rounds):
            snake = order if rnd % 2 == 0 else list(reversed(order))
            for team_name in snake:
                pick = self._choose_best_pick(team_name, board, taken, rnd)
                if not pick:
                    continue
                self.teams[team_name].roster.append(pick.id)
                taken.add(pick.id)
        # set starters/backups
        for t in self.teams.values():
            picked_cards = [self.cards[cid] for cid in t.roster]
            picked_cards.sort(key=lambda c: c.ovr, reverse=True)
            t.starters = [c.id for c in picked_cards[:STARTERS]]
            t.backup = picked_cards[STARTERS].id if len(picked_cards) > STARTERS else None
            for cid in t.roster:
                self.cards[cid].pick_seasons += 1
                self.cards[cid].teams_history.append(t.name)

        # Grades
        grades = self._compute_draft_grades(order)
        return grades

    def _draft_lottery_order(self) -> List[str]:
        # Simple: previous season standings stored in history; use last season losses to weight lottery
        if self.history:
            last_hist = self.history[-1]
            # Build from last standings: approximate by team crowns_for differential
            team_perf = {t.name: t.wins - t.losses for t in self.teams.values()}
            # Poorer teams get higher chance
            names = list(self.teams.keys())
            self.rng.shuffle(names)
            names.sort(key=lambda n: team_perf.get(n, 0))
            return names
        else:
            # Season 1: random
            names = list(self.teams.keys())
            self.rng.shuffle(names)
            return names

    def _generate_rookies(self, count: int) -> List[Card]:
        new_cards = []
        for _ in range(count):
            cid = next_card_id()
            name = self._generate_card_name()
            arche = self.rng.choice(list(Archetype))
            atype = self.rng.choice(list(AtkType))
            base = self.rng.randint(40, 88)
            # rookies with hidden variance
            stats = {
                "atk": base + self.rng.randint(-5, 10),
                "defense": base + self.rng.randint(-5, 10),
                "speed": base + self.rng.randint(-5, 10),
                "hit_speed": base + self.rng.randint(-5, 10),
                "stamina": base + self.rng.randint(-5, 10),
            }
            for k in stats:
                stats[k] = max(35, min(95, stats[k]))
            seasons_left = self.rng.randint(SEASON_MIN_LIFE, SEASON_MAX_LIFE)
            card = Card(
                id=cid, name=name, archetype=arche, atk_type=atype,
                atk=stats["atk"], defense=stats["defense"], speed=stats["speed"],
                hit_speed=stats["hit_speed"], stamina=stats["stamina"],
                seasons_left=seasons_left, rookie_season=self.season
            )
            card.compute_ovr()
            card.ovr_history.append((self.season, card.ovr))
            card.stat_history.append((self.season, dict(stats)))
            self.cards[cid] = card
            new_cards.append(card)
        return new_cards

    def _draft_combine_view(self, cards: List[Card]) -> Dict[int, Dict]:
        # Expose some stats + an uncertainty tag (UI can show)
        view = {}
        for c in cards:
            view[c.id] = {
                "name": c.name,
                "archetype": c.archetype.value,
                "atk_type": c.atk_type.value,
                "ovr": c.ovr,
                "variance": self.rng.choice(["low", "medium", "high"]),
            }
        return view

    def _choose_best_pick(self, team_name: str, board: List[Card], taken: Set[int], rnd: int) -> Optional[Card]:
        # Heuristic: GM style influences drafting
        team = self.teams[team_name]
        candidates = [c for c in board if c.id not in taken and c.seasons_left > 0]
        if not candidates:
            return None

        # Score candidate by OVR + synergy fit with current roster starters
        current_starters = [self.cards[cid] for cid in team.starters] if team.starters else []

        def synergy_fit_score(card: Card) -> float:
            starters = (current_starters + [card])[:STARTERS]
            return self._effective_synergy_multiplier(starters) - 1.0  # 0.0 baseline

        def value_score(card: Card) -> float:
            # approximate "draft value" by how high OVR relative to round
            round_bias = max(0, 3 - rnd) * 2
            return (card.ovr / 100.0) + (round_bias / 10.0)

        def style_bias(card: Card) -> float:
            if team.gm_style == "star_chaser":
                return card.ovr / 100.0
            if team.gm_style == "synergy_focused":
                return synergy_fit_score(card) * 5.0
            if team.gm_style == "risk_taker":
                return self.rng.uniform(-0.05, 0.05)
            return 0.0  # conservative

        best = max(candidates, key=lambda c: (c.ovr / 100.0) + synergy_fit_score(c) + value_score(c) * 0.5 + style_bias(c))
        return best

    def _effective_synergy_multiplier(self, starters: List[Card]) -> float:
        mult = 1.0
        for s in self.synergies.values():
            if s.active(starters):
                mult *= s.power_mult
        # Cap to reasonable range
        return max(0.9, min(1.2, mult))

    def _compute_draft_grades(self, order: List[str]) -> List[DraftGrade]:
        grades: List[DraftGrade] = []
        # Baselines per team
        for team_name in order:
            t = self.teams[team_name]
            picked = [self.cards[cid] for cid in t.roster]
            if not picked:
                grades.append(DraftGrade(team=team_name, letter="C", score=75.0, components={"ovr": 0, "synergy": 0, "value": 0}))
                continue
            avg_ovr = statistics.mean(c.ovr for c in picked)
            # Synergy fit using starters
            starters = [self.cards[cid] for cid in t.starters]
            synergy_fit = (self._effective_synergy_multiplier(starters) - 1.0) * 100.0  # 0–20 roughly
            # Draft value: compare their average pick OVR to league average
            league_avg = statistics.mean(self.cards[cid].ovr for cid in t.roster)
            value = (avg_ovr - league_avg)  # small; placeholder (in practice compare to round means)

            score = (GRADE_W_OVR * avg_ovr) + (GRADE_W_SYNERGY * (50 + synergy_fit)) + (GRADE_W_VALUE * (50 + value))
            letter = self._letter_from_score(score)
            grades.append(DraftGrade(team=team_name, letter=letter, score=score, components={
                "ovr": avg_ovr, "synergy": synergy_fit, "value": value
            }))
        return grades

    def _letter_from_score(self, score: float) -> str:
        if score >= 90: return "A+"
        if score >= 85: return "A"
        if score >= 80: return "A-"
        if score >= 75: return "B+"
        if score >= 70: return "B"
        if score >= 65: return "B-"
        if score >= 60: return "C+"
        if score >= 55: return "C"
        if score >= 50: return "C-"
        if score >= 45: return "D+"
        if score >= 40: return "D"
        return "F"

    # ----- Schedule & Simulation -----

    def _make_schedule(self) -> List[Tuple[str, str]]:
        teams = list(self.teams.keys())
        schedule: List[Tuple[str, str]] = []
        self.rng.shuffle(teams)
        # round-robin once
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                schedule.append((teams[i], teams[j]))
        self.rng.shuffle(schedule)
        # Trim to ~29 games/team: schedule length approx NUM_TEAMS*(NUM_TEAMS-1)/2 already fits
        return schedule

    def _simulate_game(self, home: str, away: str, week: int) -> GameResult:
        t_home = self.teams[home]
        t_away = self.teams[away]
        starters_home = [self.cards[cid] for cid in t_home.starters]
        starters_away = [self.cards[cid] for cid in t_away.starters]
        # Apply rivalry win post-buff
        mult_home = 1.0 + (RIVALRY_WIN_BUFF_PCT if t_home.rivalry_boost_games_left > 0 else 0.0)
        mult_away = 1.0 + (RIVALRY_WIN_BUFF_PCT if t_away.rivalry_boost_games_left > 0 else 0.0)
        if t_home.rivalry_boost_games_left > 0: t_home.rivalry_boost_games_left -= 1
        if t_away.rivalry_boost_games_left > 0: t_away.rivalry_boost_games_left -= 1

        # Team effective power
        eff_home = self._team_effective_power(starters_home) * mult_home
        eff_away = self._team_effective_power(starters_away) * mult_away

        # Luck factor
        luck_home = 0.9 + self.rng.random() * 0.2
        luck_away = 0.9 + self.rng.random() * 0.2

        score_home = POWER_WEIGHT * eff_home + LUCK_WEIGHT * luck_home
        score_away = POWER_WEIGHT * eff_away + LUCK_WEIGHT * luck_away

        # Convert to crowns (0–3 each side, no ties by tie-breaker crown)
        base = max(0.1, score_home + score_away)
        p_home = score_home / base
        home_crowns = int(round(3 * p_home))
        away_crowns = 3 - home_crowns
        if home_crowns == away_crowns:
            if score_home >= score_away:
                home_crowns += 1
                away_crowns -= 1
            else:
                away_crowns += 1
                home_crowns -= 1
        home_crowns = max(0, min(3, home_crowns))
        away_crowns = max(0, min(3, away_crowns))

        # Distribute crowns among starters, track contribution
        details = {home: {}, away: {}}
        highlights = []
        for team_name, starters, crowns in [(home, starters_home, home_crowns), (away, starters_away, away_crowns)]:
            # Fatigue: backup may sub in occasionally
            team = self.teams[team_name]
            pool = starters[:]
            if team.backup and self.rng.random() < 0.25:
                pool = starters[:2] + [self.cards[team.backup]]
            weights = [max(1, c.atk + c.speed + c.hit_speed) for c in pool]
            total_w = sum(weights)
            for _ in range(crowns):
                pick = self.rng.choices(pool, weights=weights, k=1)[0]
                details[team_name][pick.id] = details[team_name].get(pick.id, 0) + 1
                if self.rng.random() < 0.25:
                    highlights.append(f"🔥 {pick.name} slammed a crown!")
            # Update per-team season tallies
            for c in pool:
                c.games_played += 1
                team.season_card_contrib[c.id] += details[team_name].get(c.id, 0) / max(1, crowns)
                if c.id in details[team_name]:
                    c.crowns_total += details[team_name][c.id]
                    c.crowns_high = max(c.crowns_high, details[team_name][c.id])
                    team.season_card_crowns[c.id] += details[team_name][c.id]
                    c.usage_games += 1

        # Update team records
        if home_crowns > away_crowns:
            t_home.wins += 1
            t_away.losses += 1
        else:
            t_away.wins += 1
            t_home.losses += 1
        t_home.crowns_for += home_crowns
        t_home.crowns_against += away_crowns
        t_away.crowns_for += away_crowns
        t_away.crowns_against += home_crowns

        # Rivalry intensity update
        rivalry_proc = None
        if away in t_home.rivals:
            t_home.rivals[away] += RIVALRY_GAIN
            t_away.rivals[home] += RIVALRY_GAIN
            rivalry_proc = f"Rivalry {home} vs {away} intensifies!"
            # Winner gets +2% for next 2 games
            if home_crowns > away_crowns:
                t_home.rivalry_boost_games_left = RIVALRY_WIN_BUFF_GAMES
            else:
                t_away.rivalry_boost_games_left = RIVALRY_WIN_BUFF_GAMES

        # Mock win prob series for Simcast (UI)
        win_series = []
        prob = 0.5 + (home_crowns - away_crowns) * 0.1
        for sec in range(0, 180, 10):
            jitter = self.rng.uniform(-0.02, 0.02)
            prob = max(0.05, min(0.95, prob + jitter))
            win_series.append((sec, prob))

        return GameResult(
            season=self.season, week=week, home=home, away=away,
            home_crowns=home_crowns, away_crowns=away_crowns,
            details=details, highlights=highlights, rivalry_proc=rivalry_proc,
            win_prob_series=win_series
        )

    def _team_effective_power(self, starters: List[Card]) -> float:
        # base from OVR mean
        mean_ovr = statistics.mean(c.ovr for c in starters) / 100.0
        # synergy multiplier
        syn_mult = self._effective_synergy_multiplier(starters)
        return mean_ovr * syn_mult

    # ----- Playoffs -----

    def _seed_playoffs(self) -> List[Tuple[str, str]]:
        # Top 16 by wins; break ties by crowns differential
        teams = list(self.teams.values())
        teams.sort(key=lambda t: (t.wins, t.crowns_for - t.crowns_against), reverse=True)
        top16 = teams[:16]
        # Pair 1v16, 2v15, ...
        pairs = [(top16[i].name, top16[-(i+1)].name) for i in range(8)]
        return pairs

    def _run_playoffs(self, bracket: List[Tuple[str, str]]) -> Tuple[str, Tuple[str, str]]:
        current = bracket[:]
        finalists = (None, None)
        while len(current) > 1:
            next_round = []
            for a, b in current:
                wins_a = wins_b = 0
                while wins_a < 3 and wins_b < 3:
                    res = self._simulate_game(a, b, week=0)
                    if res.home == a and res.home_crowns > res.away_crowns:
                        wins_a += 1
                    else:
                        wins_b += 1
                winner = a if wins_a > wins_b else b
                next_round.append((winner, None))  # placeholder for pairing zip
            # pair winners
            names = [p[0] for p in next_round]
            current = list(zip(names[::2], names[1::2]))
            if len(current) == 1:
                finalists = current[0]
        champion = finalists[0]  # left side winner
        # update rings/dynasty
        self.teams[champion].rings += 1
        self.teams[champion].dynasty_points += 3
        if finalists[1]:
            self.teams[finalists[1]].dynasty_points += 2
        return champion, finalists

    # ----- Awards & HOF -----

    def _compute_awards(self) -> AwardWinners:
        # MVP = highest total crowns weighted by team success
        best = None
        best_score = -1
        for t in self.teams.values():
            team_factor = 1.0 + (t.wins / max(1, t.wins + t.losses))  # 1–2
            for cid in t.roster:
                c = self.cards[cid]
                score = c.crowns_total * team_factor
                if score > best_score:
                    best_score, best = score, c

        # Most Improved: compare this season OVR vs last season OVR
        mip = None
        mip_delta = -999
        for c in self.cards.values():
            if len(c.ovr_history) >= 2:
                prev = c.ovr_history[-2][1]
                delta = c.ovr - prev
                if delta > mip_delta:
                    mip_delta, mip = delta, c

        # All teams: pick top 15 by crowns
        all_sorted = sorted(
            [c for c in self.cards.values() if c.seasons_left > 0],
            key=lambda x: x.crowns_total, reverse=True
        )
        first = [c.id for c in all_sorted[:5]]
        second = [c.id for c in all_sorted[5:10]]
        third = [c.id for c in all_sorted[10:15]]

        # All-Star via fan votes (stub: top by crowns, plus randomness weighted by fan noise)
        all_star = [c.id for c in all_sorted[:10]]

        # MOTY: pick 6 most exciting (highlights count proxy)
        moty = []
        for i, g in enumerate(self.game_log):
            hype = len(g.highlights) + abs(g.home_crowns - g.away_crowns) * 2
            if hype > 2 and len(moty) < 6:
                # pick top performer of the game
                top_card = None
                top_crowns = -1
                for team, dist in g.details.items():
                    for cid, cr in dist.items():
                        if cr > top_crowns:
                            top_crowns, top_card = cr, cid
                if top_card:
                    moty.append((i, top_card))

        # assign awards to cards
        if best:
            best.awards["MVP"] += 1
        if mip:
            mip.awards["MIP"] += 1
        for cid in first + second + third:
            self.cards[cid].awards["ALL_TEAM"] += 1
        for cid in all_star:
            self.cards[cid].awards["ALL_STAR"] += 1
            self.cards[cid].all_star_appearances += 1
        for _, cid in moty:
            self.cards[cid].awards["MOTY"] += 1

        return AwardWinners(
            season=self.season,
            mvp=best.id if best else None,
            most_improved=mip.id if mip else None,
            all_first=first, all_second=second, all_third=third,
            moty=moty, all_stars=all_star
        )

    def _update_leaders_and_history(self, hist: SeasonHistory):
        # leaders by totals this season
        crowns_leaders = sorted(self.cards.values(), key=lambda c: c.crowns_total, reverse=True)[:10]
        contrib_leaders = sorted(self.cards.values(), key=lambda c: c.contribution_sum, reverse=True)[:10]
        usage_leaders = sorted(self.cards.values(), key=lambda c: c.usage_pct(), reverse=True)[:10]
        hist.leaders = {
            "crowns": [c.id for c in crowns_leaders],
            "contribution": [c.id for c in contrib_leaders],
            "usage": [c.id for c in usage_leaders],
        }
        self.history.append(hist)

        # HOF check for cards that just retired (handled in retirements)

    def _handle_retirements_and_rookies(self):
        # decrement seasons_left, retire those at 0 -> HOF check
        retired: List[Card] = []
        for c in self.cards.values():
            if c.seasons_left > 0:
                c.seasons_left -= 1
                # trend record for season end
                c.ovr_history.append((self.season, c.ovr))
            if c.seasons_left == 0 and not c.legend:
                retired.append(c)

        for c in retired:
            score = self._hof_score(c)
            if score >= HOF_GUARANTEE or (HOF_BUBBLE_MIN <= score < HOF_GUARANTEE and self.rng.random() < 0.5):
                c.legend = True
                # could add to a Hall of Legends list; UI can filter by legend flag

        # remove truly expired from draft pool next season (keep for history)
        # (We keep them in self.cards but with seasons_left==0 they won't be drafted.)

        # Add 4 rookies next season (done during draft)

    def _hof_score(self, c: Card) -> float:
        # Career averages
        # Career OVR average
        if c.ovr_history:
            career_ovr = statistics.mean(val for _, val in c.ovr_history)
        else:
            career_ovr = c.ovr
        # crowns per game
        cpg = c.crowns_total / max(1, c.games_played)
        # awards tally
        award_points = (
            c.awards.get("MVP", 0) * AWARD_POINTS["MVP"] +
            c.all_star_appearances * AWARD_POINTS["ALL_STAR"] +
            c.awards.get("MOTY", 0) * AWARD_POINTS["MOTY"] +
            c.awards.get("MIP", 0) * AWARD_POINTS["MIP"] +
            c.awards.get("ALL_TEAM", 0) * AWARD_POINTS["ALL_TEAM"]
        )
        # championships via teams_history count (approximate: count rings on teams played — simplified)
        champ_points = 0
        for tname in set(c.teams_history):
            champ_points += self.teams.get(tname, Team(tname, "", "", "")).rings * CHAMPIONSHIP_POINTS

        # HOF formula
        score = (career_ovr * 0.30) + (cpg * 100 * 0.25) + (cpg * 100 * 0.15) + (award_points * 0.20) + (champ_points * 0.10)
        # Note: cpg used twice per original spec mix (Avg Score & Total Score/Game proxy)
        return score

    def _decay_rivalries(self):
        for t in self.teams.values():
            for r in list(t.rivals.keys()):
                t.rivals[r] = max(0, t.rivals[r] - RIVALRY_DECAY)
                if t.rivals[r] == 0:
                    del t.rivals[r]

    # ---------- Public API for UI ----------

    # Patch Notes & Meta
    def get_patch_notes(self, season: Optional[int] = None) -> Dict[str, List[Dict]]:
        """Return latest or specific season patch notes (cards + synergies) as JSON-like."""
        if season is None:
            season = self.season
        target = None
        for h in self.history[::-1]:
            if h.season == season:
                target = h
                break
        if not target:
            return {"cards": [], "synergies": []}
        return {
            "cards": [asdict(p) for p in target.patch_notes],
            "synergies": [asdict(p) for p in target.synergy_notes]
        }

    # Teams / Standings
    def get_standings(self) -> List[Dict]:
        tlist = list(self.teams.values())
        tlist.sort(key=lambda t: (t.wins, t.crowns_for - t.crowns_against), reverse=True)
        return [{
            "team": t.name, "gm": t.gm_name, "record": t.record_str(),
            "cf": t.crowns_for, "ca": t.crowns_against, "rings": t.rings
        } for t in tlist]

    def get_playoff_bracket(self) -> List[Tuple[str, str]]:
        return self.playoff_bracket[:]

    # Leaders
    def get_league_leaders(self, category: str = "crowns", season: Optional[int] = None) -> List[Dict]:
        if season is None:
            season = self.season
        target = None
        for h in self.history[::-1]:
            if h.season == season:
                target = h
                break
        if not target or category not in target.leaders:
            return []
        return [self._card_view(cid) for cid in target.leaders[category]]

    # Cards
    def get_card_profile(self, card_id: int) -> Dict:
        c = self.cards[card_id]
        return {
            "id": c.id, "name": c.name, "archetype": c.archetype.value, "atk_type": c.atk_type.value,
            "stats": {"atk": c.atk, "defense": c.defense, "speed": c.speed, "hit_speed": c.hit_speed, "stamina": c.stamina},
            "ovr": c.ovr, "lifespan_left": c.seasons_left, "rookie_season": c.rookie_season,
            "badges": {"rookie": c.rookie_season == self.season, "seasonal_special": c.seasonal_special, "legend": c.legend},
            "career": {
                "games": c.games_played, "crowns_total": c.crowns_total, "crowns_high": c.crowns_high,
                "pick_rate_pct": round(c.pick_rate_pct(self.season), 1),
                "usage_pct": round(c.usage_pct(), 1),
                "contribution_total": round(c.contribution_sum, 2),
            },
            "history": {
                "ovr": c.ovr_history,
                "stats": c.stat_history,
                "patch_reactions": c.patch_reactions,
            },
            "awards": dict(c.awards),
            "all_stars": c.all_star_appearances,
            "teams_history": c.teams_history,
        }

    def _card_view(self, cid: int) -> Dict:
        c = self.cards[cid]
        return {"id": c.id, "name": c.name, "ovr": c.ovr, "archetype": c.archetype.value, "atk_type": c.atk_type.value}

    # Synergies
    def get_synergies_table(self) -> List[Dict]:
        out = []
        for s in sorted(self.synergies.values(), key=lambda x: x.code):
            out.append({
                "code": s.code, "name": s.name, "desc": s.description,
                "power_mult": s.power_mult, "history": s.history
            })
        return out

    # Rivalries
    def get_rivalries(self, team_name: str) -> List[Dict]:
        t = self.teams[team_name]
        rows = []
        for rname, intensity in sorted(t.rivals.items(), key=lambda kv: kv[1], reverse=True):
            rows.append({"team": team_name, "rival": rname, "intensity": intensity})
        return rows

    # Draft grades
    def get_last_draft_grades(self) -> List[Dict]:
        for h in self.history[::-1]:
            if h.draft_grades:
                return [{"team": g.team, "grade": g.letter, "score": round(g.score, 1), **g.components} for g in h.draft_grades]
        return []

    # Twitter-esque feeds (strings for UI to render)
    def get_patch_reactions_feed(self) -> List[str]:
        msgs = []
        for c in self.cards.values():
            msgs.extend(c.patch_reactions[-2:])
        self.rng.shuffle(msgs)
        return msgs[:50]

    # Utility
    def reset_rng(self, seed: Optional[int]):
        self.rng = random.Random(seed if seed is not None else DEFAULT_SEED)
