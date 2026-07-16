import discord
import traceback
from datetime import datetime

# ===========================
# CONFIG
# ===========================

LOG_CHANNEL_ID = YOUR_LOG_CHANNEL_ID


# ===========================
# INTERNAL
# ===========================

async def _send(bot, embed):
    """
    Sends an embed to the configured log channel.
    """

    channel = bot.get_channel(LOG_CHANNEL_ID)

    if channel is None:
        return

    try:
        await channel.send(embed=embed)
    except Exception:
        pass


# ===========================
# ACTION LOG
# ===========================

async def log_action(
    bot,
    title,
    description,
    color=discord.Color.blue(),
    user=None,
    guild=None,
    channel=None,
):
    """
    Generic action logger.
    """

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow(),
    )

    if user is not None:
        embed.add_field(
            name="User",
            value=f"{user} (`{user.id}`)",
            inline=False,
        )

    if guild is not None:
        embed.add_field(
            name="Server",
            value=f"{guild.name} (`{guild.id}`)",
            inline=False,
        )

    if channel is not None:
        embed.add_field(
            name="Channel",
            value=channel.mention,
            inline=False,
        )

    await _send(bot, embed)

# ===========================
# ERROR LOG
# ===========================

async def log_error(
    bot,
    error,
    user=None,
    guild=None,
    channel=None,
    command=None,
):
    """
    Logs any exception with traceback.
    """

    tb = "".join(
        traceback.format_exception(
            type(error),
            error,
            error.__traceback__,
        )
    )

    if len(tb) > 3900:
        tb = tb[:3900] + "\n..."

    embed = discord.Embed(
        title="❌ Bot Error",
        color=discord.Color.red(),
        timestamp=datetime.utcnow(),
    )

    if command is not None:
        embed.add_field(
            name="Command",
            value=command,
            inline=False,
        )

    if user is not None:
        embed.add_field(
            name="User",
            value=f"{user} (`{user.id}`)",
            inline=False,
        )

    if guild is not None:
        embed.add_field(
            name="Server",
            value=f"{guild.name} (`{guild.id}`)",
            inline=False,
        )

    if channel is not None:
        embed.add_field(
            name="Channel",
            value=channel.mention,
            inline=False,
        )

    embed.add_field(
        name="Traceback",
        value=f"```py\n{tb}\n```",
        inline=False,
    )

    await _send(bot, embed)