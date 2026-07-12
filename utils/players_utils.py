import json
import os

PLAYERS_FILE = "players.json"


def load_players():
    if not os.path.exists(PLAYERS_FILE):
        with open(PLAYERS_FILE, "w") as f:
            json.dump([], f, indent=4)

    with open(PLAYERS_FILE, "r") as f:
        return json.load(f)


def save_players(players):
    with open(PLAYERS_FILE, "w") as f:
        json.dump(players, f, indent=4)


def player_exists(player_id):
    players = load_players()

    for player in players:
        if player["id"] == player_id:
            return True

    return False


def get_player(player_id):
    players = load_players()

    for player in players:
        if player["id"] == player_id:
            return player

    return None


def add_player(
    player_id,
    name,
    ovr,
    batting_ovr,
    bowling_ovr,
    fielding_ovr,
    fitness,
    role,
    batting_style,
    bowling_style,
    country,
    team,
    rarity,
    age,
    power,
    timing,
    technique,
    pace,
    spin,
    control,
    price,
    image
):

    players = load_players()

    if player_exists(player_id):
        return False

    player = {

        "id": player_id,

        "name": name,
        "display_name": name.upper(),

        "country": country,
        "team": team,

        "role": role,

        "rarity": rarity,

        "age": age,

        "ovr": ovr,

        "batting_ovr": batting_ovr,
        "bowling_ovr": bowling_ovr,
        "fielding_ovr": fielding_ovr,
        "fitness": fitness,

        "batting_style": batting_style,
        "bowling_style": bowling_style,

        "power": power,
        "timing": timing,
        "technique": technique,

        "pace": pace,
        "spin": spin,
        "control": control,

        "matches": 0,
        "innings": 0,
        "runs": 0,
        "balls": 0,
        "fours": 0,
        "sixes": 0,
        "highest_score": 0,
        "average": 0,
        "strike_rate": 0,

        "wickets": 0,
        "overs": 0,
        "maidens": 0,
        "economy": 0,
        "bowling_average": 0,
        "best_figures": "0/0",

        "catches": 0,
        "stumpings": 0,
        "run_outs": 0,

        "price": price,
        "sell_price": int(price * 0.7),

        "card_design": "default",
        "series": "Base",
        "release": "Season 1",

        "image": image
    }

    players.append(player)

    save_players(players)

    return True


def remove_player(player_id):

    players = load_players()

    players = [p for p in players if p["id"] != player_id]

    save_players(players)


def update_player(player_id, key, value):

    players = load_players()

    for player in players:

        if player["id"] == player_id:

            player[key] = value

            break

    save_players(players)