
# utils/over_manager.py

from utils.match_utils import load_matches, save_matches


def get_match(match_id: str):
    matches = load_matches()
    return matches, matches.get(str(match_id))


def legal_balls_per_over(match: dict) -> int:
    """Default to six legal deliveries per over."""
    return int(match.get("legal_balls_per_over", 6))


def get_bowling_xi(match: dict) -> list:
    team = str(match.get("bowling_team", ""))
    xi = match.get(f"{team}_xi", [])
    return xi if isinstance(xi, list) else []


def get_player_id(player) -> str:
    if isinstance(player, dict):
        return str(player.get("id", player.get("player_id", "")))
    return str(player)


def get_player_name(player) -> str:
    if isinstance(player, dict):
        return str(
            player.get("display_name")
            or player.get("name")
            or player.get("id")
            or "Unknown"
        )
    return str(player)


def legal_balls_bowled(match: dict) -> int:
    """
    Count legal balls in the current innings.

    `balls` is treated as legal balls within the current over.
    `overs` may be stored as an integer or a cricket-style string such as 3.4.
    """
    balls = int(match.get("balls", 0))
    overs = match.get("overs", 0)

    if isinstance(overs, str) and "." in overs:
        whole_overs, partial_balls = overs.split(".", 1)
        return int(whole_overs) * legal_balls_per_over(match) + int(partial_balls)

    # Numeric overs can be stored as a completed-over count.
    return int(overs) * legal_balls_per_over(match) + balls


def over_is_complete(match: dict) -> bool:
    return int(match.get("balls", 0)) >= legal_balls_per_over(match)


def available_bowlers(match: dict) -> list:
    """Return eligible bowlers, excluding the previous over's bowler."""
    xi = get_bowling_xi(match)
    current_bowler = str(match.get("current_bowler", ""))
    previous_bowler = str(match.get("previous_bowler", ""))

    # During a bowler-selection stage, current_bowler may be the bowler
    # who just completed the previous over.
    excluded = previous_bowler or current_bowler

    return [
        player for player in xi
        if get_player_id(player)
        and get_player_id(player) != excluded
    ]


def start_bowler_selection(match_id: str) -> dict:
    """
    Switch the match to bowler selection after a completed over.
    Call this only after the delivery engine confirms the over is complete.
    """
    matches, match = get_match(match_id)

    if not match:
        return {"ok": False, "error": "Match not found."}

    if match.get("status") != "live":
        return {"ok": False, "error": "Match is not live."}

    if not over_is_complete(match):
        return {"ok": False, "error": "The over is not complete."}

    old_bowler = str(match.get("current_bowler", ""))
    match["previous_bowler"] = old_bowler
    match["current_bowler"] = None
    match["balls"] = 0
    match["overs"] = int(match.get("overs", 0)) + 1
    match["status"] = "bowler_selection"
    match["interaction_stage"] = "bowler_selection"

    # Clear the completed-over ball count before the next over starts.
    save_matches(matches)

    return {
        "ok": True,
        "match": match,
        "available_bowlers": available_bowlers(match),
    }


def choose_bowler(match_id: str, bowler_id: str) -> dict:
    matches, match = get_match(match_id)

    if not match:
        return {"ok": False, "error": "Match not found."}

    if match.get("status") != "bowler_selection":
        return {"ok": False, "error": "The match is not waiting for a bowler."}

    selected_id = str(bowler_id)
    candidates = available_bowlers(match)

    selected = next(
        (
            player for player in candidates
            if get_player_id(player) == selected_id
        ),
        None,
    )

    if selected is None:
        return {
            "ok": False,
            "error": "Choose a player from the bowling XI other than the previous bowler.",
        }

    match["current_bowler"] = selected_id
    match["current_bowler_name"] = get_player_name(selected)
    match["status"] = "live"
    match["interaction_stage"] = "variation"

    save_matches(matches)

    return {
        "ok": True,
        "bowler_id": selected_id,
        "bowler_name": get_player_name(selected),
        "match": match,
    }
