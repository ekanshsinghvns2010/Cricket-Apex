import discord

from utils.match_utils import get_match
from utils.toss import perform_toss


async def build_toss_embed(guild, match_id):

    winner, choice = perform_toss(match_id)

    match = get_match(match_id)

    team = "🔴 Red Team" if winner == "red" else "🔵 Blue Team"

    captain_id = (
        match["red_captain"]
        if winner == "red"
        else match["blue_captain"]
    )

    if captain_id:
        captain = guild.get_member(int(captain_id))

        captain_name = (
            captain.display_name
            if captain
            else "Unknown"
        )
    else:
        captain_name = "Bot Captain"

    decision = "🏏 BAT FIRST" if choice == "bat" else "🧤 BOWL FIRST"

    embed = discord.Embed(
        title="🪙 TOSS RESULT",
        color=0xFFD54F
    )

    embed.description = (
        f"{team} won the toss!\n\n"
        f"👑 Captain: **{captain_name}**\n\n"
        f"Decision: **{decision}**"
    )

    return embed