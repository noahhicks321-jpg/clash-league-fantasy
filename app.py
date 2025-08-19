# === app.py ===
import streamlit as st
from league import League

# Initialize session state
if "league" not in st.session_state:
    st.session_state.league = League(seed=1337, human_team_name="Your Team")
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------- Page Functions ----------
def page_home():
    st.title("Fantasy Clash Royale League")
    st.write("Welcome to the Fantasy Clash Royale League.")
    st.write("Season overview, standings, and featured news will go here.")

    # Quick standings table
    standings = st.session_state.league.get_standings()
    st.subheader("Quick Standings")
    data = [
        {"Team": t.name, "Wins": t.wins, "Losses": t.losses}
        for t in standings
    ]
    st.table(data)

# ---------- Page Navigation ----------
PAGES = {
    "Home": page_home,
}

st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", list(PAGES.keys()))
st.session_state.page = choice

# Render current page
PAGES[st.session_state.page]()

# ---------- Page Functions ----------

def page_home():
    st.title("🏠 Home")
    # Add homepage features below (recent news, quick standings, chemistry, etc.)


def page_draft():
    st.title("📝 Draft")
    # Add draft UI (snake order, rookies, user picks) below


def page_games():
    st.title("🎮 Games & Simulation")
    # Add upcoming games, live sim, results below


def page_cards():
    st.title("🃏 Cards")
    # Add card database, stats, synergies, archetypes below


def page_standings():
    st.title("📊 Standings")
    # Add league standings table below


def page_awards():
    st.title("🏆 Awards & Leaders")
    # Add league leaders, MVP race, All-Star voting below


def page_history():
    st.title("📖 History & Hall of Fame")
    # Add past seasons, champions, Hall of Legends below


def page_twitter():
    st.title("🐦 League Twitter Feed")
    # Add GM tweets, fan chatter, memes below


# ---------- Page Navigation ----------
PAGES = {
    "Home": page_home,
    "Draft": page_draft,
    "Games": page_games,
    "Cards": page_cards,
    "Standings": page_standings,
    "Awards": page_awards,
    "History": page_history,
    "Twitter": page_twitter,
}

st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", list(PAGES.keys()))
st.session_state.page = choice

# Render selected page
PAGES[st.session_state.page]()


