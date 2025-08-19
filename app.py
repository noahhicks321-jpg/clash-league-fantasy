# === app.py (Home tab only) ===

import streamlit as st
from league import League

# Initialize league once in session
if "league" not in st.session_state:
    st.session_state.league = League(seed=1337, human_team_name="Your Team")


def page_home():
    L: League = st.session_state.league

    # Layout: main left column + right sidebar
    left, right = st.columns([2, 1])

    with left:
        st.title("🏠 Fantasy Clash Royale League - Home")

        # Season / Week info
        info = L.get_season_info()
        st.subheader(f"Season {info['season']} • Week {info['week']}")

        # Quick Standings
        st.markdown("### 📊 Quick Standings (Top 10)")
        standings = L.get_standings()
        data = []
        for t in standings[:10]:
            data.append({
                "Team": t.name,
                "GM": t.gm,
                "Record": t.record(),
                "Crowns ±": t.crowns_for - t.crowns_against
            })
        st.table(data)

        # User Team Chemistry
        chem = L.get_user_team_chemistry()
        st.markdown("### 🔗 Team Chemistry")
        st.progress(int(chem) if chem <= 100 else 100)
        st.caption(f"Chemistry Score: {chem:.1f}/100")

        # User Cards
        st.markdown("### 🃏 Your Cards")
        cards = L.get_user_cards()
        if not cards:
            st.info("No cards on your team yet — draft coming soon!")
        else:
            for c in cards:
                rookie_flag = "⭐ Rookie" if c.rookie else ""
                st.markdown(
                    f"**{c.name}** ({c.ovr} OVR) "
                    f"- {c.archetype}, {c.atk_type} {rookie_flag}"
                )
                st.caption(
                    f"ATK {c.stats['atk']} | DEF {c.stats['def']} | "
                    f"SPD {c.stats['speed']} | STAM {c.stats['stamina']}"
                )

    with right:
        st.markdown("### 📰 Recent News")
        for line in L.get_quick_news(6):
            st.write("• " + line)

        st.markdown("---")

        st.markdown("### 📅 Upcoming Games")
        games = L.get_upcoming_games(5)
        if not games:
            st.info("Schedule not available.")
        else:
            for (me, opp, week) in games:
                st.write(f"Week {week}: {me} vs {opp}")


# Register pages (if not already defined in your app)
if "PAGES" not in st.session_state:
    st.session_state.PAGES = {}
st.session_state.PAGES["Home"] = page_home
