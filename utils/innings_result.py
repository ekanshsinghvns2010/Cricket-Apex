
# utils/innings_result.py

from utils.match_utils import load_matches, save_matches


def get_team_name(match, team):
    return match.get(
        f"{team}_name",
        team.replace("_", " ").title(),
    )


def finish_match(match):
    """Determine and save the result after the chase ends."""
    team1 = "team1"
    team2 = "team2"

    batting_team = match.get("batting_team")
    bowling_team = match.get("bowling_team")

    team_scores = match.setdefault("team_scores", {})
    current_runs = int(match.get("runs", 0))

    innings = int(match.get("innings", 1))

    if innings == 1:
        team_scores[batting_team] = current_runs
        match["first_innings_team"] = batting_team
        match["status"] = "innings_break"
        match["interaction_stage"] = "innings_break"

        match["target"] = current_runs + 1
        match["batting_team"] = bowling_team
        match["bowling_team"] = batting_team

        match["innings"] = 2
        match["runs"] = 0
        match["wickets"] = 0
        match["overs"] = 0
        match["balls"] = 0
        match["balls_in_over"] = 0
        match["striker"] = None
        match["non_striker"] = None
        match["current_bowler"] = None
        match["previous_bowler"] = None
        match["dismissed_players"] = []
        match["batting_stats"] = {}
        match["bowling_stats"] = {}
        match["extras"] = {}

        return {
            "match_over": False,
            "innings_break": True,
            "message": (
                f"First innings complete. Target: {match['target']} runs. "
                "Select the second-innings batters and bowler."
            ),
        }

    team_scores[batting_team] = current_runs

    first_team = match.get("first_innings_team")
    first_score = int(team_scores.get(first_team, 0))

    second_team = batting_team
    second_score = current_runs

    if second_score > first_score:
        winner = second_team
        wickets_left = max(0, 10 - int(match.get("wickets", 0)))
        result = (
            f"{get_team_name(match, winner)} won by "
            f"{wickets_left} wicket(s)."
        )
    elif second_score < first_score:
        winner = bowling_team
        run_margin = first_score - second_score
        result = (
            f"{get_team_name(match, winner)} won by "
            f"{run_margin} run(s)."
        )
    else:
        winner = None
        result = "The match ended in a tie."

    match["winner"] = winner
    match["result"] = result
    match["status"] = "completed"
    match["interaction_stage"] = "completed"

    return {
        "match_over": True,
        "innings_break": False,
        "winner": winner,
        "result": result,
    }


def complete_innings(match_id):
    """
    Load the match, calculate the innings transition or final result,
    and persist the updated state.
    """
    matches = load_matches()
    key = str(match_id)

    if key not in matches:
        raise ValueError(f"Match {key} was not found.")

    match = matches[key]

    if match.get("status") not in {"live", "innings_break"}:
        raise ValueError("The match is not ready to complete an innings.")

    outcome = finish_match(match)

    save_matches(matches)

    return match, outcome


def build_result_embed(match):
    import discord

    status = match.get("status")

    if status == "completed":
        title = "🏆 Match Result"
        color = discord.Color.gold()
        description = match.get("result", "Match completed.")
    elif status == "innings_break":
        title = "🏏 Innings Break"
        color = discord.Color.blurple()
        description = (
            f"Target for the second innings: **{match.get('target', 0)}**"
        )
    else:
        title = "🏏 Innings Status"
        color = discord.Color.green()
        description = f"Current status: {status}"

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
    )

    for team, score in match.get("team_scores", {}).items():
        embed.add_field(
            name=get_team_name(match, team),
            value=f"{score} runs",
            inline=True,
        )

    return embed
