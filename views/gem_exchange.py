import discord
from utils.emoji import GEM, COIN


def build_gem_exchange():

    embed = discord.Embed(
        title=f"{GEM} Gem Exchange",
        description=(
            "Exchange your Gems for Coins.\n\n"
            "⭐ **Featured Pack**\n"
            "Our best value exchange pack.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "💎 Larger exchanges reward better value.\n\n"
            "**Select an exchange pack below.**"
        ),
        color=discord.Color.blue()
    )

    return embed