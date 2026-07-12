import discord
from discord.ext import commands
import json
import os

from database import connect_db

PLAYERS_FILE = "players.json"
OWNER_ID = 1451236422785958040


def load_players_json():
    if not os.path.exists(PLAYERS_FILE):
        with open(PLAYERS_FILE, "w") as f:
            json.dump([], f, indent=4)

    with open(PLAYERS_FILE, "r") as f:
        return json.load(f)


def setup_importplayers(bot):

    @bot.command(name="importplayers")
    async def importplayers(ctx):

        if ctx.author.id != OWNER_ID:
            await ctx.send("❌ Only the bot owner can use this command.")
            return

        players = load_players_json()

        total_players = len(players)
        imported = 0
        skipped = 0

        conn = connect_db()

        try:
            cursor = conn.cursor()

            for player in players:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO players (
                        id,
                        name,
                        display_name,
                        country,
                        team,
                        role,
                        batting_style,
                        bowling_style,
                        ovr,
                        batting_ovr,
                        bowling_ovr,
                        fielding_ovr,
                        fitness,
                        rarity,
                        matches,
                        runs,
                        wickets,
                        catches,
                        price,
                        sell_price,
                        image
                    ) VALUES (
                        :id,
                        :name,
                        :display_name,
                        :country,
                        :team,
                        :role,
                        :batting_style,
                        :bowling_style,
                        :ovr,
                        :batting_ovr,
                        :bowling_ovr,
                        :fielding_ovr,
                        :fitness,
                        :rarity,
                        :matches,
                        :runs,
                        :wickets,
                        :catches,
                        :price,
                        :sell_price,
                        :image
                    )
                    """,
                    {
                        "id": player.get("id"),
                        "name": player.get("name"),
                        "display_name": player.get("display_name"),
                        "country": player.get("country"),
                        "team": player.get("team"),
                        "role": player.get("role"),
                        "batting_style": player.get("batting_style"),
                        "bowling_style": player.get("bowling_style"),
                        "ovr": player.get("ovr"),
                        "batting_ovr": player.get("batting_ovr"),
                        "bowling_ovr": player.get("bowling_ovr"),
                        "fielding_ovr": player.get("fielding_ovr"),
                        "fitness": player.get("fitness"),
                        "rarity": player.get("rarity"),
                        "matches": player.get("matches", 0),
                        "runs": player.get("runs", 0),
                        "wickets": player.get("wickets", 0),
                        "catches": player.get("catches", 0),
                        "price": player.get("price"),
                        "sell_price": player.get("sell_price"),
                        "image": player.get("image"),
                    }
                )

                if cursor.rowcount == 1:
                    imported += 1
                else:
                    skipped += 1

            conn.commit()

        finally:
            conn.close()

        embed = discord.Embed(
            title="✅ Player Import Complete",
            color=discord.Color.green()
        )

        embed.add_field(name="Imported", value=str(imported), inline=True)
        embed.add_field(name="Skipped", value=str(skipped), inline=True)
        embed.add_field(name="Total JSON Players", value=str(total_players), inline=True)

        await ctx.send(embed=embed)
        