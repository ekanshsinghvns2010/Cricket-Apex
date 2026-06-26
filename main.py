import discord
from discord.ext import commands
from dotenv import load_dotenv
from commands.debut import setup_debut
from commands.profile import setup_profile
from commands.play import setup_play
import os
import time

from commands.ping import setup_ping
from commands.help import setup_help

# Load .env
load_dotenv()

TOKEN = os.getenv("TOKEN")

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
    print(f"✅ Logged in as {bot.user}")
    print("🏏 Cricket Bot is Online!")
    print(f"🏠 Connected to {len(bot.guilds)} servers")
    print("=" * 40)

# Load commands
setup_ping(bot, start_time)
setup_help(bot)

setup_debut(bot)
setup_profile(bot)
setup_play(bot)
# Run bot
bot.run(TOKEN)