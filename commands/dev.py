import random
import json

import discord
from discord.ext import commands

from database import connect_db

from utils.match_utils import (
    load_matches,
    save_matches,
    find_player_match
)

from views.matches_lobby import (
    build_lobby_embed,
    MatchLobbyView
)
from utils.countdown import start_countdown
from utils.logger import log_action

DEVELOPER_ID = 1451236422785958040


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

        # Fill Red Team
        while len(match["red_team"]) + len(match["red_bots"]) < match["team_size"]:
            match["red_bots"].append({
                "name": random.choice(bot_names),
                "role": random.choice(bot_roles)
            })

        # Fill Blue Team
        while len(match["blue_team"]) + len(match["blue_bots"]) < match["team_size"]:
            match["blue_bots"].append({
                "name": random.choice(bot_names),
                "role": random.choice(bot_roles)
            })

        save_matches(matches)

        try:
            channel = bot.get_channel(int(match["channel_id"]))

            if channel is None:
                await ctx.send("❌ Couldn't find the match channel.")
                return

            print("Match ID:", match_id)
            print("Channel ID:", match["channel_id"])
            print("Message ID:", match["message_id"])

            message = await channel.fetch_message(
                int(match["message_id"])
            )

            embed = await build_lobby_embed(
                ctx.guild,
                match_id
            )

            await message.edit(
                embed=embed,
                view=MatchLobbyView(match_id)
            )
            print("✅ Lobby message edited successfully")

            print("Red Humans:", len(match["red_team"]))
            print("Red Bots:", len(match["red_bots"]))
            print("Blue Humans:", len(match["blue_team"]))
            print("Blue Bots:", len(match["blue_bots"]))
            print("Team Size :", match["team_size"])

            red_full = len(match["red_team"]) + len(match["red_bots"])
            blue_full = len(match["blue_team"]) + len(match["blue_bots"])

            print(f"Red total = {red_full}")
            print(f"Blue total = {blue_full}")
            print(f"Required = {match['team_size']}")

            # Temporary force the countdown
            print(">>> Calling countdown...")
            await start_countdown(message, match_id)
            print("Status before countdown call:", match["status"])
            print(">>> Countdown finished")

            await ctx.send("✅ Lobby filled and refreshed!")

        except Exception as e:
            await ctx.send(f"❌ Fill Error: {type(e).__name__}: {e}")
            raise

    @bot.command(name="give")
    async def give(ctx, member: discord.Member, item: str, amount: int):

        if ctx.author.id != DEVELOPER_ID:
            await ctx.send("❌ Only the bot owner can use this command.")
            return

        if amount <= 0:
            await ctx.send("❌ Amount must be greater than 0.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id=?", (str(member.id),))
        user = cursor.fetchone()

        if not user:
            await ctx.send("❌ User doesn't have a profile.")
            conn.close()
            return

        valid_items = [
            "coins",
            "gems",
            "common",
            "rare",
            "epic",
            "legendary"
        ]

        item = item.lower()

        if item not in valid_items:
            await ctx.send(
                "❌ Valid items: coins, gems, common, rare, epic, legendary"
            )
            conn.close()
            return

        if item == "coins":
            cursor.execute(
                "UPDATE users SET coins = coins + ? WHERE user_id=?",
                (amount, str(member.id))
            )

        elif item == "gems":
            cursor.execute(
                "UPDATE users SET gems = gems + ? WHERE user_id=?",
                (amount, str(member.id))
            )

        else:
            crates = json.loads(user["crates"])

            crates[item] = crates.get(item, 0) + amount

            cursor.execute(
                "UPDATE users SET crates=? WHERE user_id=?",
                (json.dumps(crates), str(member.id))
            )

        conn.commit()
        conn.close()

        await log_action(
    bot=bot,
    title="👑 Developer Give Command",
    description=(
        f"**Developer:** {ctx.author.mention}\n"
        f"**Target:** {member.mention}\n"
        f"**Item:** {item.title()}\n"
        f"**Amount:** {amount}"
    ),
    color=discord.Color.gold(),
    user=ctx.author,
    guild=ctx.guild,
    channel=ctx.channel
)

        await ctx.send(
    f"✅ Added **{amount} {item}** to {member.mention}."
)
        