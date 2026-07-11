import discord
import json
from discord.ext import commands

USER_FILE = "users.json"

Coins ="<:coin:1521927683439595730>"
Gems = "<a:diamond:1522083613657665606>"
Trophies = "<:trophy:1522081868445388830>"
Balance_header = "<a:points_1:1522084496223240213>"


def setup_balance(bot):

    @bot.command(name="balance", aliases=["bal"])
    async def balance(ctx):

        try:
            with open(USER_FILE, "r") as f:
                users = json.load(f)
        except:
            users = {}

        user_id = str(ctx.author.id)

        if user_id not in users:
            await ctx.send("❌ Use `g!debut` first.")
            return

        user = users[user_id]

        embed = discord.Embed(title=f"{Balance_header}{ctx.author.display_name}'s Balance", color=0*00000)

        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url
        )

        embed.add_field(
            name= f"{Coins} Coins",
            value=f"**{user['coins']:,}**",
            inline=True
        )

        embed.add_field(
            name= f"{Gems} Gems",
            value=f"**{user['gems']:,}**",
            inline=True
        )

        embed.add_field(
            name= f"{Trophies} Trophies",
            value=f"**{user['trophies']:,}**",
            inline=True
        )

        embed.set_footer(
            text="Low on coins/gems? Explore g!shop to buy some"
        )

        await ctx.send(embed=embed)