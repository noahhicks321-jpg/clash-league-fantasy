import streamlit as st
import pandas as pd
from streamlit.components.v1 import html
from league import get_league

# =====================================================
# Clash Royale Fantasy League — UI (No Dropdowns Edition)
# - Tabbed navigation only
# - Clickable cards/logos instead of selects
# - Calendar & Playoff Bracket viewers
# =====================================================

st.set_page_config(page_title="Clash Royale Fantasy League", layout="wide")

# -----------------
# THEME / CSS
# -----------------
CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;800&display=swap');
  html, body, [class*="css"] { background: radial-gradient(1200px 600px at 20% 10%, #0d1330 0%, #0a0f1d 40%, #080c17 100%) !important; }
  h1,h2,h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: .5px; color: #f5f7ff; }
  .card { background: linear-gradient(145deg, rgba(20,24,45,.9), rgba(15,18,35,.9)); border: 1px solid rgba(255,255,255,.06); border-radius: 18px; padding: 14px; box-shadow: 0 12px 28px rgba(0,0,0,.35); }
  .hover:hover { transform: translateY(-2px); transition: .2s ease; box-shadow: 0 18px 30px rgba(0,0,0,.45); }
  .pill { padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; }
  .pill-rank { background: linear-gradient(90deg, #3c1053, #ad5389); color: #fff; }
  .tweet { background: rgba(255,255,255,.05); padding: 10px 12px; border-radius: 14px; border: 1px solid rgba(255,255,255,.06); margin-bottom: 8px; }
  .grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
  .btn { border: 1px solid rgba(255,255,255,.15); background: rgba(255,255,255,.06); padding: 8px 12px; border-radius: 12px; color:#eaf1ff; text-align:center; cursor:pointer; }
  .btn:hover { background: rgba(255,255,255,.12); }
  .rankbar { height: 10px; border-radius: 999px; background: rgba(255,255,255,.07); overflow: hidden; }
  .rankbar > div { height: 100%; background: linear-gradient(90deg,#00f5d4,#60efff); }
  .table-note { color:#cfe3ff; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -----------------
# STATE / DATA
# -----------------
if "league" not in st.session_state:
    st.session_state.league = get_league()
L = st.session_state.league

# Ensure calendar has teams (re-generate after teams exist)
L.calendar = L.generate_calendar()

if "selected_team" not in st.session_state:
    st.session_state.selected_team = None
if "selected_week" not in st.session_state:
    st.session_state.selected_week = 1

# -----------------
# HELPERS
# -----------------

def team_logo_block(team_obj):
    rec = f"{team_obj.wins}-{team_obj.losses}"
    html(f"""
      <div class='card hover'>
        <div style='font-size:38px'>{team_obj.logo}</div>
        <div style='font-weight:800; color:#fff; font-size:18px'>{team_obj.name}</div>
        <div style='color:#b9c8ff; font-size:13px'>GM: {team_obj.gm.name} • Rank: <span class='pill pill-rank'>{team_obj.gm.rank}</span></div>
        <div style='margin-top:6px; color:#e8ecff;'>Record: {rec}</div>
      </div>
    """, height=128)


def stat_chip(label, value):
    html(f"<div class='btn' style='display:inline-block;margin-right:6px'>{label}: <b>{value}</b></div>")


def bracket_view(bracket_dict):
    if not bracket_dict:
        st.info("Generate the bracket to view Round 1 matchups.")
        return
    # Render as 4 columns (R1 only for this minimal viewer)
    keys = sorted(bracket_dict.keys())
    cols = st.columns(4)
    for i, k in enumerate(keys):
        home, away = bracket_dict[k]
        with cols[i % 4]:
            st.markdown(f"**{k}**")
            st.markdown(f"{home} vs {away}")


def render_calendar(cal):
    st.markdown("#### Regular Season Calendar (20 weeks)")
    # Week pager buttons (no dropdown)
    c1, c2, c3, c4, c5 = st.columns(5)
    for offset, c in enumerate([c1, c2, c3, c4, c5]):
        base = 1 + offset*4
        with c:
            st.markdown("Week Jump")
            row = st.columns(4)
            for j in range(4):
                wk = base + j
                if wk <= 20 and st.button(f"W{wk}"):
                    st.session_state.selected_week = wk
    st.markdown("---")

    wk = st.session_state.selected_week
    week_obj = next((x for x in cal if x["week"] == wk), None)
    if not week_obj:
        st.warning("Week not found.")
        return

    st.subheader(f"Week {wk} Matchups")
    grid = st.container()
    with grid:
        cols = st.columns(3)
        for i, (home, away) in enumerate(week_obj["matchups"]):
            with cols[i % 3]:
                st.markdown(f"<div class='card hover'>🏟️ <b>{home}</b> vs <b>{away}</b></div>", unsafe_allow_html=True)

# -----------------
# TOP NAV TABS (NO DROPDOWNS)
# -----------------
main_tabs = st.tabs([
    "Home", "Teams", "Cards", "GMs", "Calendar", "Playoffs", "Awards & HOF", "Rivalries", "History", "News", "Trades", "Patches", "Rankings"
])

# HOME
with main_tabs[0]:
    st.title("🏠 League Home")
    c1, c2 = st.columns([2,1])
    with c1:
        st.subheader("Standings")
        standings_df = L.get_standings()
        try:
            st.dataframe(standings_df, use_container_width=True)
        except Exception:
            st.table(standings_df)
    with c2:
        st.subheader("Headlines")
        for n in L.get_news():
            st.markdown(f"- {n}")
        st.markdown("---")
        if st.button("Generate Playoff Bracket"):
            L.generate_playoff_bracket()
        st.caption("Use the Playoffs tab to view the bracket.")

# TEAMS (grid of clickable cards)
with main_tabs[1]:
    st.title("🧑‍🤝‍🧑 Teams")
    st.caption("Click any team card to focus below. No dropdowns — pure click nav.")

    # Grid of team cards as buttons
    team_objs = L.teams
    grid_container = st.container()

    cols = st.columns(4)
    for idx, T in enumerate(team_objs):
        with cols[idx % 4]:
            if st.button(f"{T.logo} {T.name}"):
                st.session_state.selected_team = T.name
            team_logo_block(T)

    st.markdown("---")
    # Focused team details
    sel_name = st.session_state.selected_team or (team_objs[0].name if team_objs else None)
    if sel_name:
        T = L.get_team(sel_name)
        st.header(f"{T.logo} {T.name}")
        cA, cB = st.columns([2,1])
        with cA:
            st.markdown("### Overview")
            stat_chip("GM", T.gm.name)
            stat_chip("Rank", T.gm.rank)
            stat_chip("Record", f"{T.wins}-{T.losses}")
            st.markdown("#### Lineup (3 + 1 backup)")
            if T.lineup:
                df = pd.DataFrame([c.to_dict() for c in T.lineup])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No lineup set yet.")
        with cB:
            st.markdown("### Trophy Case")
            trophies = T.gm.trophies or ["—"]
            for tr in trophies:
                st.markdown(f"<div class='btn'>🏆 {tr}</div>", unsafe_allow_html=True)

# CARDS (search + chips; no dropdowns)
with main_tabs[2]:
    st.title("🃏 Card Database")
    cards_df = L.get_all_cards()

    # Search bar + filter chips
    q = st.text_input("Search card name / type (press Enter)")
    colc1, colc2, colc3 = st.columns(3)
    with colc1:
        melee = st.checkbox("Melee")
    with colc2:
        ranged = st.checkbox("Ranged")
    with colc3:
        rookies_only = st.checkbox("Rookies only")

    df = cards_df.copy()
    if q:
        ql = q.lower()
        df = df[df["Name"].str.lower().str.contains(ql) | df["ATK Type"].str.lower().str.contains(ql)]
    types = []
    if melee: types.append("Melee")
    if ranged: types.append("Ranged")
    if types:
        df = df[df["ATK Type"].isin(types)]
    if rookies_only:
        df = df[df["Rookie"] == True]

    st.dataframe(df.sort_values("Overall", ascending=False), use_container_width=True)
    st.caption("Trend arrows reflect buffs/nerfs impact over time.")

# GMs (leaderboard + tweets)
with main_tabs[3]:
    st.title("🧑‍💼 GM Tracker — Ranks & Tweets")
    gm_df = L.get_gm_leaderboard()
    st.dataframe(gm_df, use_container_width=True)
    st.markdown("### Recent GM Trash Talk (modern slang)")
    for line in L.get_news():
        st.markdown(f"<div class='tweet'>{line}</div>", unsafe_allow_html=True)

# CALENDAR (week grid buttons)
with main_tabs[4]:
    st.title("📅 Season Calendar")
    render_calendar(L.calendar)

# PLAYOFFS (bracket viewer)
with main_tabs[5]:
    st.title("🏆 Playoffs — Bracket")
    st.markdown("Click 'Generate Playoff Bracket' from Home if empty.")
    bracket_view(L.playoff_bracket)

# AWARDS & HOF
with main_tabs[6]:
    st.title("🏅 Awards & Hall of Fame")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Season Awards")
        try:
            st.table(L.get_awards())
        except Exception:
            st.info("No awards yet.")
    with c2:
        st.subheader("Hall of Fame")
        try:
            st.table(L.get_hof())
        except Exception:
            st.info("No inductees yet.")

# RIVALRIES
with main_tabs[7]:
    st.title("⚔️ Rivalries")
    try:
        st.dataframe(L.get_rivalries(), use_container_width=True)
    except Exception:
        st.info("Rivalries will populate as the league sim runs.")

# HISTORY
with main_tabs[8]:
    st.title("📜 League History & Eras")
    hist = L.get_history()
    if hist:
        st.dataframe(pd.DataFrame(hist), use_container_width=True)
    else:
        st.info("History will fill after seasons are completed.")

# NEWS
with main_tabs[9]:
    st.title("📰 News & Fan Reactions")
    left, right = st.columns(2)
    with left:
        st.subheader("GM Tweets")
        for line in L.get_news():
            st.markdown(f"<div class='tweet'>{line}</div>", unsafe_allow_html=True)
    with right:
        st.subheader("Fan Memes (placeholder)")
        for i in range(6):
            st.markdown(f"<div class='tweet'>Fan{i+1}: 'buffs dropped and my squad still HIM 😤'</div>", unsafe_allow_html=True)

# TRADES
with main_tabs[10]:
    st.title("🔄 Trades — Finder & Deadline Week")
    st.subheader("Rumors")
    st.table(L.get_trade_rumors())
    st.caption("Use backend functions to generate/execute trades in a future sim update.")

# PATCHES
with main_tabs[11]:
    st.title("🛠️ Patches — Buffs/Nerfs & Meta Shifts")
    try:
        st.table(L.get_patches())
    except Exception:
        st.info("No patches applied yet.")

# RANKINGS
with main_tabs[12]:
    st.title("🏆 GM Rankings & Progression")
    st.dataframe(L.get_gm_leaderboard(), use_container_width=True)
    st.caption("Points model: Win +50 / Loss −50. Playoff values & award bonuses can be added later.")

st.markdown("---")
st.caption("No dropdowns used. Navigation is tabs + clickable cards. To update on GitHub: open file, select all → paste new code → commit.")
