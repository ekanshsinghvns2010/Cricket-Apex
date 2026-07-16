import discord
from discord.ext import commands

from database import connect_db
from utils.logger import log_action

OWNER_ID = 1451236422785958040


def setup_removeplayer(bot):

    @bot.command(name="removeplayer")
    async def removeplayer(ctx, *, player_name):

        if ctx.author.id != OWNER_ID:
            await ctx.send("❌ Only the bot owner can use this command.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        # Find player first
        cursor.execute(
            "SELECT * FROM players WHERE LOWER(name) = LOWER(?)",
            (player_name,)
        )

        player = cursor.fetchone()

        if player is None:
            conn.close()
            await ctx.send(
                f"❌ Player not found: `{player_name}`"
            )
            return

        # Delete player
        cursor.execute(
            "DELETE FROM players WHERE LOWER(name) = LOWER(?)",
            (player_name,)
        )

        conn.commit()
        conn.close()
        await log_action(
    bot=bot,
    title="🗑️ Player Removed",
    description=(
        f"**Player:** {player['name']}\n"
        f"**Country:** {player['country']}\n"
        f"**Role:** {player['role']}\n"
        f"**OVR:** {player['ovr']}\n"
        f"**Rarity:** {player['rarity']}"
    ),
    color=discord.Color.red(),
    user=ctx.author,
    guild=ctx.guild,
    channel=ctx.channel
)

        embed = discord.Embed(
            title="🗑️ Player Removed",
            description=f"Successfully removed **{player['name']}** from database.",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Country",
            value=player["country"],
            inline=True
        )

        embed.add_field(
            name="OVR",
            value=str(player["ovr"]),
            inline=True
        )

        embed.add_field(
            name="Rarity",
            value=player["rarity"],
            inline=True
        )

        await ctx.send(embed=embed)