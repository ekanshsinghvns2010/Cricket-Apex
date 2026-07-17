import discord
from discord.ext import commands

import random
import sqlite3
import time
import json

from database import connect_db

DAILY_COOLDOWN = 86400  # 24 Hours

COIN_REWARDS = [
    (5000, 60),
    (10000, 40)
]

CRATE_CHANCES = {
    "common": 20,
    "rare": 10,
    "epic": 5,
    "legendary": 2
}


def weighted_coin_reward():
    roll = random.randint(1, 100)

    if roll <= 60:
        return 5000

    return 10000


def roll_crates():

    rewards = {
        "common": 0,
        "rare": 0,
        "epic": 0,
        "legendary": 0
    }

    for crate, chance in CRATE_CHANCES.items():

        if random.randint(1, 100) <= chance:
            rewards[crate] += 1

    return rewards


def get_random_streak_player():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM players
        WHERE ovr BETWEEN 80 AND 84
        ORDER BY RANDOM()
        LIMIT 1
    """)

    player = cursor.fetchone()

    conn.close()

    return player


def seconds_to_text(seconds):

    hours = seconds // 3600

    minutes = (seconds % 3600) // 60

    return f"{hours}h {minutes}m"


def get_user(user_id):

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (str(user_id),)
    )

    user = cursor.fetchone()

    conn.close()

    return user

def setup_daily(bot):

    @bot.command(name="daily")
    async def daily(ctx):

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE user_id=?",
            (str(ctx.author.id),)
        )

        user = cursor.fetchone()

        if user is None:
            conn.close()
            await ctx.send(
                "❌ You don't have a profile.\nUse `g!debut` first."
            )
            return

        now = int(time.time())

        last_daily = user["last_daily"]

        if now - last_daily < DAILY_COOLDOWN:

            remaining = DAILY_COOLDOWN - (now - last_daily)

            embed = discord.Embed(
                title="⏳ Daily Already Claimed",
                description=(
                    f"Come back after **{seconds_to_text(remaining)}**."
                ),
                color=discord.Color.red()
            )

            await ctx.send(embed=embed)

            conn.close()
            return

        coins = weighted_coin_reward()

        crates = roll_crates()

        current_crates = json.loads(user["crates"])

        for crate_name, amount in crates.items():
            current_crates[crate_name] += amount

        streak = user["daily_streak"] + 1

        streak_reward = None

        if streak % 7 == 0:
            current_crates["rare"] += 1

            streak_reward = get_random_streak_player()

            if streak_reward:

                cards = json.loads(user["cards"])

                if streak_reward["id"] not in cards:
                    cards.append(streak_reward["id"])

                cards_json = json.dumps(cards)

            else:
                cards_json = user["cards"]

        else:

            cards_json = user["cards"]
        cursor.execute(
            """
            UPDATE users
            SET
                coins = coins + ?,
                lifetime_earned = lifetime_earned + ?,
                crates = ?,
                cards = ?,
                last_daily = ?,
                daily_streak = ?
            WHERE user_id = ?
            """,
            (
                coins,
                coins,
                json.dumps(current_crates),
                cards_json,
                now,
                streak,
                str(ctx.author.id)
            )
        )

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="🎁 Daily Rewards",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="💰 Coins",
            value=f"+{coins:,}",
            inline=False
        )

        crate_text = ""

        if crates["common"]:
            crate_text += f"📦 Common Crate × {crates['common']}\n"

        if crates["rare"]:
            crate_text += f"🟦 Rare Crate × {crates['rare']}\n"

        if crates["epic"]:
            crate_text += f"🟪 Epic Crate × {crates['epic']}\n"

        if crates["legendary"]:
            crate_text += f"🟨 Legendary Crate × {crates['legendary']}\n"

        if crate_text == "":
            crate_text = "No crate won today."

        embed.add_field(
            name="📦 Bonus Rewards",
            value=crate_text,
            inline=False
        )

        embed.add_field(
            name="🔥 Daily Streak",
            value=f"{streak}/7",
            inline=True
        )

        if streak_reward:

            embed.add_field(
                name="🎉 Streak Reward",
                value=(
                    f"🎴 **{streak_reward['name']}**\n"
                    f"⭐ {streak_reward['ovr']} OVR\n"
                    f"📦 Rare Crate ×1"
                ),
                inline=False
            )

        embed.add_field(
            name="🎲 Reward Chances",
            value=(
                "💰 5,000 Coins — 60%\n"
                "💰 10,000 Coins — 40%\n\n"
                "📦 Common Crate — 20%\n"
                "🟦 Rare Crate — 10%\n"
                "🟪 Epic Crate — 5%\n"
                "🟨 Legendary Crate — 2%"
            ),
            inline=False
        )

        embed.set_footer(
            text="Come back after 24 hours!"
        )

        await ctx.send(embed=embed)