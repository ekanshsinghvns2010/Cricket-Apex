
import os
import time
import json

import discord
from discord.ext import commands
from dotenv import load_dotenv

import database
from database import create_tables
from keep_alive import keep_alive
from backupdb import setup_backupdb
from utils.logger import log_error

from commands.debut import setup_debut
from commands.profile import setup_profile
from commands.play import setup_play
from commands.dev import setup_dev
from commands.ping import setup_ping
from commands.help import setup_help
from commands.balance import setup_balance
from commands.shop import setup_shop
from commands.crate import setup_crate
from commands.addplayer import setup_addplayer
from commands.buy import setup_buy
from commands.importplayers import setup_importplayers
from commands.removeplayer import setup_removeplayer
from commands.players import setup_players
from commands.xi import setup_xi
from commands.daily import setup_daily
from commands.inventory import setup_inventory
from commands.stats import setup_stats


# ---------------- CONFIGURATION ----------------

OWNER_ID = 1451236422785958040

load_dotenv()

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError(
        "Missing TOKEN environment variable. "
        "Add TOKEN to your hosting provider's secrets."
    )


# ---------------- BOT INITIALIZATION ----------------

start_time = time.time()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="g!",
    intents=intents,
    help_command=None
)


# ---------------- READY EVENT ----------------

@bot.event
async def on_ready():
    print("=" * 40)
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("Cricket Apex is online!")
    print(f"Connected to {len(bot.guilds)} servers")
    print("=" * 40)

# ---------------- MAINTENANCE MODE ----------------

def is_maintenance_enabled() -> bool:
    try:
        with open("maintenance.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("enabled", False)

    except (FileNotFoundError, json.JSONDecodeError):
        return False


@bot.check
async def maintenance_check(ctx):
    if ctx.author.id == OWNER_ID:
        return True

    if not is_maintenance_enabled():
        return True

    embed = discord.Embed(
        title="🚧 Scheduled Maintenance",
        description=(
            "⚙️ Cricket Apex is currently under maintenance.\n\n"
            "We're working on improvements and bug fixes.\n\n"
            "Please check back soon.\n\n"
            "Thank you for your patience and support! ❤️"
        ),
        color=discord.Color.orange()
    )

    embed.set_footer(
        text="Cricket Apex • We'll be back soon!"
    )

    await ctx.send(embed=embed)
    return False


# ---------------- REGISTER COMMANDS ----------------

setup_ping(bot, start_time)
setup_help(bot)
setup_debut(bot)
setup_profile(bot)
setup_play(bot)
setup_dev(bot)
setup_balance(bot)
setup_shop(bot)
setup_crate(bot)
setup_addplayer(bot)
setup_buy(bot)
setup_importplayers(bot)
setup_removeplayer(bot)
setup_backupdb(bot)
setup_players(bot)
setup_xi(bot)
setup_daily(bot)
setup_inventory(bot)
setup_stats(bot)


# ---------------- DATABASE INITIALIZATION ----------------

create_tables()


# ---------------- HOSTING KEEP-ALIVE SERVER ----------------

keep_alive()

# ---------------- ERROR HANDLING ----------------

@bot.event
async def on_command_error(ctx, error):

    # Ignore normal command lookup failures.
    if isinstance(error, commands.CommandNotFound):
        return

    # Handle missing permissions without exposing tracebacks.
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ You don't have permission to use this command."
        )
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "❌ You're missing a required argument for this command."
        )
        return

    # Log unexpected errors using your existing logger.
    try:
        await log_error(
            bot=bot,
            error=error,
            user=ctx.author,
            guild=ctx.guild,
            channel=ctx.channel,
            command=ctx.message.content
        )
    except Exception as log_error_exception:
        print(
            "Failed to log command error:",
            type(log_error_exception).__name__
        )

    await ctx.send(
        "❌ An unexpected error occurred. Please try again later."
    )


# ---------------- LOGGER TEST COMMAND ----------------

@bot.command()
async def logtest(ctx):
    channel = bot.get_channel(1527174625241333780)

    if channel is None:
        await ctx.send("❌ Logger channel not found!")
        return

    await channel.send("✅ Logger works!")
    await ctx.send("✅ Test message sent!")


# ---------------- START BOT ----------------

if __name__ == "__main__":
    bot.run(TOKEN)
