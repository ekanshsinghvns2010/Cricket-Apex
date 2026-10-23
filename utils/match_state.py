
# utils/match_state.py

from utils.match_utils import load_matches, save_matches

VALID_TEAMS = {"red", "blue"}


def get_match(match_id):
    matches = load_matches()
    return matches.get(str(match_id))


def save_match(match_id, match):
    matches = load_matches()
    matches[str(match_id)] = match
    save_matches(matches)


def get_team_xi(match, team):
    if team not in VALID_TEAMS:
        raise ValueError(f"Invalid team: {team}")

    xi = match.get(f"{team}_xi", [])
    return xi if isinstance(xi, list) else []


def get_player_id(player):
    if isinstance(player, dict):
        value = player.get("id") or player.get("player_id")
        return str(value) if value is not None else ""

    return str(player) if player is not None else ""


def get_player_name(player):
    if isinstance(player, dict):
        return (
            player.get("display_name")
            or player.get("name")
            or "Unknown"
        )

    return str(player) if player is not None else "Unknown"


def validate_xi(match, team):
    xi = get_team_xi(match, team)

    if len(xi) != 11:
        return False, f"{team} must have exactly 11 players."

    ids = [get_player_id(player) for player in xi]

    if any(not player_id for player_id in ids):
        return False, "Every selected player must have a valid card ID."

    if len(set(ids)) != 11:
        return False, "A team cannot select duplicate player cards."

    return True, "XI valid."


def is_dismissed(match, player):
    dismissed = {
        get_player_id(item)
        for item in match.get("dismissed_players", [])
    }
    return get_player_id(player) in dismissed


def record_dismissal(match, player):
    player_id = get_player_id(player)

    if not player_id:
        raise ValueError("Cannot dismiss a player without a valid ID.")

    dismissed = match.setdefault("dismissed_players", [])

    if player_id not in {
        get_player_id(item) for item in dismissed
    }:
        dismissed.append(player_id)

    if get_player_id(match.get("striker")) == player_id:
        match["striker"] = None

    if get_player_id(match.get("non_striker")) == player_id:
        match["non_striker"] = None


def validate_opening_batters(match):
    striker = match.get("striker")
    non_striker = match.get("non_striker")

    if not striker or not non_striker:
        return False, "Both opening batters must be selected."

    striker_id = get_player_id(striker)
    non_striker_id = get_player_id(non_striker)

    if striker_id == non_striker_id:
        return False, "The opening batters must be different."

    batting_team = match.get("batting_team")

    if batting_team not in VALID_TEAMS:
        return False, "The batting team is invalid."

    xi_ids = {
        get_player_id(player)
        for player in get_team_xi(match, batting_team)
    }

    if striker_id not in xi_ids:
        return False, "The striker must belong to the batting XI."

    if non_striker_id not in xi_ids:
        return False, "The non-striker must belong to the batting XI."

    if is_dismissed(match, striker):
        return False, "A dismissed player cannot bat again."

    if is_dismissed(match, non_striker):
        return False, "A dismissed player cannot bat again."

    return True, "Opening batters valid."


def validate_bowler(match):
    bowler = match.get("current_bowler")

    if not bowler:
        return False, "Select a bowler before delivering a ball."

    bowling_team = match.get("bowling_team")

    if bowling_team not in VALID_TEAMS:
        return False, "The bowling team is invalid."

    xi_ids = {
        get_player_id(player)
        for player in get_team_xi(match, bowling_team)
    }

    if get_player_id(bowler) not in xi_ids:
        return False, "The bowler must belong to the bowling XI."

    return True, "Bowler valid."


def record_delivery(
    match,
    runs=0,
    wicket=False,
    legal=True,
    batter=None,
    extra_type=None,
):
    """Record a delivery. Runs include any extras."""

    if match.get("status") != "live":
        raise ValueError("The match is not live.")

    if not isinstance(runs, int) or runs < 0:
        raise ValueError("Runs must be a non-negative integer.")

    match["runs"] = int(match.get("runs", 0)) + runs

    if wicket:
        batter = batter or match.get("striker")

        if batter is None:
            raise ValueError("A dismissed batter must be identified.")

        record_dismissal(match, batter)
        match["wickets"] = int(match.get("wickets", 0)) + 1

    if legal:
        match["balls"] = int(match.get("balls", 0)) + 1

    balls_per_over = int(match.get("balls_per_over", 6))

    if balls_per_over <= 0:
        raise ValueError("balls_per_over must be positive.")

    total_balls = int(match.get("balls", 0))
    match["overs"] = total_balls // balls_per_over
    match["balls_in_over"] = total_balls % balls_per_over

    extras = match.setdefault("extras", {})

    if extra_type:
        extras[extra_type] = int(extras.get(extra_type, 0)) + runs

    max_overs = int(match.get("overs", match.get("max_overs", 20)))
    batting_team = match.get("batting_team", "red")
    max_wickets = max(0, len(get_team_xi(match, batting_team)) - 1)

    target = match.get("target")
    target_reached = (
        target is not None
        and match["runs"] >= int(target)
    )

    innings_over = (
        match["wickets"] >= max_wickets
        or match["overs"] >= max_overs
        or target_reached
    )

    over_complete = (
        legal
        and match["balls_in_over"] == 0
        and total_balls > 0
    )

    return {
        "runs": match["runs"],
        "wickets": match["wickets"],
        "overs": match["overs"],
        "balls_in_over": match["balls_in_over"],
        "over_complete": over_complete,
        "innings_over": innings_over,
        "target_reached": target_reached,
    }


def prepare_second_innings(match):
    """Switch teams and reset innings-specific state."""

    first_innings_runs = int(match.get("runs", 0))

    batting_team = match.get("batting_team")
    bowling_team = match.get("bowling_team")

    if batting_team not in VALID_TEAMS or bowling_team not in VALID_TEAMS:
        raise ValueError("Cannot start the chase: teams are not configured.")

    match["first_innings_runs"] = first_innings_runs
    match["target"] = first_innings_runs + 1

    match["batting_team"] = bowling_team
    match["bowling_team"] = batting_team

    match["runs"] = 0
    match["wickets"] = 0
    match["overs"] = 0
    match["overs_completed"] = 0
    match["balls"] = 0
    match["balls_in_over"] = 0
    match["extras"] = {}

    match["dismissed_players"] = []
    match["batted_players"] = []

    match["striker"] = None
    match["non_striker"] = None
    match["current_bowler"] = None
    match["previous_bowler"] = None

    match["delivery_choices"] = {}
    match["dismissed_slot"] = None
    match["interaction_stage"] = "opening_selection"
    match["status"] = "opening_selection"
    match["innings"] = 2

    return match
