import discord
import json

from utils.stadium import get_random_stadium
from utils.match_utils import create_match
from views.matches_lobby import MatchLobbyView
from utils.match_utils import set_lobby_message

def setup_play(bot):

    @bot.command(
        name="play",
        help="Create a multiplayer cricket match."
    )
    async def play(ctx, overs: int = None, match_format: str = None):

        # ----------------------------
        # Check arguments
        # ----------------------------

        if overs is None or match_format is None:
            await ctx.send(
                "❌ Usage: `g!play <overs> <3v3-11v11>`\n"
                "Example: `g!play 20 11v11`"
            )
            return

        if overs < 1 or overs > 20:
            await ctx.send("❌ Overs must be between **1** and **20**.")
            return

        valid_formats = [
            "3v3",
            "4v4",
            "5v5",
            "6v6",
            "7v7",
            "8v8",
            "9v9",
            "10v10",
            "11v11"
        ]

        if match_format not in valid_formats:
            await ctx.send(
                "❌ Invalid format.\n"
                "Choose between **3v3** and **11v11**."
            )
            return

        # ----------------------------
        # Check player profile
        # ----------------------------

        with open("users.json", "r") as f:
            users = json.load(f)

        user_id = str(ctx.author.id)

        if user_id not in users:
            await ctx.send(
                "❌ You haven't started your career.\n"
                "Use `g!debut` first."
            )
            return

        # ----------------------------
        # Stadium
        # ----------------------------

        stadium = get_random_stadium()

        team_size = int(match_format.split("v")[0])

        match_id = create_match(
            creator_id=ctx.author.id,
            guild_id=ctx.guild.id,
            overs=overs,
            match_format=match_format,
            team_size=team_size,
            stadium=stadium
        )

        # ----------------------------
        # Lobby Embed
        # ----------------------------

        embed = discord.Embed(
            title="🏏 MATCH LOBBY",
            color=0x00C853
        )

        embed.add_field(
            name="🏟 Stadium",
            value=stadium["name"],
            inline=True
        )

        embed.add_field(
            name="🌍 Country",
            value=stadium["country"],
            inline=True
        )

        embed.add_field(
            name="🌦 Weather",
            value=stadium["weather"],
            inline=True
        )

        embed.add_field(
            name="🏏 Pitch",
            value=stadium["pitch"],
            inline=True
        )

        embed.add_field(
            name="⏱ Match",
            value=f"{overs} Overs",
            inline=True
        )

        embed.add_field(
            name="👥 Format",
            value=match_format,
            inline=True
        )

        embed.add_field(
            name="🔴 Red Team",
            value=f"👑 {ctx.author.mention}\n(1/{team_size})",
            inline=False
        )

        embed.add_field(
            name="🔵 Blue Team",
            value=f"(0/{team_size})",
            inline=False
        )

        embed.add_field(
            name="🆔 Match ID",
            value=match_id,
            inline=True
        )

        embed.add_field(
            name="⏳ Status",
            value="Waiting for players...",
            inline=True
        )

        embed.set_footer(
            text="Join buttons will be available in the next update."
        )

        view = MatchLobbyView(match_id)

        message = await ctx.send(
            embed=embed,
            view=view
        )

        set_lobby_message(
            match_id,
            ctx.channel.id,
            message.id
        )