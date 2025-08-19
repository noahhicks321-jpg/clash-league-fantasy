# === app.py ===
# Streamlit UI for the Fantasy Clash Royale League
# - Button-only navigation (no dropdowns)
# - Dark theme + white text
# - Pages: Home, Season, Draft, Standings, Leaders, Simcast, Patch Notes, Synergies, Cards, Playoffs, Rivalries, Twitter
# - Uses 'league.py' League engine

import time
import math
import random
from typing import List, Dict
import streamlit as st

from league import League

# ---------------------------
# Global App Config & Styles
# ---------------------------
st.set_page_config(page_title="Clash Royale Fantasy League", page_icon="🏆", layout="wide")

DARK_CSS = """
<style>
/* Dark background + white text */
html, body, [data-testid="stAppViewContainer"]{
  background: #0b0f16;
  color: #ffffff;
}
h1, h2, h3, h4, h5, h6, p, span, div, code, pre {
  color: #ffffff !important;
}
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
button[kind="primary"]{
  background: #1f2937 !important;
  color: #ffffff !important;
  border: 1px solid #334155 !important;
  border-radius: 12px !important;
}
button[kind="secondary"]{
  background: #111827 !important;
  color: #ffffff !important;
  border: 1px solid #374151 !important;
  border-radius: 12px !important;
}
.sidebar .sidebar-content {
  background: #0b0f16 !important;
}
hr {
  border: none;
  border-top: 1px solid #334155;
}
table {
  color: #ffffff !important;
}
[data-baseweb="tag"] {
  background: #111827 !important;
  color: #fff !important;
}
a { color: #93c5fd !important; }
.block-container { padding-top: 1rem !important; }
.badge {
  display:inline-block; padding:2px 8px; border-radius:999px; border:1px solid #475569; font-size:12px; margin-left:8px;
  background:#111827; color:#fff;
}
.card-grid { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; }
.card {
  border:1px solid #334155; border-radius:16px; padding:12px; background:#111827;
}
.metric {
  display:flex; justify-content:space-between; align-items:center; border:1px solid #334155; border-radius:12px; padding:12px; background:#0f172a;
}
.win { color:#22c55e !important; }
.lose { color:#ef4444 !important; }
.subtle { color:#94a3b8 !important; font-size:12px; }
.kbd { border:1px solid #334155; padding:0 6px; border-radius:6px; margin-left:6px; font-size:12px; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# ---------------------------
# Session State
# ---------------------------
if "league" not in st.session_state:
    st.session_state.league = League(seed=1337, human_team_name=None)
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "season_histories" not in st.session_state:
    st.session_state.season_histories: List[Dict] = []
if "sim_speed" not in st.session_state:
    st.session_state.sim_speed = 1.0  # 1x, 2x, 4x, 8x
if "simcast_idx" not in st.session_state:
    st.session_state.simcast_idx = None  # which game from game_log
if "selected_card" not in st.session_state:
    st.session_state.selected_card = None
if "selected_team" not in st.session_state:
    st.session_state.selected_team = None

L: League = st.session_state.league

# ---------------------------
# Navigation (buttons only)
# ---------------------------
def nav_button(label: str, target: str, col):
    if col.button(label, use_container_width=True):
        st.session_state.page = target

with st.container():
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
    nav_button("🏠 Home", "Home", c1)
    nav_button("📆 Season", "Season", c2)
    nav_button("🎯 Draft", "Draft", c3)
    nav_button("📈 Standings", "Standings", c4)
    nav_button("🏅 Leaders", "Leaders", c5)
    nav_button("🎛️ Simcast", "Simcast", c6)
    nav_button("🛠 Patch Notes", "PatchNotes", c7)
    nav_button("🧩 Synergies", "Synergies", c8)

c9, c10, c11, c12 = st.columns(4)
nav_button("🃏 Cards", "Cards", c9)
nav_button("🏆 Playoffs", "Playoffs", c10)
nav_button("⚔️ Rivalries", "Rivalries", c11)
nav_button("🐦 Twitter", "Twitter", c12)

st.markdown("<hr/>", unsafe_allow_html=True)

# ---------------------------
# Helpers
# ---------------------------
def tag(text): 
    st.markdown(f"<span class='badge'>{text}</span>", unsafe_allow_html=True)

def team_metric(trow: Dict):
    with st.container():
        st.markdown(
            f"<div class='metric'><div><b>{trow['team']}</b><div class='subtle'>GM: {trow['gm']}</div></div>"
            f"<div>W-L: <b>{trow['record']}</b> &nbsp; CF: {trow['cf']} / CA: {trow['ca']} &nbsp; Rings: {trow['rings']}</div></div>",
            unsafe_allow_html=True
        )

def grid_buttons(labels: List[str], key_prefix: str, cols=5):
    rows = []
    for i in range(0, len(labels), cols):
        rows.append(labels[i:i+cols])
    for r, row in enumerate(rows):
        cols_list = st.columns(len(row))
        for j, lab in enumerate(row):
            if cols_list[j].button(lab, key=f"{key_prefix}_{r}_{j}", use_container_width=True):
                return lab
    return None

def card_button(cid: int):
    c = L.cards[cid]
    badges = []
    if c.rookie_season == L.season:
        badges.append("Rookie")
    if c.seasonal_special:
        badges.append("Seasonal")
    if c.legend:
        badges.append("Legend")
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write(f"**{c.name}**")
        st.write(f"{c.archetype.value} • {c.atk_type.value}")
        st.write(f"OVR: **{c.ovr}**  | Lifespan left: {c.seasons_left}")
        st.write(f"Stats — ATK {c.atk} | DEF {c.defense} | SPD {c.speed} | HIT {c.hit_speed} | STA {c.stamina}")
        if badges:
            st.write("Badges: " + ", ".join(badges))
        if st.button("View Profile", key=f"view_card_{cid}", use_container_width=True):
            st.session_state.selected_card = cid
            st.session_state.page = "Cards"
        st.markdown("</div>", unsafe_allow_html=True)

def page_header(title: str, subtitle: str = ""):
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f"<div class='subtle'>{subtitle}</div>", unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)

# ---------------------------
# Pages
# ---------------------------
def page_home():
    page_header("Clash Royale Fantasy League", "Dark theme • Button navigation • 30 teams • 160–170 card pool")
    st.write("**Quick Actions**")
    a, b, c, d = st.columns(4)
    if a.button("▶️ Sim Full Season", use_container_width=True):
        hist = L.run_full_season()
        st.session_state.season_histories.append({"season": hist.season})
        st.success(f"Season {hist.season} complete! Champion: {hist.champion}")
    if b.button("🧭 Go to Standings", use_container_width=True):
        st.session_state.page = "Standings"
    if c.button("📜 View Patch Notes", use_container_width=True):
        st.session_state.page = "PatchNotes"
    if d.button("🧩 Explore Synergies", use_container_width=True):
        st.session_state.page = "Synergies"

    st.markdown("#### Recent Headlines")
    feed = L.get_patch_reactions_feed()
    for msg in feed[:10]:
        st.write(f"- {msg}")

    st.markdown("#### Top Cards Right Now")
    leaders = L.get_league_leaders("crowns") or []
    cols = st.columns(5)
    for i, entry in enumerate(leaders[:5]):
        c = L.cards[entry["id"]]
        with cols[i]:
            st.metric(label=c.name, value=f"OVR {c.ovr}", delta=f"{c.crowns_total} crowns")

def page_season():
    page_header("Season Control", "Run season flow: Patches → Draft → Games → Playoffs → Awards")
    col1, col2, col3 = st.columns(3)
    if col1.button("▶️ Run Full Season", use_container_width=True):
        hist = L.run_full_season()
        st.session_state.season_histories.append({"season": hist.season})
        st.success(f"Season {hist.season} complete! Champion: {hist.champion}")
    if col2.button("🔁 Reset RNG (New Seed)", use_container_width=True):
        new_seed = random.randint(1, 999999)
        L.reset_rng(new_seed)
        st.info(f"RNG reseeded: {new_seed}")
    if col3.button("ℹ️ Season Summary (Latest)", use_container_width=True):
        if L.history:
            h = L.history[-1]
            st.write(f"Season {h.season} — Champion: **{h.champion}** | Finalists: {h.finalists}")
            st.write("Awards: MVP:", h.awards.mvp if h.awards else None)
        else:
            st.warning("No seasons completed yet.")

    st.markdown("#### Awards & Records (Latest Season)")
    if not L.history:
        st.info("Run at least one season to see awards and records.")
    else:
        h = L.history[-1]
        if h.awards:
            aw = h.awards
            cols = st.columns(4)
            cols[0].write(f"**MVP**: {L.cards[aw.mvp].name if aw.mvp else '—'}")
            cols[1].write(f"**MIP**: {L.cards[aw.most_improved].name if aw.most_improved else '—'}")
            cols[2].write(f"**All-Star (10)**: " + ", ".join(L.cards[cid].name for cid in aw.all_stars[:5]) + "…")
            cols[3].write(f"**MOTY (6)**: {len(aw.moty)} selections")
        else:
            st.info("No awards computed yet.")

def page_draft():
    page_header("Draft Room", "Patch notes drop → Draft order → Picks → Grades")
    c1, c2, c3 = st.columns(3)
    if c1.button("📜 Show Patch Notes (Latest)", use_container_width=True):
        _render_patch_notes(latest=True)
    if c2.button("🎲 Draft Now (Only)", use_container_width=True):
        # Run only the draft phase: we’ll emulate by calling run_full_season but stopping early is not exposed.
        # For UX, we run the full season and show draft grades below (fast).
        hist = L.run_full_season()
        st.session_state.season_histories.append({"season": hist.season})
        st.success(f"Season {hist.season} drafted & completed (fast run). See grades below.")
    if c3.button("📝 Show Last Draft Grades", use_container_width=True):
        grades = L.get_last_draft_grades()
        if not grades:
            st.info("No draft grades yet. Run a season first.")
        else:
            _render_draft_grades(grades)

    st.markdown("#### Last Draft Grades")
    grades = L.get_last_draft_grades()
    if grades:
        _render_draft_grades(grades)
    else:
        st.info("No grades available yet.")

def _render_draft_grades(grades):
    cols = st.columns(3)
    for i, g in enumerate(grades):
        col = cols[i % 3]
        with col:
            st.markdown(
                f"<div class='card'><b>{g['team']}</b><br/>Grade: <b>{g['grade']}</b><br/>"
                f"Score: {round(g['score'],1)}<br/><span class='subtle'>OVR {round(g['ovr'],1)} • Synergy {round(g['synergy'],1)} • Value {round(g['value'],1)}</span></div>",
                unsafe_allow_html=True
            )

def page_standings():
    page_header("League Standings", "W-L, crowns for/against, rings")
    data = L.get_standings()
    for row in data:
        team_metric(row)

def page_leaders():
    page_header("League Leaders", "Crowns • Usage • Contribution")
    b1, b2, b3 = st.columns(3)
    if b1.button("Crowns", use_container_width=True): _render_leaders("crowns")
    if b2.button("Usage %", use_container_width=True): _render_leaders("usage")
    if b3.button("Contribution %", use_container_width=True): _render_leaders("contribution")

    st.markdown("#### Current: Crowns")
    _render_leaders("crowns")

def _render_leaders(cat: str):
    leaders = L.get_league_leaders(cat) or []
    cols = st.columns(5)
    for i, e in enumerate(leaders[:10]):
        c = L.cards[e["id"]]
        col = cols[i % 5]
        with col:
            st.markdown(
                f"<div class='card'><b>{c.name}</b><br/>{c.archetype.value} • {c.atk_type.value}<br/>"
                f"OVR {c.ovr}<br/><span class='subtle'>Career crowns: {c.crowns_total} • Usage: {c.usage_pct():.1f}%</span></div>",
                unsafe_allow_html=True
            )

def page_simcast():
    page_header("Simcast Live", "3-minute ticker • speed x1/x2/x4/x8 • highlights • win prob")
    # Choose a game from recent log via buttons (paginated)
    if not L.game_log:
        st.info("No games in the log yet. Run a season to generate games.")
        return

    st.write("**Pick a recent game to replay:**")
    recent = L.game_log[-20:]  # last 20
    labels = []
    for i, g in enumerate(reversed(recent)):
        labels.append(f"{g.home} {g.home_crowns}-{g.away_crowns} {g.away} (S{g.season} W{g.week})")
    chosen = grid_buttons(labels, "simcast_games", cols=2)
    if chosen is not None:
        st.session_state.simcast_idx = len(L.game_log) - 1 - labels.index(chosen)

    sp1, sp2, sp3, sp4 = st.columns(4)
    if sp1.button("1×", use_container_width=True): st.session_state.sim_speed = 1.0
    if sp2.button("2×", use_container_width=True): st.session_state.sim_speed = 2.0
    if sp3.button("4×", use_container_width=True): st.session_state.sim_speed = 4.0
    if sp4.button("8×", use_container_width=True): st.session_state.sim_speed = 8.0
    st.caption(f"Speed: {int(st.session_state.sim_speed)}×")

    idx = st.session_state.simcast_idx if st.session_state.simcast_idx is not None else len(L.game_log) - 1
    g = L.game_log[idx]

    st.write(f"**{g.home}** vs **{g.away}** — Season {g.season}, Week {g.week}")
    st.write(f"Final: **{g.home_crowns} - {g.away_crowns}**")

    # Simulate a 3-minute ticker (180s) using stored win_prob_series (every 10s)
    container = st.empty()
    high = st.empty()
    for tsec, p_home in g.win_prob_series:
        with container.container():
            pct = int(round(p_home * 100))
            bar_home = "█" * (pct // 5)
            bar_away = "█" * ((100 - pct) // 5)
            st.write(f"Time: {tsec:>3}s — Win Prob: {g.home} {pct}%  |  {g.away} {100-pct}%")
            st.write(f"{g.home:<20} {bar_home}")
            st.write(f"{g.away:<20} {bar_away}")
        if g.highlights and random.random() < 0.3:
            high.write(f"**Highlight:** {g.highlights[random.randint(0, len(g.highlights)-1)]}")
        # sleep scaled by speed
        time.sleep(max(0.02, 0.25 / st.session_state.sim_speed))

    if g.rivalry_proc:
        st.success(g.rivalry_proc)

def page_patch_notes():
    page_header("Patch Notes", "Buffs low pick/usage • Nerf overused • 2–5 synergy shifts")
    _render_patch_notes(latest=True)

def _render_patch_notes(latest: bool = True):
    notes = L.get_patch_notes() if latest else L.get_patch_notes(season=L.season)
    if not notes["cards"] and not notes["synergies"]:
        st.info("No patch notes recorded yet. Run a season.")
        return
    st.markdown("#### Card Changes")
    if notes["cards"]:
        for p in notes["cards"][:100]:
            name = L.cards[p["card_id"]].name if p["card_id"] else "—"
            delta_str = ", ".join([f"{k} {('+' if v>=0 else '')}{v}" for k, v in p["stat_deltas"].items()])
            st.markdown(
                f"<div class='card'><b>{name}</b><br/>{p['reason']}<br/>{delta_str}<br/>"
                f"<span class='subtle'>{p['msg']}</span></div>",
                unsafe_allow_html=True
            )
    else:
        st.write("No card changes.")

    st.markdown("#### Synergy Shifts")
    if notes["synergies"]:
        for s in notes["synergies"][:100]:
            st.markdown(f"<div class='card'>{s['msg']}</div>", unsafe_allow_html=True)
    else:
        st.write("No synergy changes.")

def page_synergies():
    page_header("Synergy Library", "90+ rules • live power multipliers • per-season history")
    syn = L.get_synergies_table()
    cols = st.columns(3)
    for i, s in enumerate(syn[: ninety(syn)]):
        col = cols[i % 3]
        with col:
            st.markdown(
                f"<div class='card'><b>{s['code']}</b> — {s['name']}<br/>"
                f"{s['desc']}<br/>Power × {s['power_mult']:.2f}</div>",
                unsafe_allow_html=True
            )

def ninety(lst):  # helper to cap to 90 for grid demo
    return min(90, len(lst))

def page_cards():
    page_header("Card Profiles", "Click a card to view full profile and trends")

    # Quick filters by buttons (no dropdowns) — archetype
    st.write("**Filter by Archetype** (button toggles):")
    a1, a2, a3, a4, a5, a6 = st.columns(6)
    filters = st.session_state.get("card_filters", set())
    def toggle_filter(tag, col):
        if col.button(tag, use_container_width=True):
            if tag in filters: filters.remove(tag)
            else: filters.add(tag)
            st.session_state.card_filters = filters
    toggle_filter("Tank", a1)
    toggle_filter("Healer", a2)
    toggle_filter("Burst", a3)
    toggle_filter("Control", a4)
    toggle_filter("Utility", a5)
    toggle_filter("Balanced", a6)
    tags = list(filters)

    # Render cards grid
    shown = 0
    cols = st.columns(4)
    for cid, c in list(L.cards.items())[:]:
        if c.seasons_left <= 0:  # still show legends? show but deemphasize
            pass
        if tags and c.archetype.value not in tags:
            continue
        with cols[shown % 4]:
            card_button(cid)
        shown += 1
        if shown >= 20:
            break

    # Selected card profile
    if st.session_state.selected_card:
        c = L.cards[st.session_state.selected_card]
        st.markdown("#### Profile")
        st.markdown(
            f"<div class='card'><b>{c.name}</b> — {c.archetype.value} • {c.atk_type.value}<br/>"
            f"OVR {c.ovr} | Lifespan left {c.seasons_left} | Rookie S{c.rookie_season}<br/>"
            f"Stats: ATK {c.atk} • DEF {c.defense} • SPD {c.speed} • HIT {c.hit_speed} • STA {c.stamina}<br/>"
            f"Career: Games {c.games_played} • Crowns {c.crowns_total} (High {c.crowns_high}) • Usage {c.usage_pct():.1f}% • Pick Rate {c.pick_rate_pct(L.season):.1f}%<br/>"
            f"Awards: {dict(c.awards)} • All-Star {c.all_star_appearances}<br/>"
            f"Teams: {', '.join(c.teams_history) if c.teams_history else '—'}</div>",
            unsafe_allow_html=True
        )
        # Trend text (no charts to keep it lightweight)
        if c.ovr_history:
            last5 = c.ovr_history[-5:]
            st.write("**OVR Trend (last 5 points):** " + " → ".join(f"S{s}={v}" for s, v in last5))
        if c.patch_reactions:
            st.write("**Patch Reactions:**")
            for r in c.patch_reactions[-3:]:
                st.write("- " + r)

def page_playoffs():
    page_header("Playoff Bracket", "Live bracket after regular season")
    bracket = L.get_playoff_bracket()
    if not bracket:
        st.info("No bracket yet. Run a season.")
        return
    st.markdown("#### Round of 16")
    cols = st.columns(2)
    for i, (a, b) in enumerate(bracket[:8]):
        col = cols[i % 2]
        with col:
            st.markdown(f"<div class='card'><b>{a}</b> vs <b>{b}</b></div>", unsafe_allow_html=True)

def page_rivalries():
    page_header("Rivalries", "Intensity meter • +2% stats for 2 games after rivalry win")
    teams = list(L.teams.keys())
    # Use buttons to pick a team
    st.write("**Pick a Team**")
    chosen = grid_buttons(teams[:20], "rival_team", cols=3)
    if chosen:
        st.session_state.selected_team = chosen
    name = st.session_state.selected_team or teams[0]
    st.write(f"**Team:** {name}")
    rows = L.get_rivalries(name)
    if not rows:
        st.info("No active rivalries yet.")
        return
    cols = st.columns(2)
    for i, r in enumerate(rows[:10]):
        col = cols[i % 2]
        with col:
            st.markdown(
                f"<div class='card'><b>{r['rival']}</b><br/>Intensity: {r['intensity']}</div>",
                unsafe_allow_html=True
            )

def page_twitter():
    page_header("League Twitter", "GM personalities • fan reactions • patch/draft debates")
    feed = L.get_patch_reactions_feed()
    if not feed:
        st.info("Nothing yet. Run a season or show patch notes.")
        return
    for msg in feed[:50]:
        st.write(f"- {msg}")

# ---------------------------
# Page Router
# ---------------------------
PAGES = {
    "Home": page_home,
    "Season": page_season,
    "Draft": page_draft,
    "Standings": page_standings,
    "Leaders": page_leaders,
    "Simcast": page_simcast,
    "PatchNotes": page_patch_notes,
    "Synergies": page_synergies,
    "Cards": page_cards,
    "Playoffs": page_playoffs,
    "Rivalries": page_rivalries,
    "Twitter": page_twitter,
}

PAGES[st.session_state.page]()
