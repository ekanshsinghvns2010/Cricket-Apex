import discord
import json
import random

from views.crate_open import build_crate_open
from views.crate_open_view import CrateOpenView


# --------------------------
# Reward Generator
# --------------------------

def generate_rewards(crate_type):

    rewards = []

    if crate_type == "common":

        pool = [

            {
                "type": "coins",
                "amount": 500,
                "chance": 40
            },

            {
                "type": "coins",
                "amount": 1000,
                "chance": 20
            },

            {
                "type": "gems",
                "amount": 20,
                "chance": 15
            },

            {
                "type": "xp",
                "amount": 100,
                "chance": 15
            },

            {
                "type": "card",
                "player": "Virat Kohli",
                "rarity": "Common",
                "emoji": "🟢",
                "chance": 8
            },

            {
                "type": "card",
                "player": "AB de Villiers",
                "rarity": "Epic",
                "emoji": "🟣",
                "chance": 2
            }

        ]

        for _ in range(3):

            reward = random.choices(
                population=pool,
                weights=[int(r["chance"]) for r in pool],
                k=1
            )[0]

            rewards.append(reward.copy())

    return rewards

# --------------------------
# Crate Command
# --------------------------

def setup_crate(bot):

    @bot.command()
    async def crate(ctx, crate_type="common"):

        user_id = str(ctx.author.id)

        with open("users.json", "r") as f:
            data = json.load(f)

        crate_type = crate_type.lower()

        if user_id not in data:
            await ctx.send("❌ Create your profile first using `g!debut`.")
            return

        if crate_type not in data[user_id]["crates"]:
            await ctx.send("❌ Invalid crate type.")
            return

        if data[user_id]["crates"][crate_type] <= 0:
            await ctx.send(
                f"❌ You don't own any **{crate_type.title()} Crates**."
            )
            return

        # Consume one crate

        data[user_id]["crates"][crate_type] -= 1

        with open("users.json", "w") as f:
            json.dump(data, f, indent=4)

        rewards = generate_rewards(crate_type)

        embed = build_crate_open(
            f"{crate_type.title()} Crate",
            len(rewards)
        )

        await ctx.send(
            embed=embed,
            view=CrateOpenView(
                rewards,
                crate_type,
                user_id
            )
        )