import streamlit as st
from league import League

# ---------- App Setup ----------
st.set_page_config(page_title="Fantasy Clash Royale League", layout="wide")

if "league" not in st.session_state:
    st.session_state.league = League(seed=1337)
L = st.session_state.league

# ---------- Page Placeholders ----------
def page_home():
    st.title("🏠 Home")
    st.write("Welcome to the Fantasy Clash Royale League.")
    st.write("Season overview, standings, and featured news will go here.")

def page_draft():
    st.title("📝 Draft")
    st.write("Draft board, user picks, AI picks, and draft grades will go here.")

def page_sim():
    st.title("🎮 Simcast Live")
    st.write("Simulated games with timer controls (1x/2x/4x/8x) will go here.")

def page_standings():
    st.title("📊 Standings & Power Rankings")
    st.write("Season standings and weekly power rankings will go here.")

def page_leaders():
    st.title("🏅 League Leaders & Awards")
    st.write("Crowns, averages, awards, All-Star voting will go here.")

def page_cards():
    st.title("🃏 Card Profiles & Synergies")
    st.write("Card pool, stats, synergies, and seasonal meta shifts will go here.")

def page_patch_notes():
    st.title("📜 Patch Notes")
    st.write("Buffs/nerfs and meta reports before each season’s draft will go here.")

def page_playoffs():
    st.title("🏆 Playoffs & Bracket")
    st.write("Interactive playoff bracket and dynasty tracker will go here.")

def page_rivalries():
    st.title("🔥 Rivalries")
    st.write("Rivalry intensity meters and boosts will go here.")

def page_history():
    st.title("📖 History & Hall of Legends")
    st.write("Awards history, records, and HOF will go here.")

def page_twitter():
    st.title("🐦 Twitter Feed")
    st.write("GM tweets, fan reactions, and draft/patch debates will go here.")

# ---------- Page Registry ----------
PAGES = {
    "Home": page_home,
    "Draft": page_draft,
    "Simcast": page_sim,
    "Standings": page_standings,
    "Leaders & Awards": page_leaders,
    "Cards & Synergies": page_cards,
    "Patch Notes": page_patch_notes,
    "Playoffs": page_playoffs,
    "Rivalries": page_rivalries,
    "History & Hall of Legends": page_history,
    "Twitter": page_twitter,
}

# ---------- Sidebar Navigation ----------
if "page" not in st.session_state:
    st.session_state.page = "Home"

st.sidebar.title("📂 Navigation")
choice = st.sidebar.radio("Go to:", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state.page))
st.session_state.page = choice

# ---------- Render Selected Page ----------
PAGES[st.session_state.page]()

# ------------------------
# Home Page
# ------------------------
def page_home():
    L: League = st.session_state.league

    st.title("🏠 League Home")

    # --- Season / Game Info + Chemistry ---
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"Season {L.season} • Game {L.current_game+1}/{L.total_games}")
    with col2:
        chem = L.get_team_chemistry(L.human_team)
        st.metric("Team Chemistry", f"{chem:.0f}%", delta=None)

    st.markdown("---")

    # --- Layout: Left (Standings + User Cards) / Right (News Feed) ---
    left, right = st.columns([2, 1])

    # LEFT SIDE
    with left:
        # Quick Standings
        st.subheader("📊 Quick Standings")
        standings = L.get_standings()
        st.table(standings.head(5))  # only top 5 for quick glance

        # User Cards
        st.subheader("🃏 Your Cards")
        user_cards = L.get_team_cards(L.human_team)
        for c in user_cards:
            st.markdown(
                f"**{c.name}** (OVR {c.ovr}) — "
                f"ATK {c.stats['atk']}, DEF {c.stats['def']}, SPD {c.stats['speed']} "
                f" | Crowns: {c.crowns_total}"
            )

    # RIGHT SIDE
    with right:
        st.subheader("📰 Recent News")
        feed = L.get_recent_tweets(limit=8)
        for post in feed:
            st.markdown(f"- {post}")

    st.markdown("---")

    # --- Upcoming Games ---
    st.subheader("📅 Upcoming Games")
    games = L.get_upcoming_games(L.human_team, num=3)
    for g in games:
        st.markdown(f"- {g['opponent']} (Game {g['game_num']})")

