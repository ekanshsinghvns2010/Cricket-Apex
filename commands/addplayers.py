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
            ("Upload Player Image", "image")
        ]

        data = {}

        def check(m):
            return (
                m.author == ctx.author and
                m.channel == ctx.channel
            )

        for question, key in questions:

            await ctx.send(f"**{question}:**")

            try:
                msg = await bot.wait_for(
                    "message",
                    timeout=120,
                    check=check
                )

            except Exception:
                await ctx.send("❌ Timed out.")
                return

            if key == "image":

                if len(msg.attachments) == 0:
                    await ctx.send("❌ Please upload an image.")
                    return

                data[key] = msg.attachments[0].url
                continue

            value = msg.content

            if key in [
                "ovr",
                "batting_ovr",
                "bowling_ovr",
                "fielding_ovr",
                "fitness",
                "price"
            ]:

                try:
                    value = int(value)

                except ValueError:
                    await ctx.send(f"❌ {question} must be a number.")
                    return

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

        # Prevent duplicate players
        for p in players:
            if p["id"] == player["id"]:
                await ctx.send("❌ A player with this name already exists.")
                return

        players.append(player)
        save_players(players)

        embed = discord.Embed(
            title="✅ Player Added Successfully",
            description=f"**{player['name']}** has been added to the database.",
            color=discord.Color.green()
        )

        embed.add_field(name="🪙 Price", value=f"{player['price']:,}", inline=True)
        embed.add_field(name="⭐ OVR", value=player["ovr"], inline=True)
        embed.add_field(name="🏏 Role", value=player["role"], inline=True)

        embed.add_field(name="🌍 Country", value=player["country"], inline=True)
        embed.add_field(name="🎖️ Rarity", value=player["rarity"], inline=True)
        embed.add_field(name="🏏 Team", value=player["team"], inline=True)

        embed.add_field(name="Batting", value=player["batting_ovr"], inline=True)
        embed.add_field(name="Bowling", value=player["bowling_ovr"], inline=True)
        embed.add_field(name="Fielding", value=player["fielding_ovr"], inline=True)

        if player["image"]:
            embed.set_thumbnail(url=player["image"])

        embed.set_footer(text=f"Player ID: {player['id']}")

        await ctx.send(embed=embed)
        