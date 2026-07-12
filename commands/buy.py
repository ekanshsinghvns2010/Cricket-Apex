import discord
from discord.ext import commands

from database import connect_db
from views.buy_view import BuyView


def fetch_player(identifier):
    """
    Looks up a player by exact id or by name (case-insensitive).
    Returns a sqlite3.Row or None.
    """
    conn = connect_db()

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM players WHERE id = ? OR LOWER(name) = LOWER(?)",
            (identifier, identifier)
        )
        return cursor.fetchone()
    finally:
        conn.close()


def build_player_embed(player):
    """Builds the embed shown alongside the Buy/Cancel buttons."""
    embed = discord.Embed(
        title=player["name"],
        description=f"{player['role']} • {player['country']} • {player['rarity']}",
        color=discord.Color.blue()
    )

    embed.add_field(name="🪙 Price", value=f"{player['price']:,}", inline=True)
    embed.add_field(name="⭐ OVR", value=player["ovr"], inline=True)
    embed.add_field(name="🏏 Team", value=player["team"], inline=True)

    embed.add_field(name="Batting", value=player["batting_ovr"], inline=True)
    embed.add_field(name="Bowling", value=player["bowling_ovr"], inline=True)
    embed.add_field(name="Fielding", value=player["fielding_ovr"], inline=True)

    if player.get ("image"):
        embed.set_image(url=player("image"))

    embed.set_footer(text=f"Player ID: {player['id']}")

    return embed


def setup_buy(bot):

    @bot.command(name="buy")
    async def buy(ctx, *, player_name: str = None):

        if not player_name:
            await ctx.send("❌ Please specify a player name. Usage: `g!buy <player name>`")
            return

        player = fetch_player(player_name)

        if player is None:
            await ctx.send(f"❌ No player found matching `{player_name}`.")
            return

        embed = build_player_embed(player)

        view = BuyView(dict(player), ctx.author)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg
        