
import json
import random
import time

MATCH_FILE = "matches.json"


def load_matches():
    try:
        with open(MATCH_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_matches(matches):
    with open(MATCH_FILE, "w", encoding="utf-8") as file:
        json.dump(matches, file, indent=4)


def generate_match_id():
    matches = load_matches()

    while True:
        match_id = str(random.randint(100000, 999999))
        if match_id not in matches:
            return match_id


def create_match(
    creator_id,
    guild_id,
    overs,
    match_format,
    team_size,
    stadium
):
    matches = load_matches()
    match_id = generate_match_id()

    matches[match_id] = {
        "guild_id": str(guild_id),
        "status": "lobby",
        "creator": str(creator_id),
        "overs": overs,
        "format": match_format,
        "team_size": team_size,
        "stadium": stadium["name"],
        "country": stadium["country"],
        "weather": stadium["weather"],
        "pitch": stadium["pitch"],
        "red_team": [str(creator_id)],
        "blue_team": [],
        "red_bots": [],
        "blue_bots": [],
        "red_captain": str(creator_id),
        "blue_captain": None,
        "message_id": None,
        "channel_id": None,
        "ready_players": [],
        "state": "LOBBY",
        "toss_winner": None,
        "toss_choice": None,
        "innings": 1,
        "batting_team": None,
        "bowling_team": None,
        "runs": 0,
        "wickets": 0,
        "overs_completed": 0,
        "balls": 0,
        "target": None,
        "striker": None,
        "non_striker": None,
        "current_bowler": None,
        "winner": None,
        "player_of_match": None,
        "created_at": int(time.time())
    }

    save_matches(matches)
    return match_id


def get_match(match_id):
    matches = load_matches()
    return matches.get(str(match_id))


def find_player_match(user_id):
    matches = load_matches()
    user_id = str(user_id)

    # Search newest matches first.
    for match_id, match in reversed(list(matches.items())):
        red_team = match.get("red_team", [])
        blue_team = match.get("blue_team", [])

        if user_id in red_team or user_id in blue_team:
            return match_id

    return None


def join_team(match_id, user_id, team):
    matches = load_matches()
    match = matches.get(str(match_id))

    if not match:
        return False, "Match not found."

    if match.get("status") != "lobby":
        return False, "This match is no longer accepting players."

    user_id = str(user_id)

    red_team = match.setdefault("red_team", [])
    blue_team = match.setdefault("blue_team", [])

    if user_id in red_team or user_id in blue_team:
        return False, "You are already in this match."

    if team == "red":
        if len(red_team) + len(match.get("red_bots", [])) >= match["team_size"]:
            return False, "Red Team is full."

        red_team.append(user_id)

    elif team == "blue":
        if len(blue_team) + len(match.get("blue_bots", [])) >= match["team_size"]:
            return False, "Blue Team is full."

        blue_team.append(user_id)

        if match.get("blue_captain") is None:
            match["blue_captain"] = user_id

    else:
        return False, "Invalid team."

    save_matches(matches)
    return True, "Joined successfully."


def leave_team(match_id, user_id):
    matches = load_matches()
    match = matches.get(str(match_id))

    if not match:
        return False, "Match not found."

    user_id = str(user_id)

    if user_id == match.get("red_captain"):
        return False, "Red Captain cannot leave."

    if user_id in match.get("red_team", []):
        match["red_team"].remove(user_id)

    elif user_id in match.get("blue_team", []):
        match["blue_team"].remove(user_id)

        if match.get("blue_captain") == user_id:
            match["blue_captain"] = (
                match["blue_team"][0]
                if match["blue_team"]
                else None
            )
    else:
        return False, "You are not in this match."

    save_matches(matches)
    return True, "Left successfully."


def cancel_match(match_id):
    matches = load_matches()
    match_id = str(match_id)

    if match_id not in matches:
        return False

    del matches[match_id]
    save_matches(matches)
    return True


def set_lobby_message(match_id, channel_id, message_id):
    matches = load_matches()
    match = matches.get(str(match_id))

    if match is None:
        return False

    match["channel_id"] = str(channel_id)
    match["message_id"] = str(message_id)

    save_matches(matches)
    return True
