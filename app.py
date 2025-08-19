# === app.py ===
import streamlit as st
from league import League

# ---------- Session State Setup ----------
if "league" not in st.session_state:
    st.session_state.league = League(seed=1337, human_team_name="Your Team")

if "page" not in st.session_state:
    st.session_state.page = "Home"

L = st.session_state.league

# ---------- Page: Home ----------
def page_home():
    st.title("🏆 Fantasy Clash Royale League")
    st.subheader(f"Season {L.season}")
    st.write(f"Total Teams: {len(L.teams)}")
    st.write(f"Total Cards in Pool: {len(L.cards)}")

    st.markdown("---")
    st.markdown("### League Summary")
    st.text(str(L))  # uses League.__str__

# ---------- Page: Draft ----------
def page_draft():
    st.title("📋 Fantasy Draft")

    # Start draft if not already active
    if L.draft is None:
        if st.button("Start Draft"):
            L.start_draft()
            st.experimental_rerun()
        return

    st.subheader(f"Round {L.draft.round} / {L.draft.max_rounds}")
    st.write(f"Pick {L.draft.pick_no} of {L.draft.total_picks}")

    gm = L.draft.current_gm()
    st.markdown(f"**On the clock: {gm}**")

    # If it's the human GM's turn
    if gm == L.human_team_name:
        st.markdown("### Available Cards")
        available = L.get_available_cards()

        # Show as buttons
        for card in available[:20]:  # only show first 20 to avoid overload
            if st.button(f"Draft {card.name} (OVR {card.ovr})"):
                L.draft_pick(card.id)
                st.experimental_rerun()

        # Sim options
        if st.button("⏭️ Sim Next Pick"):
            L.draft_auto_pick()
            st.experimental_rerun()
        if st.button("⏩ Sim to End of Draft"):
            while not L.draft.done:
                L.draft_auto_pick()
            st.experimental_rerun()

    else:
        # AI pick
        if st.button(f"Sim AI Pick ({gm})"):
            L.draft_auto_pick()
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("📜 Draft Log")
    for entry in L.get_draft_log()[::-1]:  # reverse for latest first
        st.write(entry)

# ---------- Pages Dictionary ----------
PAGES = {
    "Home": page_home,
    "Draft": page_draft,
}

# ---------- Sidebar Navigation ----------
st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state.page))
st.session_state.page = choice

# ---------- Render Page ----------
PAGES[st.session_state.page]()
