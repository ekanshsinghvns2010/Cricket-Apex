
# utils/scorecard.py

import discord


def player_id(player):
    if isinstance(player, dict):
        return str(player.get("id", ""))
    return str(player) if player is not None else ""


def player_name(player):
    if isinstance(player, dict):
        return player.get("display_name") or player.get("name", "Unknown")
    return str(player) if player is not None else "Unknown"


def overs_text(balls, balls_per_over=6):
    balls = max(0, int(balls))
    balls_per_over = max(1, int(balls_per_over))

    return f"{balls // balls_per_over}.{balls % balls_per_over}"


def build_scorecard_embed(match):
    batting_team = match.get("batting_team", "team1")
    bowling_team = match.get("bowling_team", "team2")

    batting_name = match.get(
        f"{batting_team}_name",
        batting_team.replace("_", " ").title(),
    )
    bowling_name = match.get(
        f"{bowling_team}_name",
        bowling_team.replace("_", " ").title(),
    )

    runs = int(match.get("runs", 0))
    wickets = int(match.get("wickets", 0))
    balls = int(match.get("balls", 0))
    balls_per_over = int(match.get("balls_per_over", 6))

    embed = discord.Embed(
        title="🏏 Cricket Apex Scorecard",
        description=f"**{batting_name}** vs **{bowling_name}**",
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="Team Score",
        value=f"**{runs}/{wickets}**",
        inline=True,
    )

    embed.add_field(
        name="Overs",
        value=overs_text(balls, balls_per_over),
        inline=True,
    )

    target = match.get("target")
    if target is not None:
        needed = max(0, int(target) - runs)
        embed.add_field(
            name="Target",
            value=f"{target} · {needed} runs remaining",
            inline=True,
        )

    striker = match.get("striker")
    non_striker = match.get("non_striker")

    batting_lines = []

    for player in (striker, non_striker):
        if player:
            batting_lines.append(f"🏏 {player_name(player)} — batting")

    if not batting_lines:
        batting_lines.append("No active batters selected.")

    embed.add_field(
        name="Batters at Crease",
        value="\n".join(batting_lines),
        inline=False,
    )

    bowler = match.get("current_bowler")

    embed.add_field(
        name="Current Bowler",
        value=player_name(bowler) if bowler else "Not selected",
        inline=False,
    )

    extras = match.get("extras", {})
    if isinstance(extras, dict) and extras:
        extra_lines = [
            f"{name.replace('_', ' ').title()}: {value}"
            for name, value in extras.items()
        ]
        embed.add_field(
            name="Extras",
            value="\n".join(extra_lines)[:1024],
            inline=False,
        )

    embed.add_field(
        name="Match Status",
        value=str(match.get("status", "unknown")).replace("_", " ").title(),
        inline=False,
    )

    return embed


def build_final_result_embed(match):
    embed = build_scorecard_embed(match)
    embed.title = "🏆 Cricket Apex — Match Result"

    winner = match.get("winner")
    if winner:
        winner_name = match.get(
            f"{winner}_name",
            str(winner).replace("_", " ").title(),
        )
        embed.add_field(
            name="Winner",
            value=f"🏆 {winner_name}",
            inline=False,
        )
    else:
        embed.add_field(
            name="Result",
            value="Match drawn or tied.",
            inline=False,
        )

    return embed
