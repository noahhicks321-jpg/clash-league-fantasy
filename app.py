import streamlit as st
from league import League

# ---------- App Setup ----------
st.set_page_config(page_title="Fantasy Clash Royale League", layout="wide")

if "league" not in st.session_state:
    st.session_state.league = League(seed=1337)
L = st.session_state.league

# ---------- Page Placeholders ----------
def page_home():
    st.title("🏆 Fantasy Clash Royale League")
    st.subheader(f"Season {st.session_state.league.season}")

    render_quick_standings()

    col1, col2 = st.columns([2,1])

    with col1:
        st.markdown("### 📊 Quick Standings")
        standings = st.session_state.league.get_standings()
        st.table(standings.head(10))  # top 10 teams quick view

        st.markdown("### 🃏 Your Cards Quick Stats")
        for card in st.session_state.league.get_user_cards():
            st.metric(label=card.name, value=f"OVR {card.ovr}", delta=f"Chemistry {card.chemistry:.0f}%")

        st.markdown("### 📅 Upcoming Games")
        for game in st.session_state.league.get_upcoming_games(5):
            st.write(f"{game['team1']} vs {game['team2']} (Week {game['week']})")

    with col2:
        st.markdown("### 🧪 Team Chemistry")
        st.progress(st.session_state.league.get_user_team_chemistry()/100)

        st.markdown("### 📰 Recent News & Tweets")
        for tweet in st.session_state.league.get_recent_news(5):
            st.caption(tweet)

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

def page_home():
    st.title("🏠 League Home")

    league = st.session_state.league
    user_team = league.human_team_name

    # Layout: two columns
    col1, col2 = st.columns([2, 1])

    # --- Left Side ---
    with col1:
        st.subheader(f"Season {league.season} - Game {league.current_game}")

        # Chemistry Meter
        chem = league.get_team_chemistry(user_team)
        st.metric("Team Chemistry", f"{chem:.1f}%")

        # Upcoming Games
        st.subheader("Upcoming Games")
        games = league.get_upcoming_games(user_team)
        if games:
            for g in games:
                st.write(f"Game {g['game_num']}: {g['opponent']} ({'Home' if g['home'] else 'Away'})")
        else:
            st.write("No upcoming games scheduled.")

        # Quick Standings
        st.subheader("Quick Standings")
        st.dataframe(league.get_standings().head(10))

        # Quick Card Stats
        st.subheader("Your Cards")
        cards = league.get_team_cards(user_team)
        if cards:
            for c in cards:
                st.write(f"{c.name} | OVR {c.ovr} | Synergy {c.synergy_score}")
        else:
            st.write("No cards drafted yet.")

    # --- Right Side ---
    with col2:
        st.subheader("Recent News & Tweets")
        tweets = league.get_recent_tweets()
        for t in tweets:
            st.write("💬", t)

# === Draft Page (Snake 4 rounds, live, human picks, sim controls) ===
import pandas as pd

def page_draft():
    st.title("📝 Draft Room (Snake)")

    L: League = st.session_state.league

    # Controls Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Start Draft", use_container_width=True):
            L.start_draft()
    with c2:
        if st.button("Reset Draft", use_container_width=True):
            L.reset_draft()
    with c3:
        if st.button("Sim to Your Pick", use_container_width=True):
            L.sim_to_user_turn()
    with c4:
        if st.button("Sim Entire Draft", use_container_width=True):
            L.sim_to_end()

    # Draft status
    dm = getattr(L, "draft_manager", None)
    if not dm or not dm.is_active:
        st.info("Draft not active. Click **Start Draft** to begin (adds 4 rookies automatically).")
        if dm and dm.completed_picks:
            st.subheader("Draft Results")
            st.dataframe(pd.DataFrame(dm.last_picks_table(limit=200)))
        return

    # Round / Turn header
    st.subheader(f"Round {dm.round_num} of {dm.rounds}")
    current_tid = dm.current_team_id()
    current_team = L.teams[current_tid] if current_tid else None
    on_clock = current_team.name if current_team else "—"
    st.markdown(f"**On the clock:** {on_clock} (GM: {current_team.gm if current_team else '—'})")

    # If human turn -> selection UI
    if dm.is_human_turn():
        st.success("Your turn! Pick a card from the board below.")
    else:
        if st.button("Sim Next Pick (AI)", type="primary"):
            L.sim_next_pick()
            st.rerun()

    # Board (available players)
    st.markdown("### 🃏 Draft Board (Available Cards)")
    board = dm.available_cards_table()
    if board:
        df_board = pd.DataFrame(board)
        # nicer columns order
        cols = ["id","name","ovr","rookie","archetype","atk_type","atk","def","speed","hit_speed","stamina","base_synergy"]
        df_board = df_board[cols]

        # human pick widgets only if it's our turn
        if dm.is_human_turn():
            # pick by selecting a row
            sel = st.dataframe(df_board, use_container_width=True, hide_index=True)
            # quick chooser: top N by OVR
            top_names = [f"{r['name']} (OVR {r['ovr']})" for r in board[:30]]
            name_to_id = {f"{r['name']} (OVR {r['ovr']})": r["id"] for r in board[:30]}
            choice = st.selectbox("Quick-select from top board:", top_names)
            pick_col1, pick_col2 = st.columns([1,3])
            with pick_col1:
                if st.button("Draft Selected", type="primary"):
                    cid = name_to_id[choice]
                    L.human_pick(cid)
                    st.rerun()
        else:
            st.dataframe(df_board, use_container_width=True, hide_index=True)
    else:
        st.write("No available cards left.")

    # Right column: Live feed of picks
    st.markdown("### 📜 Live Picks")
    st.dataframe(pd.DataFrame(dm.last_picks_table(limit=40)), use_container_width=True, hide_index=True)

# --- FIX: Quick Standings Display ---
import pandas as pd  # safe to leave at top if already imported

def render_quick_standings():
    standings = st.session_state.league.get_standings()
    df = pd.DataFrame([{
        "Team": t.name,
        "GM": t.gm,
        "Wins": t.wins,
        "Losses": t.losses,
        "Crowns For": t.crowns_for,
        "Crowns Against": t.crowns_against
    } for t in standings])

    st.subheader("Quick Standings (Top 10)")
    st.table(df.head(10))

