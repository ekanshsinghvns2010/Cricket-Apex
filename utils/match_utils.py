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

        "created_at": int(time.time())
    }

    save_matches(matches)

    return match_id