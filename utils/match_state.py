
# utils/match_state.py

from utils.match_utils import load_matches, save_matches


VALID_TEAMS = {"team1", "team2"}


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
        value = player.get("id")
        return str(value) if value is not None else ""

    return str(player) if player is not None else ""


def get_player_name(player):
    if isinstance(player, dict):
        return player.get("display_name") or player.get("name", "Unknown")

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
    dismissed = match.get("dismissed_players", [])
    dismissed_ids = {str(value) for value in dismissed}

    return get_player_id(player) in dismissed_ids


def record_dismissal(match, player):
    player_id = get_player_id(player)

    if not player_id:
        raise ValueError("Cannot dismiss a player without a valid ID.")

    dismissed = match.setdefault("dismissed_players", [])

    if player_id not in {str(value) for value in dismissed}:
        dismissed.append(player_id)

    # Clear a dismissed batter from the active batting positions.
    if get_player_id(match.get("striker")) == player_id:
        match["striker"] = None

    if get_player_id(match.get("non_striker")) == player_id:
        match["non_striker"] = None


def validate_opening_batters(match):
    striker = match.get("striker")
    non_striker = match.get("non_striker")

    if not striker or not non_striker:
        return False, "Both opening batters must be selected."

    if get_player_id(striker) == get_player_id(non_striker):
        return False, "The opening batters must be different."

    batting_team = match.get("batting_team")
    xi = get_team_xi(match, batting_team)

    xi_ids = {get_player_id(player) for player in xi}

    if get_player_id(striker) not in xi_ids:
        return False, "The striker must belong to the confirmed XI."

    if get_player_id(non_striker) not in xi_ids:
        return False, "The non-striker must belong to the confirmed XI."

    if is_dismissed(match, striker) or is_dismissed(match, non_striker):
        return False, "A dismissed player cannot bat again."

    return True, "Opening batters valid."


def validate_bowler(match):
    bowler = match.get("current_bowler")

    if not bowler:
        return False, "Select a bowler before delivering a ball."

    bowling_team = match.get("bowling_team")
    xi = get_team_xi(match, bowling_team)

    if get_player_id(bowler) not in {
        get_player_id(player) for player in xi
    }:
        return False, "The bowler must belong to the bowling team's XI."

    return True, "Bowler valid."


def record_delivery(
    match,
    runs=0,
    wicket=False,
    legal=True,
    batter=None,
    extra_type=None,
):
    """
    Record one delivery.

    runs: runs added to the team score, including extras.
    wicket: whether a dismissal occurred.
    legal: whether this delivery counts as a legal ball.
    batter: player dismissed, when applicable.
    extra_type: optional extra label, e.g. 'wide' or 'no_ball'.

    The caller is responsible for determining dismissal type and
    whether the delivery is legal according to the match engine.
    """
    if match.get("status") != "live":
        raise ValueError("Cannot record a delivery when the match is not live.")

    if not isinstance(runs, int) or runs < 0:
        raise ValueError("Runs must be a non-negative integer.")

    match["runs"] = int(match.get("runs", 0)) + runs

    if wicket:
        if batter is None:
            batter = match.get("striker")

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

    match.setdefault("extras", {})
    if extra_type:
        match["extras"][extra_type] = (
            int(match["extras"].get(extra_type, 0)) + runs
        )

    max_overs = int(match.get("max_overs", 20))
    max_wickets = max(0, len(get_team_xi(
        match, match.get("batting_team", "team1")
    )) - 1)

    target = match.get("target")
    target_reached = (
        target is not None and match["runs"] >= int(target)
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
    """
    Reset innings-specific score fields and set the chase target.
    Call after the first innings has ended.
    """
    first_innings_runs = int(match.get("runs", 0))

    match["target"] = first_innings_runs + 1

    batting_team = match.get("batting_team")
    bowling_team = match.get("bowling_team")

    match["batting_team"] = bowling_team
    match["bowling_team"] = batting_team

    match["runs"] = 0
    match["wickets"] = 0
    match["overs"] = 0
    match["balls"] = 0
    match["balls_in_over"] = 0
    match["extras"] = {}
    match["dismissed_players"] = []
    match["striker"] = None
    match["non_striker"] = None
    match["current_bowler"] = None
    match["previous_bowler"] = None
    match["interaction_stage"] = "opening_selection"
    match["status"] = "opening_selection"
    match["innings"] = 2

    return match
