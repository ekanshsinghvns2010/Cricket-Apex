import discord
from discord.ext import commands
import random

from utils.match_utils import (
    load_matches,
    save_matches,
    find_player_match
)

DEVELOPER_ID = 1451236422785958040  # Your Discord ID


def setup_dev(bot):

    @bot.command(name="fill")
    async def fill(ctx):

        if ctx.author.id != DEVELOPER_ID:
            await ctx.send("❌ This command is only available to the developer.")
            return

        match_id = find_player_match(ctx.author.id)

        if match_id is None:
            await ctx.send("❌ You are not in any match.")
            return

        matches = load_matches()
        match = matches[match_id]

        bot_names = [
            "Aarav", "Vivaan", "Kabir", "Rohan",
            "Aryan", "Viraj", "Aditya", "Dev",
            "Krish", "Yash", "Ishaan", "Ayaan"
        ]

        bot_roles = [
            "Aggressive Batter",
            "Anchor Batter",
            "Finisher",
            "Fast Bowler",
            "Fast Swing Bowler",
            "Spinner",
            "All-Rounder"
        ]

        while (
            len(match["red_team"]) + len(match["red_bots"])
        ) < match["team_size"]:

            match["red_bots"].append({
                "name": random.choice(bot_names),
                "role": random.choice(bot_roles)
            })

        while (
            len(match["blue_team"]) + len(match["blue_bots"])
        ) < match["team_size"]:

            match["blue_bots"].append({
                "name": random.choice(bot_names),
                "role": random.choice(bot_roles)
            })

        save_matches(matches)

        await ctx.send("🤖 Lobby filled successfully!")