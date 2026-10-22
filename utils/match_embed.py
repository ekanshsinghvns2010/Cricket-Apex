
# utils/match_embed.py

import discord


def _get_name(match: dict, team_key: str) -> str:
    return str(
        match.get(f"{team_key}_name")
        or match.get(team_key)
        or team_key.replace("_", " ").title()
    )


def _player_name(match: dict, player_id: str, name_key: str) -> str:
    if match.get(name_key):
        return str(match[name_key])

    if not player_id:
        return "Not selected"

    team = str(match.get("batting_team", ""))
    xi = match.get(f"{team}_xi", [])

    for player in xi:
        if isinstance(player, dict):
            pid = str(player.get("id", player.get("player_id", "")))
            if pid == str(player_id):
                return str(
                    player.get("display_name")
                    or player.get("name")
                    or pid
                )

    return str(player_id)


def _format_overs(match: dict) -> str:
    overs = match.get("overs", 0)
    balls = int(match.get("balls", 0))

    # Supports a completed-over integer plus current legal balls.
    if isinstance(overs, str) and "." in overs:
        return overs

    return f"{int(overs)}.{balls}"


def build_match_embed(match: dict) -> discord.Embed:
    """Build the live match score embed from the saved match dictionary."""
    batting_team = str(match.get("batting_team", "team1"))
    bowling_team = str(match.get("bowling_team", "team2"))

    team1 = _get_name(match, "team1")
    team2 = _get_name(match, "team2")

    runs = int(match.get("runs", 0))
    wickets = int(match.get("wickets", 0))
    overs = _format_overs(match)

    status = str(match.get("status", "lobby")).replace("_", " ").title()

    embed = discord.Embed(
        title=f"🏏 {team1} vs {team2}",
        description=f"**Status:** {status}",
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name=f"{batting_team.replace('_', ' ').title()} Batting",
        value=f"**{runs}/{wickets}** in **{overs} overs**",
        inline=False,
    )

    striker_id = str(match.get("striker") or "")
    non_striker_id = str(match.get("non_striker") or "")
    bowler_id = str(match.get("current_bowler") or "")

    striker = _player_name(match, striker_id, "striker_name")
    non_striker = _player_name(match, non_striker_id, "non_striker_name")
    bowler = match.get("current_bowler_name") or bowler_id or "Not selected"

    embed.add_field(
        name="🏏 Batters",
        value=(
            f"**{striker}** — Striker\n"
            f"**{non_striker}** — Non-striker"
        ),
        inline=True,
    )

    embed.add_field(
        name="🎯 Bowler",
        value=str(bowler),
        inline=True,
    )

    target = match.get("target")
    if target is not None:
        required = max(0, int(target) - runs)
        embed.add_field(
            name="🎯 Target",
            value=f"{int(target)} (need {required} more)",
            inline=True,
        )

    team_scores = match.get("team_scores", {})
    if team_scores:
        score_lines = [
            f"**{_get_name(match, team)}:** {score}"
            for team, score in team_scores.items()
        ]
        embed.add_field(
            name="📋 Innings Scores",
            value="\n".join(score_lines),
            inline=False,
        )

    result = match.get("result")
    if result:
        embed.add_field(
            name="🏆 Result",
            value=str(result),
            inline=False,
        )

    embed.set_footer(
        text=f"Match ID: {match.get('match_id', 'Unknown')}"
    )

    return embed
