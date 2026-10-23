
# utils/match_flow.py

from utils.match_utils import load_matches, save_matches

VALID_TEAMS = ("red", "blue")


def get_match(match_id):
    return load_matches().get(str(match_id))


def update_match(match_id, updates):
    matches = load_matches()
    key = str(match_id)

    if key not in matches:
        raise ValueError(f"Match {key} was not found.")

    matches[key].update(updates)
    save_matches(matches)
    return matches[key]


def start_xi_selection(match_id):
    matches = load_matches()
    key = str(match_id)

    if key not in matches:
        raise ValueError(f"Match {key} was not found.")

    match = matches[key]

    if not match.get("batting_team") or not match.get("bowling_team"):
        raise ValueError("The toss must finish before XI selection.")

    if (
        match["batting_team"] not in VALID_TEAMS
        or match["bowling_team"] not in VALID_TEAMS
        or match["batting_team"] == match["bowling_team"]
    ):
        raise ValueError("The toss returned invalid teams.")

    match["status"] = "selecting"
    match["state"] = "PLAYER_SELECTION"
    match["xi_confirmed"] = {"red": False, "blue": False}
    match["card_selections"] = []
    match["red_xi"] = []
    match["blue_xi"] = []
    match.pop("xi_confirmation_posted", None)
    match["interaction_stage"] = "card_selection"

    save_matches(matches)
    return match


def start_xi_confirmation(match_id):
    matches = load_matches()
    key = str(match_id)

    if key not in matches:
        raise ValueError(f"Match {key} was not found.")

    match = matches[key]

    if match.get("status") != "selecting":
        raise ValueError("The match is not in player-selection stage.")

    for team in VALID_TEAMS:
        xi = match.get(f"{team}_xi", [])

        if len(xi) != 11:
            raise ValueError(
                f"{team} must have exactly 11 player cards."
            )

        player_ids = [
            str(player.get("id") or player.get("player_id") or "")
            for player in xi
            if isinstance(player, dict)
        ]

        if (
            len(player_ids) != 11
            or any(not player_id for player_id in player_ids)
            or len(set(player_ids)) != 11
        ):
            raise ValueError(
                f"{team} has missing or duplicate player IDs."
            )

    match["status"] = "xi_confirmation"
    match["state"] = "XI_CONFIRMATION"
    match["xi_confirmed"] = {"red": False, "blue": False}
    match["interaction_stage"] = "xi_confirmation"

    save_matches(matches)
    return match


def start_opening_selection(match_id):
    matches = load_matches()
    key = str(match_id)

    if key not in matches:
        raise ValueError(f"Match {key} was not found.")

    match = matches[key]

    if match.get("status") not in {
        "xi_confirmation",
        "ready_to_play",
        "opening_selection",
    }:
        raise ValueError("Both XIs must be confirmed first.")

    confirmed = match.get("xi_confirmed", {})

    if not all(confirmed.get(team, False) for team in VALID_TEAMS):
        raise ValueError("Both captains must confirm their XIs.")

    for team in VALID_TEAMS:
        xi = match.get(f"{team}_xi", [])
        ids = [
            str(player.get("id") or player.get("player_id") or "")
            for player in xi
            if isinstance(player, dict)
        ]

        if (
            len(ids) != 11
            or any(not player_id for player_id in ids)
            or len(set(ids)) != 11
        ):
            raise ValueError(f"{team} does not have a valid XI.")

    match["status"] = "opening_selection"
    match["state"] = "OPENING_SELECTION"
    match["interaction_stage"] = "opening_selection"
    match["striker"] = None
    match["non_striker"] = None
    match["current_bowler"] = None

    save_matches(matches)
    return match


def start_live_match(match_id):
    matches = load_matches()
    key = str(match_id)

    if key not in matches:
        raise ValueError(f"Match {key} was not found.")

    match = matches[key]

    if match.get("status") != "opening_selection":
        raise ValueError("Opening selection is not active.")

    confirmed = match.get("xi_confirmed", {})

    if not all(confirmed.get(team, False) for team in VALID_TEAMS):
        raise ValueError("Both captains must confirm their XIs.")

    striker = match.get("striker")
    non_striker = match.get("non_striker")
    bowler = match.get("current_bowler")

    if not striker or not non_striker or not bowler:
        raise ValueError(
            "Select the opening striker, non-striker, and bowler first."
        )

    def get_id(player):
        if isinstance(player, dict):
            return str(player.get("id") or player.get("player_id") or "")
        return str(player or "")

    striker_id = get_id(striker)
    non_striker_id = get_id(non_striker)
    bowler_id = get_id(bowler)

    if (
        not striker_id
        or not non_striker_id
        or striker_id == non_striker_id
    ):
        raise ValueError("Opening batters must be distinct valid players.")

    batting_team = match.get("batting_team")
    bowling_team = match.get("bowling_team")

    if batting_team not in VALID_TEAMS or bowling_team not in VALID_TEAMS:
        raise ValueError("The batting or bowling team is invalid.")

    batting_ids = {
        get_id(player)
        for player in match.get(f"{batting_team}_xi", [])
    }
    bowling_ids = {
        get_id(player)
        for player in match.get(f"{bowling_team}_xi", [])
    }

    if striker_id not in batting_ids or non_striker_id not in batting_ids:
        raise ValueError("Opening batters must belong to the batting XI.")

    if bowler_id not in bowling_ids:
        raise ValueError("The bowler must belong to the bowling XI.")

    match["status"] = "live"
    match["state"] = "MATCH"
    match["interaction_stage"] = "variation"
    match["runs"] = 0
    match["wickets"] = 0
    match["overs_completed"] = 0
    match["balls"] = 0
    match["balls_in_over"] = 0
    match["dismissed_players"] = []
    match["batted_players"] = [striker_id, non_striker_id]
    match["extras"] = {}
    match["delivery_choices"] = {}
    match["previous_bowler"] = None
    match.setdefault("innings", 1)

    save_matches(matches)
    return match
