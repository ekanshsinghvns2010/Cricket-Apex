
import logging

from discord.ext import commands

from database import connect_db
from utils.stadium import get_random_stadium
from utils.match_utils import create_match, set_lobby_message
from views.matches_lobby import MatchLobbyView, build_lobby_embed

logger = logging.getLogger(__name__)


def setup_play(bot):

    @bot.command(
        name="play",
        help="Create a cricket match. Example: g!play 5 3v3",
    )
    async def play(ctx, overs: int = None, match_format: str = None):

        if ctx.guild is None:
            await ctx.send(
                "❌ Matches must be created inside a Discord server."
            )
            return

        if overs is None or match_format is None:
            await ctx.send(
                "🏏 **Cricket Apex Match Creator**\n"
                "Usage: `g!play <overs> <team format>`\n"
                "Example: `g!play 5 3v3`\n\n"
                "Formats: `1v1` through `11v11`\n"
                "Overs: `1` through `20`"
            )
            return

        if not 1 <= overs <= 20:
            await ctx.send(
                "❌ Overs must be between 1 and 20."
            )
            return

        match_format = match_format.lower().strip()

        valid_formats = {
            f"{size}v{size}" for size in range(1, 12)
        }

        if match_format not in valid_formats:
            await ctx.send(
                "❌ Invalid format. Choose a format from "
                "`1v1`, `2v2`, `3v3` ... `11v11`."
            )
            return

        # Confirm the creator has started their career.
        conn = connect_db()

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?",
                (str(ctx.author.id),),
            )
            profile = cursor.fetchone()
        except Exception:
            logger.exception(
                "Failed to check career profile for %s",
                ctx.author.id,
            )
            await ctx.send(
                "❌ I couldn't check your career profile. "
                "Please try again later."
            )
            return
        finally:
            conn.close()

        if profile is None:
            await ctx.send(
                "❌ You haven't started your career yet. "
                "Use `g!debut` first."
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
                stadium=stadium,
            )

            embed = await build_lobby_embed(
                ctx.guild,
                match_id,
            )

            embed.set_footer(
                text=(
                    f"Match ID: {match_id} • "
                    "Join a team to get ready"
                )
            )

            view = MatchLobbyView(match_id)

            message = await ctx.send(
                embed=embed,
                view=view,
            )

            saved = set_lobby_message(
                match_id,
                ctx.channel.id,
                message.id,
            )

            if not saved:
                logger.error(
                    "Could not save lobby message for match %s",
                    match_id,
                )
                await ctx.send(
                    "⚠️ The lobby was created, but its message "
                    "details could not be saved. Avoid running "
                    "`g!fill` for this lobby."
                )
                return

            logger.info(
                "Match %s created by %s: %s, %s overs",
                match_id,
                ctx.author.id,
                match_format,
                overs,
            )

        except Exception:
            logger.exception(
                "Failed to create match for user %s",
                ctx.author.id,
            )
            await ctx.send(
                "❌ Couldn't create the match. "
                "Check the hosting console logs."
            )
