import discord
import json
import os

PROFILES_FILE = "users.json"


def load_profiles():
    if not os.path.exists(PROFILES_FILE):
        return {}

    with open(PROFILES_FILE, "r") as f:
        return json.load(f)


def save_profiles(data):
    with open(PROFILES_FILE, "w") as f:
        json.dump(data, f, indent=4)


class BuyView(discord.ui.View):

    def __init__(self, player):
        super().__init__(timeout=60)

        self.player = player

    @discord.ui.button(
        label="Buy Player",
        emoji="🪙",
        style=discord.ButtonStyle.green
    )
    async def buy(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        profiles = load_profiles()

        user_id = str(interaction.user.id)

        if user_id not in profiles:

            await interaction.response.send_message(
                "❌ You haven't used `g!debut` yet.",
                ephemeral=True
            )
            return

        profile = profiles[user_id]

        if "cards" not in profile:
            profile["cards"] = []

        if self.player["id"] in profile["cards"]:

            await interaction.response.send_message(
                "❌ You already own this player.",
                ephemeral=True
            )
            return

        if profile["coins"] < self.player["price"]:

            await interaction.response.send_message(
                f"❌ You need **{self.player['price']:,}** coins.",
                ephemeral=True
            )
            return

        profile["coins"] -= self.player["price"]

        profile["lifetime_spent"] += self.player["price"]

        profile["cards"].append(self.player["id"])

        save_profiles(profiles)

        button.disabled = True
        button.label = "Purchased"

        embed = discord.Embed(
            title="✅ Purchase Successful",
            description=f"You bought **{self.player['name']}**!",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=self.player["image"])

        embed.add_field(
            name="Coins Left",
            value=f"🪙 {profile['coins']:,}",
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )