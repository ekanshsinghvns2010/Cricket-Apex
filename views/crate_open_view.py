import discord
import json
from utils.cards import add_card


class CrateOpenView(discord.ui.View):

    def __init__(self, rewards, crate_type, user_id):
        super().__init__(timeout=180)

        self.rewards = rewards
        self.crate_type = crate_type
        self.user_id = user_id

        self.current = 0

        self.button = discord.ui.Button(
            label="📦 OPEN",
            style=discord.ButtonStyle.green
        )

        self.button.callback = self.button_callback

        self.add_item(self.button)

    async def button_callback(self, interaction: discord.Interaction):

        # Last press = Collect
        if self.current >= len(self.rewards):
            return await self.collect(interaction)

        reward = self.rewards[self.current]

        if reward["type"] == "coins":
            title = "🪙 Coins"
            description = f"**+{reward['amount']} Coins**"

        elif reward["type"] == "gems":
            title = "💎 Gems"
            description = f"**+{reward['amount']} Gems**"

        elif reward["type"] == "xp":
            title = "⭐ XP"
            description = f"**+{reward['amount']} XP**"

        else:
            title = f"{reward['emoji']} Player Card"
            description = (
                f"**{reward['player']}**\n"
                f"Rarity: **{reward['rarity']}**"
            )

        remaining = len(self.rewards) - self.current - 1

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.gold()
        )

        embed.add_field(
            name="Rewards Remaining",
            value=f"🎁 {remaining}",
            inline=False
        )

        self.current += 1

        if self.current == len(self.rewards):
            self.button.label = "🎁 COLLECT"
            self.button.style = discord.ButtonStyle.blurple
        else:
            self.button.label = "▶ CONTINUE"

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    async def collect(self, interaction):
        pass

        async def collect(self, interaction):

         with open("users.json", "r") as f:
            data = json.load(f)

        user = data[self.user_id]

        summary = []

        for reward in self.rewards:

            if reward["type"] == "coins":

                user["coins"] += reward["amount"]
                user["lifetime_earned"] += reward["amount"]

                summary.append(
                    f"🪙 +{reward['amount']} Coins"
                )

            elif reward["type"] == "gems":

                user["gems"] += reward["amount"]

                summary.append(
                    f"💎 +{reward['amount']} Gems"
                )

            elif reward["type"] == "xp":

                user["xp"] += reward["amount"]

                summary.append(
                    f"⭐ +{reward['amount']} XP"
                )

            elif reward["type"] == "card":

                add_card(
                    self.user_id,
                    reward["player"]
                )

                summary.append(
                    f"{reward['emoji']} {reward['player']} ({reward['rarity']})"
                )

        with open("users.json", "w") as f:
            json.dump(data, f, indent=4)

        embed = discord.Embed(
            title="🎉 Crate Rewards Collected!",
            description="\n".join(summary),
            color=discord.Color.green()
        )

        embed.set_footer(
            text="All rewards have been added to your account."
        )

        self.clear_items()

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )