
# utils/innings_result.py

from utils.match_utils import load_matches, save_matches


def team_name(match, team):
    return match.get(f"{team}_name", team.title())


def finish_match(match):
    """Transition innings one to two, or calculate the final result."""
    batting_team = match.get("batting_team", "red")
    bowling_team = match.get("bowling_team", "blue")

    innings = int(match.get("innings", 1))
    runs = int(match.get("runs", 0))
    wickets = int(match.get("wickets", 0))

    scores = match.setdefault("team_scores", {})

    if innings == 1:
        scores[batting_team] = runs
        match["first_innings_team"] = batting_team
        match["target"] = runs + 1

        match["batting_team"] = bowling_team
        match["bowling_team"] = batting_team
        match["innings"] = 2

        match["runs"] = 0
        match["wickets"] = 0
        match["overs_completed"] = 0
        match["balls_in_over"] = 0
        match["balls"] = 0

        match["striker"] = None
        match["non_striker"] = None
        match["current_bowler"] = None
        match["previous_bowler"] = None

        match["dismissed_players"] = []
        match["batted_players"] = []
        match["dismissed_slot"] = None
        match["delivery_choices"] = {}
        match["extras"] = {}

        match["status"] = "opening_selection"
        match["interaction_stage"] = "opening_selection"

        return {
            "match_over": False,
            "innings_break": True,
            "message": (
                f"First innings complete! Target: {runs + 1}. "
                "Choose the second-innings opening batters and bowler."
            ),
        }

    scores[batting_team] = runs

    first_team = match.get("first_innings_team")
    first_score = int(scores.get(first_team, 0))
    target = int(match.get("target", first_score + 1))

    if runs >= target:
        winner = batting_team
        wickets_left = max(0, 10 - wickets)
        result = (
            f"{team_name(match, winner)} won by "
            f"{wickets_left} wicket(s)!"
        )
    elif runs < first_score:
        winner = bowling_team
        margin = first_score - runs
        result = (
            f"{team_name(match, winner)} won by "
            f"{margin} run(s)!"
        )
    else:
        winner = None
        result = "The match ended in a tie!"

    match["winner"] = winner
    match["result"] = result
    match["status"] = "completed"
    match["interaction_stage"] = "completed"

    return {
        "match_over": True,
        "innings_break": False,
        "winner": winner,
        "result": result,
        "message": result,
    }


def complete_innings(match_id):
    """Complete the current innings once and save its state."""
    matches = load_matches()
    key = str(match_id)

    if key not in matches:
        raise ValueError(f"Match {key} was not found.")

    match = matches[key]

    if match.get("status") != "innings_break":
        raise ValueError(
            "Set the match status to 'innings_break' before completing it."
        )

    if match.get("innings_result_processed"):
        raise ValueError("This innings has already been processed.")

    match["innings_result_processed"] = True
    outcome = finish_match(match)

    # Allow the second innings to be completed separately.
    if outcome["innings_break"]:
        match["innings_result_processed"] = False

    save_matches(matches)
    return match, outcome


def build_result_embed(match):
    import discord

    status = match.get("status")

    if status == "completed":
        embed = discord.Embed(
            title="🏆 Match Result",
            description=match.get("result", "Match completed."),
            color=discord.Color.gold(),
        )
    else:
        embed = discord.Embed(
            title="🏏 Innings Break",
            description=(
                f"Target for the second innings: "
                f"**{match.get('target', 0)} runs**"
            ),
            color=discord.Color.blurple(),
        )

    for team, score in match.get("team_scores", {}).items():
        embed.add_field(
            name=team_name(match, team),
            value=f"{score} runs",
            inline=True,
        )

    return embed
