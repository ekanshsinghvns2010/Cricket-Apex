
# utils/match_validation.py

import json
import sqlite3

from database import connect_db


VALID_TEAMS = {"team1", "team2"}


def normalize_id(value):
    return str(value) if value is not None else ""


def get_player_id(player):
    if isinstance(player, dict):
        return normalize_id(player.get("id"))
    return normalize_id(player)


def get_user_cards(user_id):
    """Return the database player records owned by a user."""
    conn = connect_db()

    try:
        row = conn.execute(
            "SELECT cards FROM users WHERE user_id = ?",
            (normalize_id(user_id),),
        ).fetchone()

        if row is None:
            return []

        try:
            card_ids = json.loads(row["cards"] or "[]")
        except (TypeError, json.JSONDecodeError):
            return []

        if not isinstance(card_ids, list):
            return []

        if not card_ids:
            return []

        placeholders = ",".join("?" for _ in card_ids)

        players = conn.execute(
            f"SELECT * FROM players WHERE id IN ({placeholders})",
            tuple(normalize_id(card_id) for card_id in card_ids),
        ).fetchall()

        return [dict(player) for player in players]

    finally:
        conn.close()


def validate_card_ownership(user_id, selected_player_ids):
    """Check that every selected card belongs to the selecting user."""
    owned_ids = {
        get_player_id(player)
        for player in get_user_cards(user_id)
    }

    selected_ids = [normalize_id(value) for value in selected_player_ids]

    if not selected_ids:
        return False, "Select at least one player card."

    if any(not value for value in selected_ids):
        return False, "One or more selected player IDs are invalid."

    if len(selected_ids) != len(set(selected_ids)):
        return False, "You cannot select the same card more than once."

    missing = [value for value in selected_ids if value not in owned_ids]

    if missing:
        return False, "You can only select cards you own."

    return True, "Card ownership verified."


def validate_team_xi(xi):
    """A valid XI contains exactly 11 unique player cards."""
    if not isinstance(xi, list) or len(xi) != 11:
        return False, "A playing XI must contain exactly 11 players."

    ids = [get_player_id(player) for player in xi]

    if any(not value for value in ids):
        return False, "Every player must have a valid card ID."

    if len(set(ids)) != 11:
        return False, "An XI cannot contain duplicate cards."

    return True, "Playing XI valid."


def validate_team_captain(match, team, user_id):
    if team not in VALID_TEAMS:
        return False, "Invalid team."

    captain_id = normalize_id(match.get(f"{team}_captain"))

    if not captain_id:
        return False, "This team has no assigned captain."

    if captain_id != normalize_id(user_id):
        return False, "Only this team's captain can perform that action."

    return True, "Captain verified."


def validate_player_in_xi(match, team, player_id):
    if team not in VALID_TEAMS:
        return False, "Invalid team."

    xi = match.get(f"{team}_xi", [])

    if not isinstance(xi, list):
        return False, "The team's XI is invalid."

    selected_id = normalize_id(player_id)

    if selected_id not in {get_player_id(player) for player in xi}:
        return False, "That player is not in the team's XI."

    return True, "Player belongs to the XI."


def validate_distinct_batters(striker, non_striker):
    striker_id = get_player_id(striker)
    non_striker_id = get_player_id(non_striker)

    if not striker_id or not non_striker_id:
        return False, "Select both opening batters."

    if striker_id == non_striker_id:
        return False, "The two batters must be different players."

    return True, "Batters verified."


def validate_not_dismissed(match, player):
    player_id = get_player_id(player)

    dismissed = {
        normalize_id(value)
        for value in match.get("dismissed_players", [])
    }

    if player_id in dismissed:
        return False, "This batter has already been dismissed."

    return True, "Batter is eligible."


def validate_opposing_teams(match):
    batting_team = match.get("batting_team")
    bowling_team = match.get("bowling_team")

    if batting_team not in VALID_TEAMS or bowling_team not in VALID_TEAMS:
        return False, "Batting and bowling teams must be assigned."

    if batting_team == bowling_team:
        return False, "A team cannot bat against itself."

    return True, "Teams verified."
