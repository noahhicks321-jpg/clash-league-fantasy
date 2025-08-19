# === app.py ===
# Fantasy Clash Royale League UI
# Spec Milestone 1 – Basic skeleton with dark theme + navigation

import streamlit as st
from league import League

st.set_page_config(page_title="Fantasy Clash League", layout="wide")

# Initialize session state
if "league" not in st.session_state:
    st.session_state.league = None
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Pages dict (will grow in later milestones)
PAGES = {}

# Sidebar Navigation
st.sidebar.title("Navigation")
choice = st.sidebar.radio(
    "Go to",
    ["Home", "Draft", "Standings", "Leaders", "Playoffs", "Twitter", "History"]
)
st.session_state.page = choice

# Dark theme styling (Streamlit doesn't allow full override, so simulate)
st.markdown(
    """
    <style>
        body { background-color: #0E1117; color: white; }
        .stMetric { color: white !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Page Handlers ---
def page_home():
    st.title("🏆 Fantasy Clash Royale League")
    st.write("Welcome! Use the sidebar to navigate.")

PAGES["Home"] = page_home

# Render current page
PAGES[st.session_state.page]()

# === Continue in app.py ===
# Milestone 2 – Hook league + draft screen placeholder

# --- Page Handlers ---
def page_home():
    st.title("🏆 Fantasy Clash Royale League")

    if st.button("Start New League"):
        st.session_state.league = League(seed=1337, human_team_name="Your Team")
        st.success("League created!")

    if st.session_state.league:
        st.write(st.session_state.league)

def page_draft():
    st.title("📋 Draft Room")
    if not st.session_state.league:
        st.warning("Start a league first on Home page.")
        return
    st.write("Draft system coming next milestone...")

# Register new pages
PAGES["Home"] = page_home
PAGES["Draft"] = page_draft

# Render current page
PAGES[st.session_state.page]()

def page_home():
    st.title("🏆 Fantasy Clash Royale League")

    if st.button("Start New League"):
        st.session_state.league = League(seed=1337, human_team_name="Your Team")
        st.success("League created!")

    if st.session_state.league:
        L = st.session_state.league
        st.subheader("League Summary")
        st.write(str(L))

        st.subheader("Teams")
        for tid, team in L.teams.items():
            st.write(f"- {team.name} (GM: {team.gm})")

def page_draft():
    st.title("📋 Fantasy Draft")

    if st.button("Run Draft"):
        results, grades = st.session_state.league.run_draft()
        st.session_state.draft_results = results
        st.session_state.draft_grades = grades

    if "draft_results" in st.session_state:
        st.subheader("Draft Results")
        for team, card in st.session_state.draft_results:
            st.write(f"{team.name} drafted {card.name} (OVR {card.ovr})")

        st.subheader("Draft Grades")
        for team, grade in st.session_state.draft_grades.items():
            st.write(f"{team}: {grade}")

PAGES = {
    "Home": page_home,
    "Draft": page_draft,
}




