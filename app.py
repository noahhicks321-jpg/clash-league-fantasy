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
