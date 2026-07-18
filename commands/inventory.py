import discord
from discord.ext import commands
import json

from views.inventory_view import InventoryView
from database import connect_db
from utils.emoji import COIN,GEM, CRATE, COMMON, RARE, EPIC, LEGENDARY, DAILY, BAG

def setup_inventory(bot):

    @bot.command(name="inventory", aliases=["inv"])
    async def inventory(ctx):

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE user_id=?",
            (str(ctx.author.id),)
        )

        user = cursor.fetchone()
        print(dict(user))

        if user is None:
            conn.close()

            await ctx.send(
                "❌ You don't have a profile.\nUse `g!debut` first."
            )
            return
        crates = json.loads(user["crates"])
        cards = json.loads(user["cards"])

        coins = user["coins"]
        gems = user["gems"]
        streak = user["daily_streak"]

        conn.close()

        embed = discord.Embed(
            title=f"🎒 {ctx.author.display_name}'s Inventory",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="💰 Economy",
            value=(
                f"{COIN} Coins: **{coins:,}**\n"
                f"{GEM} Gems: **{gems:,}**"
            ),
            inline=False
        )
        embed.add_field(
            name=f"{CRATE} Crates",
            value=(
                f"{COMMON} Common: **{crates['common']}**\n"
                f"{RARE} Rare: **{crates['rare']}**\n"
                f"{EPIC} Epic: **{crates['epic']}**\n"
                f"{LEGENDARY} Legendary: **{crates['legendary']}**"
            ),
            inline=False
        )
        embed.add_field(
            name=f"{DAILY} Daily",
            value=(
                f"🔥 Current Streak: **{streak}**"
            ),
            inline=True
        )

        embed.add_field(
            name=f"{BAG} Collection",
            value=(
                f"Players Owned: **{len(cards)} / 25**"
            ),
            inline=True
        )
        
        embed.set_footer(
            text="More inventory items will be added in future updates."
        )

        await ctx.send(
            embed=embed,
           view=InventoryView(user)
        )