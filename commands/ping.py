import discord
import time
import psutil
import os

Memory= "<:cpu:1522108472777244723>"
CPU= "<a:rk_loading:1522112218148241570>"


def setup_ping(bot, start_time):

    @bot.command()
    async def ping(ctx):

        latency = round(bot.latency * 1000)
        process = psutil.Process(os.getpid())

        memory = process.memory_info().rss / (1024 * 1024)
        cpu = psutil.cpu_percent(interval=0.1)

        users = len(set(bot.get_all_members()))
        servers = len(bot.guilds)
        commands_count = len(bot.commands)

        uptime_seconds = int(time.time() - start_time)

        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60

        uptime = f"{days}d {hours}h {minutes}m {seconds}s"

        embed = discord.Embed(
            title="🏏 Cricket Bot Status",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📡 Latency",
            value=f"`{latency}ms`",
            inline=True
        )

        embed.add_field(
            name=f"{Memory} Memory usage",
            value=f"{memory:.1f}MB",
            inline=True
        )

        embed.add_field(
            name=f"{CPU} CPU usage",
            value=f"{cpu:.1f}%",
            inline=True
        )

        embed.add_field(
            name="👥 Users",
            value=f"`{users}`",
            inline=True
        )

        embed.add_field(
            name="🏠 Servers",
            value=f"`{servers}`",
            inline=True
        )

        embed.add_field(
            name="⚙ Commands",
            value=f"`{commands_count}`",
            inline=True
        )

        embed.add_field(
            name="👑 Owner",
            value="`Ekansh Singh`",
            inline=True
        )

        embed.add_field(
            name="⏱ Uptime",
            value=f"`{uptime}`",
            inline=True
        )

        await ctx.send(embed=embed)
