import discord

from utils.match_utils import get_match


def build_match_embed(match_id):
    match = get_match(match_id)

    if match is None:
        raise ValueError(f"Match {match_id} not found")

    batting_team = match.get("batting_team") or "red"
    bowling_team = match.get("bowling_team") or "blue"

    batting_name = (
        "🔴 Red Team" if batting_team == "red"
        else "🔵 Blue Team"
    )
    bowling_name = (
        "🔴 Red Team" if bowling_team == "red"
        else "🔵 Blue Team"
    )

    runs = int(match.get("runs", 0))
    wickets = int(match.get("wickets", 0))
    overs_completed = int(match.get("overs_completed", 0))
    balls = int(match.get("balls", 0))
    innings = int(match.get("innings", 1))
    total_overs = int(match.get("overs", 1))

    embed = discord.Embed(
        title="🏏 CRICKET APEX • MATCH STARTED",
        description=(
            f"**Match ID:** `{match_id}`\n"
            f"**Stadium:** {match.get('stadium', 'Unknown')}\n\n"
            f"🏏 **Batting:** {batting_name}\n"
            f"🎯 **Bowling:** {bowling_name}"
        ),
        color=0x00C853
    )

    embed.add_field(
        name="📊 Score",
        value=f"**{runs}/{wickets}**",
        inline=True
    )

    embed.add_field(
        name="⏱️ Overs",
        value=f"{overs_completed}.{balls}/{total_overs}",
        inline=True
    )

    embed.add_field(
        name="🏆 Innings",
        value=str(innings),
        inline=True
    )

    embed.add_field(
        name="Match Status",
        value="🟢 LIVE",
        inline=False
    )

    embed.set_footer(
        text="Cricket Apex • Match initialized"
    )

    return embed