import streamlit as st
from league import get_league

# -----------------
# UI CONFIG
# -----------------
st.set_page_config(page_title="Clash Royale Fantasy League", layout="wide")

# Custom CSS for dark sports-style theme
st.markdown(
    """
    <style>
    body { background: linear-gradient(135deg, #0a0f1d, #1c1f33); color: white; }
    .sidebar .sidebar-content { background: #10131f; }
    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; }
    .stButton>button { background: #e63946; color: white; border-radius: 10px; }
    .stButton>button:hover { background: #ff6b81; }
    .metric { background: #22273b; padding: 12px; border-radius: 12px; text-align: center; }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------
# LEAGUE STATE
# -----------------
L = get_league()

# Sidebar navigation
st.sidebar.title("⚔️ Fantasy League Menu")
page = st.sidebar.radio("Navigate", [
    "Home", "Teams", "Cards", "Stats", "GMs", "Rivalries", "Awards & HOF", 
    "League History", "News", "Trades", "Patches", "Rankings"
])

# -----------------
# PAGES
# -----------------
if page == "Home":
    st.title("🏠 League Home")
    st.subheader("Live Standings")
    standings = L.get_standings()
    st.dataframe(standings)

    st.subheader("Latest Headlines")
    for headline in L.get_news():
        st.write(f"- {headline}")

elif page == "Teams":
    st.title("🧑‍🤝‍🧑 Teams")
    team = st.selectbox("Choose a Team", [t.name for t in L.teams])
    T = L.get_team(team)
    st.header(T.name)
    st.write(f"GM: {T.gm.name}")
    st.write(f"Record: {T.wins}-{T.losses}")
    st.write("### Current Lineup")
    st.table(T.lineup_stats())

elif page == "Cards":
    st.title("🃏 Card Database")
    cards_df = L.get_all_cards()
    st.dataframe(cards_df)

elif page == "Stats":
    st.title("📊 Stats & Records")
    leaders = L.get_stat_leaders()
    st.write("### Stat Leaders")
    st.table(leaders)

elif page == "GMs":
    st.title("🧑‍💼 GM Tracker")
    gm_df = L.get_gm_leaderboard()
    st.dataframe(gm_df)

elif page == "Rivalries":
    st.title("⚔️ Rivalries")
    st.dataframe(L.get_rivalries())

elif page == "Awards & HOF":
    st.title("🏅 Awards & Hall of Fame")
    st.write("### Season Awards")
    st.table(L.get_awards())
    st.write("### Hall of Fame")
    st.table(L.get_hof())

elif page == "League History":
    st.title("📜 League History")
    history = L.get_history()
    for season in history:
        st.subheader(f"Season {season['season_num']}")
        st.write(season['summary'])

elif page == "News":
    st.title("📰 Media & News")
    for post in L.get_news_feed():
        st.write(post)

elif page == "Trades":
    st.title("🔄 Trades")
    st.write("Upcoming trade finder and deadline week tracker.")
    st.table(L.get_trade_rumors())

elif page == "Patches":
    st.title("🛠️ Patches")
    st.table(L.get_patches())

elif page == "Rankings":
    st.title("🏆 GM Rankings")
    gm_df = L.get_gm_leaderboard()
    st.dataframe(gm_df)
    st.write("Ranks auto-update with points from wins/losses/playoffs.")
