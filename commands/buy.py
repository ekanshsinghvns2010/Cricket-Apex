import discord
from discord.ext import commands
import json
import os

from views.buy_view import BuyView

PLAYERS_FILE = "players.json"


def load_players():
    if not os.path.exists(PLAYERS_FILE):
        return []

    with open(PLAYERS_FILE, "r") as f:
        return json.load(f)


def setup_buy(bot):

    @bot.command(name="buy")
    async def buy(ctx, *, player_name: str = None):

        if player_name is None:
            await ctx.send("❌ Usage: `g!buy <player name>`")
            return

        players = load_players()

        if len(players) == 0:
            await ctx.send(
                embed=discord.Embed(
                    title="❌ No Players",
                    description="There are no players in the database.",
                    color=discord.Color.red()
                )
            )
            return

        player = None

        for p in players:
            if p["name"].lower() == player_name.lower():
                player = p
                break

        if player is None:
            await ctx.send(
                embed=discord.Embed(
                    title="❌ Player Not Found",
                    description=f"`{player_name}` does not exist.",
                    color=discord.Color.red()
                )
            )
            return

        embed = discord.Embed(
            title=player["name"],
            description=f"🪙 **Price:** {player['price']:,} Coins",
            color=discord.Color.gold()
        )

        if player.get("image"):
            embed.set_image(url=player["image"])

        embed.add_field(
            name="Overall",
            value=f"**{player['ovr']} OVR**",
            inline=True
        )

        embed.add_field(
            name="Role",
            value=player["role"],
            inline=True
        )

        embed.add_field(
            name="Country",
            value=player["country"],
            inline=True
        )

        embed.add_field(
            name="Batting",
            value=player["batting_ovr"],
            inline=True
        )

        embed.add_field(
            name="Bowling",
            value=player["bowling_ovr"],
            inline=True
        )

        embed.add_field(
            name="Fielding",
            value=player["fielding_ovr"],
            inline=True
        )

        embed.add_field(
            name="Batting Style",
            value=player["batting_style"],
            inline=True
        )

        embed.add_field(
            name="Bowling Style",
            value=player["bowling_style"],
            inline=True
        )

        embed.add_field(
            name="Rarity",
            value=player["rarity"],
            inline=True
        )

        embed.set_footer(text="Press the Buy button below to purchase this player.")

        await ctx.send(
            embed=embed,
            view=BuyView(player)
        )