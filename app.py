# === app.py ===
import streamlit as st
from league import League

# ---------- Session State Setup ----------
if "league" not in st.session_state:
    st.session_state.league = League(seed=1337, human_team_name="You")

if "page" not in st.session_state:
    st.session_state.page = "Home"

L = st.session_state.league

# ---------- Page Functions ----------
def page_home():
    st.title("🏆 Fantasy Clash Royale League")
    st.write("Welcome to the League Simulator!")

    st.subheader("League Status")
    st.write(str(L))  # calls League.__str__

    if st.button("Start New Draft"):
        L.start_draft()
        st.session_state.page = "Draft"
        st.rerun()


def page_draft():
    st.title("📝 Fantasy Draft (4 Rounds)")

    if not L.draft_in_progress:
        st.info("No draft in progress. Go back to Home to start a new draft.")
        return

    st.subheader(f"Round {L.draft.round_num} – Pick {L.draft.pick_num}")

    # --- Human turn ---
    if L.draft.current_gm == "You":
        st.success("✅ Your turn to draft!")

        available = L.get_available_cards()
        for c in available[:25]:  # limit to 25 for readability
            if st.button(f"Draft {c.name} (OVR {c.ovr})"):
                L.draft_pick("You", c.id)
                st.rerun()

        if st.button("Sim My Pick (Auto Pick Best)"):
            L.draft_auto_pick("You")
            st.rerun()

    # --- AI turn ---
    else:
        st.warning(f"🤖 {L.draft.current_gm}'s turn...")
        if st.button("Sim Next AI Pick"):
            L.draft_auto_pick(L.draft.current_gm)
            st.rerun()

    # --- Controls ---
    st.divider()
    if st.button("Sim To End of Draft"):
        while L.draft_in_progress:
            L.draft_auto_pick(L.draft.current_gm)
        st.success("Draft finished!")
        st.session_state.page = "Draft Results"
        st.rerun()

    # --- Draft Log ---
    st.subheader("📜 Draft Log")
    for line in reversed(L.get_draft_log()[-50:]):
        st.write(line)


def page_draft_results():
    st.title("📊 Draft Results & Grades")

    if L.draft_in_progress:
        st.warning("Draft still in progress. Finish draft first.")
        return

    results, grades = L.get_draft_results()

    st.subheader("🏆 Draft Grades")
    for gm, grade in grades.items():
        st.write(f"**{gm}**: {grade}")

    st.subheader("📜 Full Draft Board")
    for line in results:
        st.write(line)


# ---------- Page Registry ----------
PAGES = {
    "Home": page_home,
    "Draft": page_draft,
    "Draft Results": page_draft_results,
}

# ---------- Sidebar Navigation ----------
st.sidebar.title("Navigation")
if st.sidebar.button("🏠 Home"):
    st.session_state.page = "Home"
    st.rerun()
if st.sidebar.button("📝 Draft"):
    st.session_state.page = "Draft"
    st.rerun()
if st.sidebar.button("📊 Draft Results"):
    st.session_state.page = "Draft Results"
    st.rerun()

# ---------- Render Selected Page ----------
PAGES[st.session_state.page]()

