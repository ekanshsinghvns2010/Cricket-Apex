import discord

from utils.emoji import COIN, GEM, MONEY


def build_coins_shop():

    embed = discord.Embed(
        title=f"{COIN} Coins Shop",
        description=(
            "Purchase Coins to boost your Cricket 11 career.\n\n"
            "Choose how you'd like to obtain Coins.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"{GEM} **Gem Exchange**\n"
            "Exchange your Gems for Coins instantly.\n\n"
            f"{MONEY} **Coin Store**\n"
            "Purchase premium Coin Packs using real money.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**Select an option below.**"
        ),
        color=0xFFD54F
    )

    return embed