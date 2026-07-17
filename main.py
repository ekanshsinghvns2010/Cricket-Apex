import discord
import database
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
from commands.debut import setup_debut
from commands.profile import setup_profile
from commands.play import setup_play
from commands.dev import setup_dev
import os
import time
from commands.ping import setup_ping
from commands.help import setup_help
from commands.balance import setup_balance
from commands.shop import setup_shop
from commands.crate import setup_crate
from commands.addplayer import setup_addplayer
from commands.buy import setup_buy
from commands.importplayers import setup_importplayers
from commands.removeplayer import setup_removeplayer
from backupdb import setup_backupdb
from commands.players import setup_players
from database import create_tables
from commands.xi import setup_xi
from utils.logger import log_error
from commands.daily import setup_daily
# Load .env
load_dotenv()

TOKEN = os.getenv("TOKEN")
print(f"Token loaded: {TOKEN is not None}")

# Bot start time
start_time = time.time()

# Intents
intents = discord.Intents.default()
intents.message_content = True

# Bot setup
bot = commands.Bot(
    command_prefix="g!",
    intents=intents,
    help_command=None
)

# Ready event
@bot.event
async def on_ready():
    print("=" * 40)
    print(f"✅ Logged in as {bot.user.name}")
    print (bot.user.id)
    print("🏏 Cricket Bot is Online!")
    print(f"🏠 Connected to {len(bot.guilds)} servers")
    print("=" * 40)

# Load commands
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
create_tables()
setup_xi(bot)
setup_daily(bot)
#Run bot
keep_alive()
@bot.event
async def on_command_error(ctx, error):

    await log_error(
        bot=bot,
        error=error,
        user=ctx.author,
        guild=ctx.guild,
        channel=ctx.channel,
        command=ctx.message.content
    )

    await ctx.send(
        "❌ An unexpected error occurred."
    )
@bot.command()
async def logtest(ctx):
    channel = bot.get_channel(1527174625241333780)

    if channel is None:
        await ctx.send("Channel not found!")
        return

    await channel.send("✅ Logger works!")
    await ctx.send("Sent!")
@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"❌ {type(error).__name__}: {error}")
bot.run(TOKEN)