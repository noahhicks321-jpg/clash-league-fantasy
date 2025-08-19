# === app.py (Milestone 1B foundation) ===
import streamlit as st
from league import League

# ---------- session init ----------
if "league" not in st.session_state:
    st.session_state.league = League(seed=1337, human_team_name="Your Team")
if "page" not in st.session_state:
    st.session_state.page = "Home"

L: League = st.session_state.league

# ---------- pages ----------
def page_home():
    st.title("🏆 Fantasy Clash Royale League")
    st.subheader(f"Season {L.season}")
    st.write(str(L))

    if st.button("Play Random Game"):
        import random
        t1, t2 = random.sample(L.teams, 2)
        result = L.play_game(t1, t2)
        st.success(result)

def page_standings():
    st.title("📊 League Standings")
    table = [{"Team": t.name, "GM": t.gm, "Record": t.record()} for t in L.standings()]
    st.table(table)

# ---------- registry ----------
PAGES = {
    "Home": page_home,
    "Standings": page_standings,
}

# ---------- sidebar nav ----------
st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state.page))
st.session_state.page = choice

# run selected page
PAGES[choice]()

# === Milestone 2B: Draft page starter ===

def page_draft():
    st.title("📝 Draft Room")

    if "draft" not in st.session_state:
        st.session_state.draft = DraftManager(L)

    draft: DraftManager = st.session_state.draft

    if not draft.is_finished():
        if st.button("Sim Next Pick"):
            pick = draft.next_pick()
            if pick:
                st.success(f"Round {pick.round}, Pick {pick.pick_num}: {pick.team} drafted {pick.card} (OVR {pick.ovr})")
    else:
        st.success("✅ Draft complete!")

    # show draft results table
    if draft.picks:
        table = [{"Round": p.round, "Pick": p.pick_num, "Team": p.team, "Card": p.card, "OVR": p.ovr} for p in draft.picks]
        st.table(table)

PAGES = {
    "Home": page_home,
    "Standings": page_standings,
    "Draft": page_draft,
}

# === Milestone 3B: Human interactive draft ===

def page_draft():
    st.title("📝 Draft Room")

    if "draft" not in st.session_state:
        # initialize with human GM = "Team 1" for now
        st.session_state.draft = HumanDraftManager(L, human_team_name="Team 1")

    draft: HumanDraftManager = st.session_state.draft

    if not draft.is_finished():
        team_idx = (draft.current_pick - 1) % len(L.teams)
        current_team = L.teams[team_idx]

        st.subheader(f"Round {draft.current_round}, Pick {draft.current_pick}")
        st.write(f"On the clock: **{current_team.name}**")

        if draft.human_team and current_team == draft.human_team:
            st.info("Your pick! Choose a card:")

            available = [(cid, L.cards[cid]) for cid in draft.available_cards]
            available_sorted = sorted(available, key=lambda x: x[1].ovr, reverse=True)

            card_names = [f"{c.name} (OVR {c.ovr})" for cid, c in available_sorted]
            card_map = {f"{c.name} (OVR {c.ovr})": cid for cid, c in available_sorted}

            choice = st.selectbox("Available Cards:", card_names)
            if st.button("Draft Player"):
                cid = card_map[choice]
                pick = draft.next_pick(chosen_card_id=cid)
                if pick:
                    st.success(f"You drafted {pick.card} (OVR {pick.ovr})")
        else:
            if st.button("Sim Next Pick"):
                pick = draft.next_pick()
                if pick:
                    st.success(f"{pick.team} drafted {pick.card} (OVR {pick.ovr})")
    else:
        st.success("✅ Draft complete!")

    # show draft results
    if draft.picks:
        table = [{"Round": p.round, "Pick": p.pick_num, "Team": p.team, "Card": p.card, "OVR": p.ovr} for p in draft.picks]
        st.table(table)
