import random
import pandas as pd

# -----------------
# League Entities
# -----------------

class Card:
    def __init__(self, name, atk, atk_type, defense, speed, hit_speed, stamina, overall, rookie=False):
        self.name = name
        self.atk = atk
        self.atk_type = atk_type
        self.defense = defense
        self.speed = speed
        self.hit_speed = hit_speed
        self.stamina = stamina
        self.overall = overall
        self.rookie = rookie
        self.pick_rate = 0
        self.contribution = 0
        self.trend = "="  # ↑ ↓ =

    def to_dict(self):
        return {
            "Name": self.name,
            "ATK": self.atk,
            "ATK Type": self.atk_type,
            "DEF": self.defense,
            "Speed": self.speed,
            "Hit Speed": self.hit_speed,
            "Stamina": self.stamina,
            "Overall": self.overall,
            "Rookie": self.rookie,
            "Pick Rate %": self.pick_rate,
            "Trend": self.trend,
            "Contribution %": self.contribution
        }


class GM:
    def __init__(self, name):
        self.name = name
        self.rank = "Bronze I"
        self.points = 0
        self.wins = 0
        self.losses = 0
        self.trophies = []
        self.rivalries = {}
        self.personality = random.choice(["🎤 Showman", "🥷 Silent Killer", "🔥 Hype Machine", "🐍 Toxic Troll", "📊 Analyst"])

    def add_points(self, pts):
        self.points += pts
        self.update_rank()

    def update_rank(self):
        ranks = [
            (0, "Bronze I"), (1000, "Bronze II"), (2000, "Silver I"), (3200, "Silver II"),
            (4500, "Gold I"), (6000, "Gold II"), (7800, "Platinum"), (10000, "Diamond"),
            (12500, "Opal"), (15000, "Dark Matter"), (18000, "Champion"),
            (21500, "GOAT"), (25000, "Hall of Fame")
        ]
        for threshold, rank in reversed(ranks):
            if self.points >= threshold:
                self.rank = rank
                break

    def trash_talk(self):
        lines = [
            f"{self.name}: 'Y’all can’t touch me rn 🔥'",
            f"{self.name}: 'Washed? Nah, I’m legendary 👑'",
            f"{self.name}: 'Patch buffs? Still cooking 😤'",
            f"{self.name}: 'Dark Matter GM vibes 💎'",
            f"{self.name}: 'Rivals? Easy clap.'"
        ]
        return random.choice(lines)

    def to_dict(self):
        return {
            "GM": self.name,
            "Rank": self.rank,
            "Points": self.points,
            "W": self.wins,
            "L": self.losses,
            "Personality": self.personality,
            "Trophies": ", ".join(self.trophies)
        }


class Team:
    def __init__(self, name, gm, logo="🏰"):
        self.name = name
        self.gm = gm
        self.logo = logo
        self.wins = 0
        self.losses = 0
        self.lineup = []
        self.backup = None
        self.history = []

    def add_win(self):
        self.wins += 1
        self.gm.wins += 1
        self.gm.add_points(50)

    def add_loss(self):
        self.losses += 1
        self.gm.losses += 1
        self.gm.add_points(-50)

    def to_dict(self):
        return {
            "Team": self.name,
            "GM": self.gm.name,
            "Logo": self.logo,
            "Record": f"{self.wins}-{self.losses}",
            "Rank": self.gm.rank
        }


# -----------------
# League Core
# -----------------

class League:
    def __init__(self):
        self.teams = []
        self.cards = []
        self.season = 1
        self.history = []
        self.awards = []
        self.hof = []
        self.rivalries = []
        self.patches = []
        self.calendar = self.generate_calendar()
        self.playoff_bracket = {}

    def add_team(self, team):
        self.teams.append(team)

    def add_card(self, card):
        self.cards.append(card)

    def get_team_list(self):
        return [t.to_dict() for t in self.teams]

    def get_team(self, name):
        for t in self.teams:
            if t.name == name:
                return t
        return None

    def get_all_cards(self):
        return pd.DataFrame([c.to_dict() for c in self.cards])

    def get_standings(self):
        df = pd.DataFrame([t.to_dict() for t in self.teams])
        return df.sort_values(by="Record", ascending=False)

    def get_gm_leaderboard(self):
        df = pd.DataFrame([t.gm.to_dict() for t in self.teams])
        return df.sort_values(by="Points", ascending=False)

    def get_rivalries(self):
        return pd.DataFrame(self.rivalries)

    def get_awards(self):
        return pd.DataFrame(self.awards)

    def get_hof(self):
        return pd.DataFrame(self.hof)

    def get_history(self):
        return self.history

    def get_news(self):
        return [gm.trash_talk() for gm in [t.gm for t in self.teams]]

    def get_trade_rumors(self):
        return pd.DataFrame({"Rumor": ["Team A shopping Card X", "Team B interested in Rookie Y"]})

    def get_patches(self):
        return pd.DataFrame(self.patches)

    def generate_calendar(self):
        # Placeholder 20 week calendar with randomized matchups
        schedule = []
        for week in range(1, 21):
            matchups = []
            for i in range(0, len(self.teams), 2):
                if i+1 < len(self.teams):
                    matchups.append((self.teams[i].name, self.teams[i+1].name))
            schedule.append({"week": week, "matchups": matchups})
        return schedule

    def generate_playoff_bracket(self):
        # Seed top 16 teams by record
        standings = sorted(self.teams, key=lambda x: x.wins, reverse=True)
        bracket = {}
        for i in range(8):
            bracket[f"Round1_Match{i+1}"] = (standings[i].name, standings[15-i].name)
        self.playoff_bracket = bracket
        return bracket

    def all_league_teams(self):
        # Simplified All-League 1st/2nd/3rd teams
        sorted_cards = sorted(self.cards, key=lambda c: c.overall, reverse=True)
        return {
            "1st Team": [c.name for c in sorted_cards[:5]],
            "2nd Team": [c.name for c in sorted_cards[5:10]],
            "3rd Team": [c.name for c in sorted_cards[10:15]]
        }

    def gm_trophy_case(self, gm_name):
        gm = None
        for t in self.teams:
            if t.gm.name == gm_name:
                gm = t.gm
        if gm:
            return gm.trophies
        return []


# -----------------
# FACTORY
# -----------------

def get_league():
    L = League()

    # Generate sample GMs and Teams
    for i in range(30):
        gm = GM(f"GM_{i+1}")
        team = Team(f"Team_{i+1}", gm, logo=random.choice(["🐉","🦁","🦅","🐺","🐯"]))
        L.add_team(team)

    # Generate sample Cards
    for i in range(160):
        card = Card(
            name=f"Card_{i+1}",
            atk=random.randint(60,100),
            atk_type=random.choice(["Melee","Ranged"]),
            defense=random.randint(50,100),
            speed=random.randint(50,100),
            hit_speed=random.randint(50,100),
            stamina=random.randint(60,100),
            overall=random.randint(60,100),
            rookie=True if i % 40 == 0 else False
        )
        L.add_card(card)

    return L
