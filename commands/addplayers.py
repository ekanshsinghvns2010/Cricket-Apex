import discord
from discord.ext import commands
import json
import os

PLAYERS_FILE = "players.json"


def load_players():
    if not os.path.exists(PLAYERS_FILE):
        with open(PLAYERS_FILE, "w") as f:
            json.dump([], f, indent=4)

    with open(PLAYERS_FILE, "r") as f:
        return json.load(f)


def save_players(players):
    with open(PLAYERS_FILE, "w") as f:
        json.dump(players, f, indent=4)


def setup_addplayer(bot):

    # CHANGE THIS TO YOUR DISCORD USER ID
    OWNER_ID = 1451236422785958040

    @bot.command(name="addplayer")
    async def addplayer(ctx):

        if ctx.author.id != OWNER_ID:
            await ctx.send("❌ Only the bot owner can use this command.")
            return

        questions = [
            ("Player Name", "name"),
            ("Country", "country"),
            ("Team", "team"),
            ("Role (BAT/BOWL/AR/WK)", "role"),
            ("Batting Style", "batting_style"),
            ("Bowling Style", "bowling_style"),
            ("Overall", "ovr"),
            ("Batting OVR", "batting_ovr"),
            ("Bowling OVR", "bowling_ovr"),
            ("Fielding OVR", "fielding_ovr"),
            ("Fitness", "fitness"),
            ("Rarity", "rarity"),
            ("Price", "price"),
            ("Image URL or Path", "image")
        ]

        data = {}

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for question, key in questions:

            await ctx.send(f"**{question}:**")

            try:
                msg = await bot.wait_for(
                    "message",
                    timeout=120,
                    check=check
                )
            except:
                await ctx.send("❌ Timed out.")
                return

            value = msg.content

            if key in [
                "ovr",
                "batting_ovr",
                "bowling_ovr",
                "fielding_ovr",
                "fitness",
                "price"
            ]:
                value = int(value)

            data[key] = value

        player = {
            "id": data["name"].lower().replace(" ", "_"),
            "name": data["name"],
            "display_name": data["name"].upper(),

            "country": data["country"],
            "team": data["team"],

            "role": data["role"],

            "batting_style": data["batting_style"],
            "bowling_style": data["bowling_style"],

            "ovr": data["ovr"],
            "batting_ovr": data["batting_ovr"],
            "bowling_ovr": data["bowling_ovr"],
            "fielding_ovr": data["fielding_ovr"],
            "fitness": data["fitness"],

            "rarity": data["rarity"],

            "matches": 0,
            "runs": 0,
            "wickets": 0,
            "catches": 0,

            "price": data["price"],
            "sell_price": int(data["price"] * 0.7),

            "image": data["image"]
        }

        players = load_players()
        players.append(player)
        save_players(players)

        embed = discord.Embed(
            title="✅ Player Added",
            color=discord.Color.green()
        )

        embed.add_field(name="Name", value=player["name"])
        embed.add_field(name="OVR", value=player["ovr"])
        embed.add_field(name="Role", value=player["role"])
        embed.add_field(name="Country", value=player["country"])
        embed.add_field(name="Rarity", value=player["rarity"])

        await ctx.send(embed=embed)