import discord
from discord.ext import commands

def setup_backupdb(bot):

    @bot.command()
    async def backupdb(ctx):

        if ctx.author.id != 1451236422785958040:
            return

        await ctx.send(
            file=discord.File("cricket_go.db")
        )