
# utils/match_flow.py

from utils.match_utils import load_matches, save_matches


VALID_TEAMS = ("team1", "team2")


def get_match(match_id):
    matches = load_matches()
    return matches.get(str(match_id))


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

    match["status"] = "selecting"
    match["xi_confirmed"] = {"team1": False, "team2": False}
    match["card_selections"] = {"team1": {}, "team2": {}}
    match["team1_xi"] = []
    match["team2_xi"] = []
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
                f"{team} must have exactly 11 unique player cards."
            )

        player_ids = [
            str(player.get("id", ""))
            for player in xi
            if isinstance(player, dict)
        ]

        if len(player_ids) != 11 or len(set(player_ids)) != 11:
            raise ValueError(
                f"{team} has missing or duplicate player IDs."
            )

    match["status"] = "xi_confirmation"
    match["xi_confirmed"] = {"team1": False, "team2": False}
    match["interaction_stage"] = "xi_confirmation"

    save_matches(matches)
    return match


def start_opening_selection(match_id):
    matches = load_matches()
    key = str(match_id)

    if key not in matches:
        raise ValueError(f"Match {key} was not found.")

    match = matches[key]

    if match.get("status") not in {"xi_confirmation", "ready_to_play"}:
        raise ValueError("Both XIs must be confirmed first.")

    confirmed = match.get("xi_confirmed", {})

    if not all(confirmed.get(team, False) for team in VALID_TEAMS):
        raise ValueError("Both captains must confirm their XIs.")

    match["status"] = "opening_selection"
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

    striker = match.get("striker")
    non_striker = match.get("non_striker")
    bowler = match.get("current_bowler")

    if not striker or not non_striker or not bowler:
        raise ValueError(
            "Select the opening striker, non-striker, and bowler first."
        )

    striker_id = str(striker.get("id", ""))
    non_striker_id = str(non_striker.get("id", ""))

    if not striker_id or not non_striker_id or striker_id == non_striker_id:
        raise ValueError("Opening batters must be distinct valid players.")

    batting_team = match.get("batting_team")
    bowling_team = match.get("bowling_team")

    batting_ids = {
        str(p.get("id", ""))
        for p in match.get(f"{batting_team}_xi", [])
        if isinstance(p, dict)
    }
    bowling_ids = {
        str(p.get("id", ""))
        for p in match.get(f"{bowling_team}_xi", [])
        if isinstance(p, dict)
    }

    if striker_id not in batting_ids or non_striker_id not in batting_ids:
        raise ValueError("Opening batters must belong to the batting XI.")

    if str(bowler.get("id", "")) not in bowling_ids:
        raise ValueError("The bowler must belong to the bowling XI.")

    match["status"] = "live"
    match["interaction_stage"] = "variation"
    match.setdefault("runs", 0)
    match.setdefault("wickets", 0)
    match.setdefault("overs", 0)
    match.setdefault("balls", 0)
    match.setdefault("balls_in_over", 0)
    match.setdefault("dismissed_players", [])
    match.setdefault("extras", {})
    match.setdefault("innings", 1)

    save_matches(matches)
    return match
