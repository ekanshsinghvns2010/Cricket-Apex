
# utils/innings_flow.py

import discord

from utils.match_utils import load_matches, save_matches
from utils.match_state import (
    get_player_id,
    get_player_name,
    validate_xi,
    validate_opening_batters,
    validate_bowler,
)


def get_match_or_raise(match_id):
    matches = load_matches()
    match = matches.get(str(match_id))

    if match is None:
        raise ValueError(f"Match {match_id} was not found.")

    return matches, match


def save_current_match(match_id, match):
    matches = load_matches()
    matches[str(match_id)] = match
    save_matches(matches)


def both_xis_confirmed(match):
    confirmed = match.get("xi_confirmed", {})

    return (
        confirmed.get("team1", False)
        and confirmed.get("team2", False)
    )


def validate_match_setup(match):
    if not both_xis_confirmed(match):
        return False, "Both captains must confirm their playing XIs."

    for team in ("team1", "team2"):
        valid, reason = validate_xi(match, team)
        if not valid:
            return False, reason

    return True, "Match setup valid."


def validate_innings_start(match):
    valid, reason = validate_match_setup(match)
    if not valid:
        return False, reason

    valid, reason = validate_opening_batters(match)
    if not valid:
        return False, reason

    valid, reason = validate_bowler(match)
    if not valid:
        return False, reason

    return True, "Ready to start."


def score_embed(match):
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
    overs = int(match.get("overs", 0))
    balls = int(match.get("balls_in_over", 0))

    embed = discord.Embed(
        title="🏏 Cricket Apex — Live Score",
        description=f"**{batting_name}** vs **{bowling_name}**",
        color=discord.Color.green(),
    )

    embed.add_field(
        name="Score",
        value=f"**{runs}/{wickets}**",
        inline=True,
    )
    embed.add_field(
        name="Overs",
        value=f"{overs}.{balls}",
        inline=True,
    )
    embed.add_field(
        name="Striker",
        value=get_player_name(match.get("striker")),
        inline=True,
    )
    embed.add_field(
        name="Non-striker",
        value=get_player_name(match.get("non_striker")),
        inline=True,
    )
    embed.add_field(
        name="Bowler",
        value=get_player_name(match.get("current_bowler")),
        inline=True,
    )

    target = match.get("target")
    if target is not None:
        embed.add_field(
            name="Target",
            value=str(target),
            inline=True,
        )

    return embed


async def announce_next_stage(channel, match_id):
    """
    Announce which selection is needed next.
    Call this after updating and saving the match state.
    """
    matches, match = get_match_or_raise(match_id)
    status = match.get("status")

    if status == "bowler_selection":
        from views.over_selection import send_next_bowler_selection

        await send_next_bowler_selection(channel, match_id)
        return

    if status == "opening_selection":
        from views.opening_selection import send_opening_selection

        await send_opening_selection(channel, match_id)
        return

    if status == "live":
        await channel.send(
            embed=score_embed(match),
            content="🏏 Match is live. Continue with your MatchView controls.",
        )
        return

    if status in {"innings_break", "completed"}:
        await channel.send(
            embed=discord.Embed(
                title="Match Status",
                description=f"Current state: **{status}**",
                color=discord.Color.blurple(),
            )
        )
        return

    await channel.send(f"Match state: `{status}`")


async def begin_live_innings(interaction, match_id):
    """
    Validate selections before changing the match to live.
    This function does not create MatchView because its constructor
    and control API depend on your existing implementation.
    """
    matches, match = get_match_or_raise(match_id)

    if match.get("status") not in {
        "opening_selection",
        "ready_to_play",
    }:
        await interaction.response.send_message(
            "The match is not ready to start an innings.",
            ephemeral=True,
        )
        return False

    valid, reason = validate_innings_start(match)

    if not valid:
        await interaction.response.send_message(
            reason,
            ephemeral=True,
        )
        return False

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

    await interaction.response.send_message(
        "✅ Innings setup validated. Your existing MatchView still needs "
        "to be attached here to enable ball-by-ball controls.",
        ephemeral=True,
    )

    return True
