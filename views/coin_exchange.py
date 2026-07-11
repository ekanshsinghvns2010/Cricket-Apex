import discord
from utils.emoji import GEM, COIN


def build_coin_exchange():

    embed = discord.Embed(
        title=f"{COIN} Coin Exchange",
        description=(
            "Exchange your Coins for Gems.\n\n"
            "⭐ **Featured Pack**\n"
            "Our best value exchange pack.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🪙 Larger exchanges reward better value.\n\n"
            "**Select an exchange pack below.**"
        ),
        color=discord.Color.blue()
    )

    return embed