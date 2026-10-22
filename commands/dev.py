import random
import json
import discord
from discord.ext import commands

from database import connect_db
from utils.match_utils import load_matches, save_matches, find_player_match
from views.matches_lobby import build_lobby_embed, MatchLobbyView
from utils.countdown import start_countdown
from utils.logger import log_action

DEVELOPER_ID = 1451236422785958040


def setup_dev(bot):

    @bot.command(name="maintenance")
    async def maintenance(ctx, mode=None):
        if ctx.author.id != DEVELOPER_ID:
            await ctx.send("❌ This command is only available to the developer.")
            return

        if mode is None or mode.lower() not in ("on", "off"):
            await ctx.send("Usage: g!maintenance on/off")
            return

        enabled = mode.lower() == "on"

        with open("maintenance.json", "w", encoding="utf-8") as file:
            json.dump({"enabled": enabled}, file, indent=4)

        if enabled:
            await bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="🚧 Under Maintenance"
                )
            )
            await ctx.send("✅ Maintenance enabled.")
        else:
            await bot.change_presence(
                activity=discord.Game("g!help | Cricket Go")
            )
            await ctx.send("✅ Maintenance disabled.")

    @bot.command(name="fill")
    async def fill(ctx):
        if ctx.author.id != DEVELOPER_ID:
            await ctx.send("❌ This command is only available to the developer.")
            return

        match_id = find_player_match(ctx.author.id)

        if match_id is None:
            await ctx.send(
                "❌ I couldn't find a match containing you. "
                "Create a new lobby and try again."
            )
            return

        matches = load_matches()
        match = matches.get(str(match_id))

        if match is None:
            await ctx.send("❌ Match data could not be loaded.")
            return

        if match.get("status") != "lobby":
            await ctx.send(
                f"❌ This match is already in status: "
                f"{match.get('status', 'unknown')}."
            )
            return

        try:
            team_size = int(match["team_size"])

            match.setdefault("red_team", [])
            match.setdefault("blue_team", [])
            match.setdefault("red_bots", [])
            match.setdefault("blue_bots", [])

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

            # Fill Red Team without exceeding the team size.
            while (
                len(match["red_team"]) + len(match["red_bots"])
                < team_size
            ):
                match["red_bots"].append({
                    "name": random.choice(bot_names),
                    "role": random.choice(bot_roles)
                })

            # Fill Blue Team without exceeding the team size.
            while (
                len(match["blue_team"]) + len(match["blue_bots"])
                < team_size
            ):
                match["blue_bots"].append({
                    "name": random.choice(bot_names),
                    "role": random.choice(bot_roles)
                })

            save_matches(matches)

            channel_id = match.get("channel_id")
            message_id = match.get("message_id")

            if not channel_id or not message_id:
                await ctx.send(
                    "❌ The lobby message is not saved correctly. "
                    "Please create a fresh lobby using g!play."
                )
                return

            channel = bot.get_channel(int(channel_id))

            if channel is None:
                channel = await bot.fetch_channel(int(channel_id))

            lobby_message = await channel.fetch_message(int(message_id))

            red_total = (
                len(match["red_team"]) + len(match["red_bots"])
            )
            blue_total = (
                len(match["blue_team"]) + len(match["blue_bots"])
            )

            both_full = (
                red_total >= team_size
                and blue_total >= team_size
            )

            if not both_full:
                embed = await build_lobby_embed(ctx.guild, match_id)

                await lobby_message.edit(
                    embed=embed,
                    view=MatchLobbyView(match_id)
                )

                await ctx.send(
                    "⚠️ Lobby refreshed, but teams are not full.\n"
                    f"🔴 Red: {red_total}/{team_size}\n"
                    f"🔵 Blue: {blue_total}/{team_size}"
                )
                return

            await ctx.send(
                "✅ Teams filled!\n"
                f"🔴 Red: {red_total}/{team_size}\n"
                f"🔵 Blue: {blue_total}/{team_size}\n"
                "⏳ Starting five-second countdown..."
            )

            # The countdown function handles the status transition.
            await start_countdown(lobby_message, match_id)

        except discord.NotFound:
            await ctx.send(
                "❌ The lobby message or channel could not be found. "
                "Please create a fresh lobby using g!play."
            )

        except discord.Forbidden:
            await ctx.send(
                "❌ I don't have permission to read or edit the lobby message."
            )

        except Exception as error:
            print(
                f"g!fill failed: {type(error).__name__}: {error}"
            )
            await ctx.send(
                f"❌ Fill failed: {type(error).__name__}: {error}"
            )

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

        try:
            cursor.execute(
                "SELECT * FROM users WHERE user_id=?",
                (str(member.id),)
            )
            user = cursor.fetchone()

            if not user:
                await ctx.send("❌ User doesn't have a profile.")
                return

            valid_items = [
                "coins", "gems", "common",
                "rare", "epic", "legendary"
            ]

            item = item.lower()

            if item not in valid_items:
                await ctx.send(
                    "❌ Valid items: coins, gems, common, rare, epic, legendary"
                )
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

        finally:
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