import discord
from discord.ext import commands

from database import connect_db


OWNER_ID = 1451236422785958040


def setup_addplayer(bot):

    @bot.command(name="addplayer")
    async def addplayer(ctx):

        if ctx.author.id != OWNER_ID:
            await ctx.send("❌ Only the bot owner can use this command.")
            return

        questions = [
            ("Player Name", "name"),
            ("Country", "country"),
            ("Team", "team"),
            ("Role (BAT/WK/AR/BOWL)", "role"),
            ("Batting Style", "batting_style"),
            ("Bowling Style", "bowling_style"),
            ("Overall Rating", "ovr"),
            ("Batting OVR", "batting_ovr"),
            ("Bowling OVR", "bowling_ovr"),
            ("Fielding OVR", "fielding_ovr"),
            ("Fitness", "fitness"),
            ("Rarity", "rarity"),
            ("Price", "price"),
            ("Image URL", "image")
        ]

        data = {}

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for question, key in questions:

            await ctx.send(f"**{question}:**")

            try:
                msg = await bot.wait_for(
                    "message",
                    timeout=60,
                    check=check
                )

            except:
                await ctx.send("❌ Timeout.")
                return

            data[key] = msg.content


        number_fields = [
            "ovr",
            "batting_ovr",
            "bowling_ovr",
            "fielding_ovr",
            "fitness",
            "price"
        ]

        try:
            for field in number_fields:
                data[field] = int(data[field])

        except ValueError:
            await ctx.send("❌ Ratings and price must be numbers.")
            return


        player_id = data["name"].lower().replace(" ", "_")


        sell_price = int(data["price"] * 0.7)


        conn = connect_db()

        try:

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO players (

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

                )

                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

                """,

                (
                    player_id,
                    data["name"],
                    data["name"].upper(),
                    data["country"],
                    data["team"],
                    data["role"],
                    data["batting_style"],
                    data["bowling_style"],
                    data["ovr"],
                    data["batting_ovr"],
                    data["bowling_ovr"],
                    data["fielding_ovr"],
                    data["fitness"],
                    data["rarity"],
                    0,
                    0,
                    0,
                    0,
                    data["price"],
                    sell_price,
                    data["image"]
                )
            )

            conn.commit()


        except Exception as e:

            await ctx.send(
                f"❌ Database error:\n`{e}`"
            )

            conn.close()
            return


        conn.close()


        embed = discord.Embed(
            title="✅ Player Added",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Name",
            value=data["name"]
        )

        embed.add_field(
            name="OVR",
            value=str(data["ovr"])
        )

        embed.add_field(
            name="Role",
            value=data["role"]
        )

        embed.add_field(
            name="Country",
            value=data["country"]
        )

        embed.add_field(
            name="Rarity",
            value=data["rarity"]
        )

        embed.set_image(
            url=data["image"]
        )


        await ctx.send(embed=embed)