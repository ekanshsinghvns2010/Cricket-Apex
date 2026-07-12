import discord
from discord.ext import commands

from database import connect_db
from views.buy_view import BuyView


def setup_buy(bot):

    @bot.command(name="buy")
    async def buy(ctx, *, player_name: str = None):

        if player_name is None:
            await ctx.send("❌ Usage: `g!buy <player name>`")
            return


        conn = connect_db()
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT *
            FROM players
            WHERE LOWER(name) = LOWER(?)
            """,
            (player_name,)
        )

        player = cursor.fetchone()

        conn.close()


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


        if player["image"]:
            embed.set_image(
                url=player["image"]
            )


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
            value=str(player["batting_ovr"]),
            inline=True
        )

        embed.add_field(
            name="Bowling",
            value=str(player["bowling_ovr"]),
            inline=True
        )

        embed.add_field(
            name="Fielding",
            value=str(player["fielding_ovr"]),
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


        embed.set_footer(
            text="Press the Buy button below to purchase this player."
        )


        await ctx.send(
            embed=embed,
            view=BuyView(dict(player))
        )