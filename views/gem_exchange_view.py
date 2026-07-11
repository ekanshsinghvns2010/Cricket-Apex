import discord
import json

class GemExchangeSelect(discord.ui.Select):

    def __init__(self):

        options = [
            discord.SelectOption(
                label="Starter Exchange",
                emoji="💎",
                description="Entry level exchange"
            ),
            discord.SelectOption(
                label="Rookie Exchange",
                emoji="🔷",
                description="Better value"
            ),
            discord.SelectOption(
                label="Pro Exchange",
                emoji="🔹",
                description="Popular choice"
            ),
            discord.SelectOption(
                label="Elite Exchange",
                emoji="💠",
                description="High value exchange"
            ),
            discord.SelectOption(
                label="Ultimate Exchange",
                emoji="👑",
                description="Best value"
            ),
        ]

        super().__init__(
            placeholder="Select an exchange pack...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        pack = self.values[0]

        if pack == "Starter Exchange":
            embed = discord.Embed(
                title = f"💎 {self.values[0]}",
                description = "**Cost**\n"
"💎 100\n\n"
"**Receive**\n"
"🪙 7000\n\n"
"**Bonus**\n"
"✨ 1000\n\n",
                color = discord.Color.blue()
            )
            await interaction.response.edit_message(
                embed = embed,
                view = GemPackView(100, 7000)
            )
        if pack == "Rookie Exchange":
            embed = discord.Embed(
                title = f"🔷 {self.values[0]}",
                description = "**Cost**\n"
"💎 250\n\n"
"**Recieve**\n"
"🪙 15000\n\n"
"**Bonus**\n"
"✨ 2000\n\n",
                color = discord.Color.blue()
            )
            await interaction.response.edit_message(
                embed = embed,
                view = GemPackView(250, 15000)
            )
        if pack == "Pro Exchange":
            embed = discord.Embed(
                title = f"🔹{self.values[0]}",
                description = "**Cost**\n"
"💎 800\n\n"
"**Recieve**\n"
"🪙 50000\n\n"
"**Bonus**\n"
"✨ 7500\n\n",
                color = discord.Color.blue()  
            )
            await interaction.response.edit_message(
                embed = embed,
                view = GemPackView(800, 50000)
            )
        if pack == "Elite Exchange":
                embed = discord.Embed(
                    title = f"💠{self.values[0]}",
                    description = "**Cost**\n"
"💎 2000\n\n"
"**Recieve**\n"
"🪙 150000\n\n"
"**Bonus**\n"
"✨ 25000\n\n",
                    color = discord.Color.blue()
                )
                await interaction.response.edit_message(
                    embed=embed,
                    view = GemPackView(2000, 150000)
                )
        if pack == "Ultimate Exchange":
                    embed = discord.Embed(
                        title = f"👑 {self.values[0]}",
                    description = "**Cost**\n"
"💎 4000\n\n"
"**Recieve**\n"
"🪙 300000\n\n"
"**Bonus**\n"
"✨ 50000\n\n",
                    color = discord.Color.blue()
                    )
                    await interaction.response.edit_message(
                    embed=embed,
                    view=GemPackView(4000, 300000)
)

class GemExchangeView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GemExchangeSelect())

class GemPackView(discord.ui.View):

    def __init__(self, cost, reward):
        super().__init__(timeout=None)

        self.cost = cost
        self.reward = reward

        purchase = discord.ui.Button(
            label="Purchase",
            emoji="✅",
            style=discord.ButtonStyle.green
        )

        back = discord.ui.Button(
            label="Back",
            emoji="⬅️",
            style=discord.ButtonStyle.secondary
        )

        purchase.callback = self.purchase_callback
        back.callback = self.back_callback

        self.add_item(purchase)
        self.add_item(back)

    async def purchase_callback(self, interaction: discord.Interaction):

        user_id = str(interaction.user.id)

        with open("users.json", "r") as f:
            data = json.load(f)

        # Create user if missing
        if user_id not in data:
            data[user_id] = {
                "coins": 0,
                "gems": 0,
                "lifetime_earned": 0,
                "lifetime_spent": 0
            }

        # Check gems
        if data[user_id]["gems"] < self.cost:
            await interaction.response.send_message(
                f"❌ You need **{self.cost}** 💎 Gems.\nYou only have **{data[user_id]['gems']}**.",
                ephemeral=True
            )
            return

        # Exchange
        data[user_id]["gems"] -= self.cost
        data[user_id]["coins"] += self.reward
        data[user_id]["lifetime_earned"] += self.reward
        data[user_id]["lifetime_spent"] += self.cost

        with open("users.json", "w") as f:
            json.dump(data, f, indent=4)

        embed = discord.Embed(
            title="✅ Exchange Successful",
            description=(
                f"Spent: 💎 **{self.cost}**\n"
                f"Received: 🪙 **{self.reward}**\n\n"
                f"Remaining Gems: 💎 **{data[user_id]['gems']}**\n"
                f"Current Coins: 🪙 **{data[user_id]['coins']}**"
            ),
            color=discord.Color.green()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

    async def back_callback(self, interaction: discord.Interaction):

        from views.gem_exchange import build_gem_exchange

        await interaction.response.edit_message(
            embed=build_gem_exchange(),
            view=GemExchangeView
        )