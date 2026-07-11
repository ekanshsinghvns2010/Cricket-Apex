import discord
import json
from utils.emoji import COIN
from utils.emoji import GEM
from views.shop_view import ShopView

USER_FILE = "users.json"


def load_users():
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def setup_shop(bot):

    @bot.command(name="shop")
    async def shop(ctx):

        users = load_users()

        user_id = str(ctx.author.id)

        if user_id not in users:
            await ctx.send(
                "❌ You haven't started your career.\nUse `g!debut` first."
            )
            return

        user = users[user_id]

        embed = discord.Embed(
            title="🛒 Cricket 11 Shop",
            description=(
                 "Welcome to the official Cricket 11 Marketplace!\n\n"
"Purchase premium items, unlock Passes, stock up on Coins and Gems, or exchange your resources through the menu below."
            ),
            color=discord.Color.green()
        )

        embed.add_field(
            name=f"{COIN} Coins",
            value=f"**{user['coins']:,}**",
            inline=True
        )

        embed.add_field(
            name=f"{GEM} Gems",
            value=f"**{user['gems']:,}**",
            inline=True
        )

        embed.set_thumbnail(
            url=ctx.author.display_avatar.url
        )

        embed.set_footer(
            text="Cricket 11 Economy"
        )

        await ctx.send(
            embed=embed,
            view=ShopView()
        )