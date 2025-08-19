# === app.py ===
# Fantasy Clash Royale League UI
# Spec Milestone 1 – Basic skeleton with dark theme + navigation

import streamlit as st
from league import League

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "league" not in st.session_state:
    from league import League
    st.session_state.league = League(seed=1337, human_team_name=None)

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

def page_draft():
    L = st.session_state.league

    # --- Start Draft ---
    if L.draft is None:
        st.title("Fantasy Draft")
        if st.button("Start Draft"):
            L.start_draft()
            st.rerun()
        return

    st.title(f"Draft - Round {L.draft.current_round}, Pick {L.draft.pick_in_round+1}")

    # --- Available Cards ---
    st.subheader("Available Cards")
    available = L.get_available_cards()
    for c in available[:20]:  # only show top 20 by OVR for now
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.write(f"{c.name} ({c.archetype.value}, {c.atk_type.value})")
        with col2:
            st.write(f"OVR {c.ovr}")
        with col3:
            if st.button(f"Draft {c.name}", key=f"pick_{c.id}"):
                L.draft_pick("Human GM", c.id)
                st.rerun()

    # --- Draft Controls ---
    st.subheader("Draft Controls")
    if st.button("Sim Next AI Pick"):
        next_gm = L.draft.get_current_gm()
        if next_gm != "Human GM":
            L.draft_auto_pick(next_gm)
        st.rerun()

    if st.button("Sim to End of Draft"):
        while not L.draft.is_complete():
            gm = L.draft.get_current_gm()
            if gm == "Human GM":
                # if user skips, auto pick best available
                L.draft_auto_pick(gm)
            else:
                L.draft_auto_pick(gm)
        st.rerun()

    # --- Draft Log ---
    st.subheader("Draft Log")
    for pick in L.get_draft_log():
        st.write(f"Round {pick.round} | {pick.gm_name} drafted {pick.card_name} (OVR {pick.card_ovr})")

    # --- Draft Complete ---
    if L.draft.is_complete():
        st.success("Draft Complete!")

