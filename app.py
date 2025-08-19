import time
import random
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html
from league import get_league, RANK_TIERS, POINT_VALUES

# =====================================================
# 🎮 APP.UI — Streamlit front-end for Clash Royale Fantasy League
# Expanded UI: dark sports look, neon accents, SimCast, All-Star, Trades, Patches, Rankings
# =====================================================

st.set_page_config(page_title="Clash Royale Fantasy League", layout="wide")

# -----------------
# THEME / CSS (dark + neon)
# -----------------
CUSTOM_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;800&display=swap');
  html, body, [class*="css"]  { background: radial-gradient(1200px 600px at 20% 10%, #0d1330 0%, #0a0f1d 40%, #080c17 100%) !important; }
  h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; color: #f5f7ff; }
  .league-card { background: linear-gradient(145deg, rgba(20,24,45,.9), rgba(15,18,35,.9)); border: 1px solid rgba(255,255,255,.06); border-radius: 18px; padding: 16px; box-shadow: 0 12px 28px rgba(0,0,0,.35); }
  .metric { background: rgba(255,255,255,.06); border-radius: 14px; padding: 10px 12px; }
  .pill { padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; }
  .pill-rank { background: linear-gradient(90deg, #3c1053, #ad5389); color: #fff; }
  .pill-hot { background: #0fa; color: #012; }
  .pill-cold { background: #ff5b5b; color: #210; }
  .hover-card:hover { transform: translateY(-2px); transition: .2s ease; box-shadow: 0 18px 30px rgba(0,0,0,.45); }
  .rankbar { height: 10px; border-radius: 999px; background: rgba(255,255,255,.07); overflow: hidden; }
  .rankbar > div { height: 100%; background: linear-gradient(90deg,#00f5d4,#60efff); }
  .progress { height: 12px; border-radius: 10px; background: rgba(255,255,255,.08); }
  .progress > div { height: 100%; background: linear-gradient(90deg,#ffe55e,#ff7b00); border-radius: 10px; }
  .tweet { background: rgba(255,255,255,.05); padding: 10px 12px; border-radius: 14px; border: 1px solid rgba(255,255,255,.06); margin-bottom: 8px; }
  .badge { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.1); padding: 4px 8px; border-radius: 8px; font-size: 12px; }
  .svg-wrap { border-radius: 18px; overflow: hidden; border: 1px solid rgba(255,255,255,.08); }
  .stDataFrame, .stTable { color: #e8ecff; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------
# STATE
# -----------------
L = get_league()

# Sidebar navigation + Sim controls
st.sidebar.title("⚔️ League Control Center")
page = st.sidebar.selectbox(
    "Jump to", [
        "Home", "SimCast", "Teams", "Cards", "Stats & Records", "GMs", "Rivalries",
        "Awards & HOF", "League History", "News", "Trades", "Patches", "Rankings"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Sim Controls")
col_sb1, col_sb2 = st.sidebar.columns(2)
if col_sb1.button("Sim Week"):
    L.sim_week(L.week)
if col_sb2.button("Seed Playoffs"):
    L.seed_playoffs()
col_sb3, col_sb4 = st.sidebar.columns(2)
if col_sb3.button("Run Playoffs"):
    L.run_playoffs()
if col_sb4.button("All-Star Weekend"):
    L.run_all_star()

st.sidebar.markdown("---")
if st.sidebar.button("Advance Offseason"):
    L.finalize_awards()
    L.offseason_reset()

# -----------------
# HELPERS
# -----------------

def rank_threshold_table():
    rows = []
    for name, threshold, buff in RANK_TIERS:
        buff_txt = "—"
        if buff:
            pct, games = buff
            buff_txt = f"+{int(pct*100)}% for {games} games"
        rows.append({"Rank": name, "Min XP": threshold, "Buff": buff_txt})
    return pd.DataFrame(rows)


def svg_logo(svg: str, width: int = 120, height: int = 120):
    html(f"<div class='svg-wrap' style='width:{width}px;height:{height}px'>{svg}</div>", height=height+4)


def meter(label: str, value: float, max_val: float = 1.0):
    pct = max(0.0, min(1.0, float(value)/max_val))
    html(f"""
    <div style='margin:6px 0'>
      <div style='display:flex;justify-content:space-between'>
        <div style='color:#cfe3ff'>{label}</div>
        <div style='color:#fff;font-weight:700'>{int(pct*100)}%</div>
      </div>
      <div class='progress'><div style='width:{pct*100:.1f}%'></div></div>
    </div>
    """, height=36)


def hot_cold_pill(wins: int, losses: int):
    if wins + losses < 5:
        return "<span class='pill pill-hot'>NEW</span>"
    streak_val = wins - losses
    if streak_val >= 3:
        return "<span class='pill pill-hot'>HOT</span>"
    if streak_val <= -3:
        return "<span class='pill pill-cold'>COLD</span>"
    return "<span class='pill' style='background:#889; color:#fff'>EVEN</span>"

# -----------------
# PAGES
# -----------------
if page == "Home":
    st.title("🏠 League Home")
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Live Standings")
        rows = L.get_standings()
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with c2:
        st.subheader("Headlines")
        for n in L.get_news():
            st.markdown(f"- {n}")
        st.subheader("Quick Patch")
        if st.button("Apply Meta Patch"):
            L.apply_patch()
            st.success("Patch applied. Low-pick cards buffed, villains clipped.")

elif page == "SimCast":
    st.title("🟣 SimCast — Live Game Viewer")
    left, right = st.columns(2)
    team_names = [t.name for t in L.teams.values()]
    with left:
        home_pick = st.selectbox("Home Team", team_names)
    with right:
        away_pick = st.selectbox("Away Team", team_names, index=min(1, len(team_names)-1))

    if home_pick == away_pick:
        st.warning("Pick two different teams to run SimCast.")
    else:
        th = L.get_team(home_pick)
        ta = L.get_team(away_pick)
        st.markdown("---")
        c1, c2, c3 = st.columns([1,1,2])
        with c1:
            st.markdown("#### Home")
            svg_logo(th.logo_svg, 110, 110)
            st.markdown(f"**{th.name}**")
            meter("Chemistry", th.chemistry, 0.25)
            meter("Fatigue", th.fatigue, 0.30)
        with c2:
            st.markdown("#### Away")
            svg_logo(ta.logo_svg, 110, 110)
            st.markdown(f"**{ta.name}**")
            meter("Chemistry", ta.chemistry, 0.25)
            meter("Fatigue", ta.fatigue, 0.30)
        with c3:
            st.markdown("#### Controls")
            speed = st.select_slider("Speed", options=["1x","2x","4x","8x"], value="2x")
            run_btn = st.button("Run SimCast")

        if run_btn:
            # Simple animation loop faking a 3:00 clock
            pace = {"1x":0.25, "2x":0.15, "4x":0.08, "8x":0.04}[speed]
            timer = st.empty()
            pb = st.progress(0)
            for tick in range(0, 180):
                mm = (179 - tick) // 60
                ss = (179 - tick) % 60
                timer.markdown(f"### ⏱️ {mm:02d}:{ss:02d}")
                pb.progress(int((tick/180)*100))
                time.sleep(pace)
            # Finalize game once animation is done
            res = L.sim_game(next(k for k,v in L.teams.items() if v.name==home_pick),
                             next(k for k,v in L.teams.items() if v.name==away_pick))
            st.success(f"Final: {home_pick} {res.home_crowns} - {res.away_crowns} {away_pick}")
            st.write(res.recap)
            st.json(res.contribution)

elif page == "Teams":
    st.title("🧑‍🤝‍🧑 Teams")
    team = st.selectbox("Choose a Team", [t.name for t in L.teams.values()])
    T = L.get_team(team)
    b1, b2, b3 = st.columns([1,2,2])
    with b1:
        svg_logo(T.logo_svg, 140, 140)
        st.markdown(hot_cold_pill(T.wins, T.losses), unsafe_allow_html=True)
    with b2:
        st.header(T.name)
        st.markdown(f"**GM:** {T.gm.name}  ")
        st.markdown(f"**Record:** {T.wins}-{T.losses}")
        st.markdown(f"<span class='pill pill-rank'>{T.gm.rank}</span>", unsafe_allow_html=True)
        html(f"<div class='rankbar'><div style='width:{min(100, max(0, (T.gm.points/ max(1, T.gm.next_tier_threshold))*100)):.1f}%'></div></div>", height=16)
    with b3:
        meter("Chemistry", T.chemistry, 0.25)
        meter("Fatigue", T.fatigue, 0.30)
        st.caption("Chemistry persists across seasons. Fatigue caps at +30%.")

    st.markdown("### Current Lineup")
    st.table(pd.DataFrame(T.lineup_stats()))

elif page == "Cards":
    st.title("🃏 Card Database")
    cards_df = pd.DataFrame(L.get_all_cards())
    c1, c2, c3 = st.columns(3)
    with c1:
        min_ovr = st.slider("Min OVR", 50, 99, 70)
    with c2:
        rookie_only = st.checkbox("Rookies only")
    with c3:
        tag_filter = st.multiselect("Tags", ["aggressive", "tank", "retired"]) 

    df = cards_df[cards_df["Overall"] >= min_ovr]
    if rookie_only:
        df = df[df["Rookie"] == True]
    if tag_filter:
        df = df[df["Tags"].apply(lambda s: any(t in s for t in tag_filter))]

    st.dataframe(df.sort_values("Overall", ascending=False), use_container_width=True)

elif page == "Stats & Records":
    st.title("📊 Stats & Records")
    leaders = pd.DataFrame(L.get_stat_leaders())
    st.subheader("Contribution % Leaders")
    st.table(leaders)
    st.subheader("League Records (sample)")
    st.info("Records module placeholder — hook to season history + milestones.")

elif page == "GMs":
    st.title("🧑‍💼 GM Tracker — Ranks, XP, Tweets")
    gm_df = pd.DataFrame(L.get_gm_leaderboard())
    st.dataframe(gm_df, use_container_width=True)

    st.markdown("### Rank System & Buffs")
    st.table(rank_threshold_table())

    st.markdown("### Recent GM Tweets (modern trash talk)")
    feed = L.get_news_feed()
    for line in feed[-12:][::-1]:
        st.markdown(f"<div class='tweet'>{line}</div>", unsafe_allow_html=True)

elif page == "Rivalries":
    st.title("⚔️ Rivalries")
    st.dataframe(pd.DataFrame(L.get_rivalries()), use_container_width=True)
    st.caption("Rivalry W grants a +3% stat boost for 2 games (applied in sim).")

elif page == "Awards & HOF":
    st.title("🏅 Awards & Hall of Fame")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Season Awards")
        st.table(pd.DataFrame(L.get_awards()))
        if st.button("Finalize Awards Now"):
            L.finalize_awards()
            st.success("Awards finalized for current season.")
    with col2:
        st.subheader("Hall of Fame")
        st.table(pd.DataFrame(L.get_hof()))

elif page == "League History":
    st.title("📜 League History & Eras")
    hist = L.get_history()
    st.dataframe(pd.DataFrame(hist), use_container_width=True)
    st.markdown(f"**Current Era:** {L.era}")

elif page == "News":
    st.title("📰 Media & Storylines")
    for post in L.get_news_feed()[::-1]:
        st.markdown(f"<div class='tweet'>{post}</div>", unsafe_allow_html=True)

elif page == "Trades":
    st.title("🔄 Trades — Finder & Deadline Week")
    st.subheader("Rumors")
    st.table(pd.DataFrame(L.get_trade_rumors()))
    cta1, cta2 = st.columns(2)
    if cta1.button("Generate Rumor"):
        L.generate_trade_rumors()
        st.success("New rumor generated.")
    if cta2.button("Execute Random Trade"):
        L.execute_random_trade()
        st.success("Trade executed. Lineups will re-calc.")

elif page == "Patches":
    st.title("🛠️ Patches — Buffs/Nerfs & Meta Shifts")
    st.table(pd.DataFrame(L.get_patches()))
    st.caption("Low pick-rate cards are buffed; top pick 'patch villains' get slight nerfs.")
    if st.button("Apply Patch Now"):
        L.apply_patch()
        st.success("Patch applied.")

elif page == "Rankings":
    st.title("🏆 GM Rankings & Progression")
    st.dataframe(pd.DataFrame(L.get_gm_leaderboard()), use_container_width=True)
    st.subheader("Points Model (exact values)")
    st.json(POINT_VALUES)
    st.subheader("Rank Thresholds")
    st.table(rank_threshold_table())

# Footer mini-help
st.markdown("---")
st.caption("Tip: When updating code in GitHub, replace the entire file (select all → paste) to avoid duplicate classes/functions.")
