import discord
from discord.ext import commands

from database import connect_db
from views.buy_view import BuyView
from utils.logger import log_action

def fetch_player(identifier):
    conn = connect_db()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM players
            WHERE id = ?
               OR LOWER(name) = LOWER(?)
            """,
            (identifier, identifier)
        )

        row = cursor.fetchone()

        if row:
            return dict(row)

        return None

    finally:
        conn.close()


def build_player_embed(player):
    embed = discord.Embed(
        title=player["name"],
        description=f"{player['role']} • {player['country']} • {player['rarity']}",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🪙 Price",
        value=f"{player['price']:,}",
        inline=True
    )

    embed.add_field(
        name="⭐ OVR",
        value=str(player["ovr"]),
        inline=True
    )

    embed.add_field(
        name="🏏 Team",
        value=player["team"] or "Unknown",
        inline=True
    )

    embed.add_field(
        name="🏏 Batting",
        value=str(player["batting_ovr"]),
        inline=True
    )

    embed.add_field(
        name="🎯 Bowling",
        value=str(player["bowling_ovr"]),
        inline=True
    )

    embed.add_field(
        name="🧤 Fielding",
        value=str(player["fielding_ovr"]),
        inline=True
    )

    if player.get("image"):
        embed.set_image(url=player["image"])

    embed.set_footer(text=f"Player ID: {player['id']}")

    return embed


def setup_buy(bot):

    @bot.command(name="buy")
    async def buy(ctx, *, player_name: str = None):

        if player_name is None:
            await ctx.send("❌ Usage: `g!buy <player name>`")
            return

        player = fetch_player(player_name)

        if player is None:
            await ctx.send(f"❌ No player found matching `{player_name}`.")
            return

        embed = build_player_embed(player)

        view = BuyView(player, ctx.author)

        message = await ctx.send(
            embed=embed,
            view=view
        )

        view.message = message