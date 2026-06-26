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
            "Aarav",
            "Vivaan",
            "Kabir",
            "Arjun",
            "Rohan",
            "Viraj",
            "Aditya",
            "Dev",
            "Aryan",
            "Yash"
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

        bot_number = 1

        while len(match["red_team"]) < match["team_size"]:
            bot_id = f"BOT_RED_{bot_number}"
            match["red_team"].append(bot_id)
            bot_number += 1

        while len(match["blue_team"]) < match["team_size"]:
            bot_id = f"BOT_BLUE_{bot_number}"
            match["blue_team"].append(bot_id)

            if match["blue_captain"] is None:
                match["blue_captain"] = bot_id

            bot_number += 1

        save_matches(matches)

        await ctx.send("🤖 Lobby filled successfully!")