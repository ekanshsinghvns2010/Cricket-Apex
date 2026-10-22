
import discord
from database import connect_db

Coins = "<:coin:1521927683439595730>"
Gems = "<a:diamond:1522083613657665606>"
Trophies = "<:trophy:1522081868445388830>"
Balance_header = "<a:points_1:1522084496223240213>"


def setup_balance(bot):

    @bot.command(name="balance", aliases=["bal"])
    async def balance(ctx):

        user_id = str(ctx.author.id)

        conn = connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT coins, gems, trophies
                FROM users
                WHERE user_id = ?
                """,
                (user_id,)
            )
            user = cursor.fetchone()
        finally:
            conn.close()

        if user is None:
            await ctx.send("❌ Use `g!debut` first.")
            return

        coins = user["coins"] or 0
        gems = user["gems"] or 0
        trophies = user["trophies"] or 0

        embed = discord.Embed(
            title=f"{Balance_header} {ctx.author.display_name}'s Balance",
            color=discord.Color.gold()
        )

        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url
        )

        embed.add_field(
            name=f"{Coins} Coins",
            value=f"**{coins:,}**",
            inline=True
        )

        embed.add_field(
            name=f"{Gems} Gems",
            value=f"**{gems:,}**",
            inline=True
        )

        embed.add_field(
            name=f"{Trophies} Trophies",
            value=f"**{trophies:,}**",
            inline=True
        )

        embed.set_footer(
            text="Low on coins/gems? Explore g!shop to buy some"
        )

        await ctx.send(embed=embed)
