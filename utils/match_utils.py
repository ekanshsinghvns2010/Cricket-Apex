import json
import random
import time

MATCH_FILE = "matches.json"


def load_matches():
    try:
        with open(MATCH_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_matches(matches):
    with open(MATCH_FILE, "w") as f:
        json.dump(matches, f, indent=4)


def generate_match_id():
    return str(random.randint(100000, 999999))


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

        "red_captain": str(creator_id),
        "blue_captain": None,

        "message_id": None,
"channel_id": None,
"ready_players": [],

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

    for match_id, match in matches.items():
        if user_id in match["red_team"] or user_id in match["blue_team"]:
            return match_id

    return None


def join_team(match_id, user_id, team):
    matches = load_matches()

    match = matches.get(str(match_id))

    if not match:
        return False, "Match not found."

    user_id = str(user_id)

    if user_id in match["red_team"] or user_id in match["blue_team"]:
        return False, "You are already in this match."

    if team == "red":

        if len(match["red_team"]) >= match["team_size"]:
            return False, "Red Team is full."

        match["red_team"].append(user_id)

    elif team == "blue":

        if len(match["blue_team"]) >= match["team_size"]:
            return False, "Blue Team is full."

        match["blue_team"].append(user_id)

        if match["blue_captain"] is None:
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

    if user_id == match["red_captain"]:
        return False, "Red Captain cannot leave."

    if user_id in match["red_team"]:
        match["red_team"].remove(user_id)

    elif user_id in match["blue_team"]:

        match["blue_team"].remove(user_id)

        if match["blue_captain"] == user_id:

            if len(match["blue_team"]) > 0:
                match["blue_captain"] = match["blue_team"][0]
            else:
                match["blue_captain"] = None

    else:
        return False, "You are not in this match."

    save_matches(matches)

    return True, "Left successfully."


def cancel_match(match_id):
    matches = load_matches()

    if str(match_id) in matches:
        del matches[str(match_id)]
        save_matches(matches)
        return True

    return False

def set_lobby_message(match_id, channel_id, message_id):
    matches = load_matches()

    if str(match_id) not in matches:
        return

    matches[str(match_id)]["channel_id"] = str(channel_id)
    matches[str(match_id)]["message_id"] = str(message_id)

    save_matches(matches)