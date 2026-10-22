
import logging

import discord
from discord.ext import commands

from database import connect_db
from utils.stadium import get_random_stadium
from utils.match_utils import create_match, set_lobby_message
from views.matches_lobby import MatchLobbyView, build_lobby_embed

logger = logging.getLogger(__name__)


def setup_play(bot):

    @bot.command(
        name="play",
        help="Create a cricket match. Example: g!play 5 3v3"
    )
    async def play(ctx, overs: int = None, match_format: str = None):

        if overs is None or match_format is None:
            await ctx.send(
                "❌ Usage: `g!play <overs> <team format>`\n"
                "Example: `g!play 5 3v3`"
            )
            return

        if not 1 <= overs <= 20:
            await ctx.send("❌ Overs must be between 1 and 20.")
            return

        match_format = match_format.lower()
        valid_formats = {
            "3v3", "4v4", "5v5", "6v6", "7v7",
            "8v8", "9v9", "10v10", "11v11"
        }

        if match_format not in valid_formats:
            await ctx.send(
                "❌ Invalid format. Choose a format from `3v3` to `11v11`."
            )
            return

        if ctx.guild is None:
            await ctx.send("❌ Create matches inside a Discord server.")
            return

        # Check career profile in the same database used by g!debut.
        conn = connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?",
                (str(ctx.author.id),)
            )
            profile = cursor.fetchone()
        finally:
            conn.close()

        if profile is None:
            await ctx.send(
                "❌ You haven't started your career. Use `g!debut` first."
            )
            return

        try:
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

            embed = await build_lobby_embed(ctx.guild, match_id)
            view = MatchLobbyView(match_id)

            message = await ctx.send(embed=embed, view=view)

            set_lobby_message(
                match_id,
                ctx.channel.id,
                message.id
            )

        except Exception:
            logger.exception("Failed to create match for user %s", ctx.author.id)
            await ctx.send(
                "❌ Couldn't create the match. Please check the hosting console logs."
            )


