import discord
import json

class CoinExchangeSelect(discord.ui.Select):

    def __init__(self):

        options = [
            discord.SelectOption(
                label="Small Pack",
                emoji="🪙",
                description="Entry level exchange"
            ),
            discord.SelectOption(
                label="Medium Pack",
                emoji="💴",
                description="Better value"
            ),
            discord.SelectOption(
                label="Large Pack",
                emoji="💶",
                description="Popular choice"
            ),
            discord.SelectOption(
                label="Epic Pack",
                emoji="💷",
                description="High value exchange"
            ),
            discord.SelectOption(
                label="Legendary Pack",
                emoji="💰",
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

        if pack == "Small Pack":
            embed = discord.Embed(
                title = f"🪙 {self.values[0]}",
                description = "**Cost**\n"
"🪙 20000\n\n"
"**Receive**\n"
"💎 100\n\n"
"**Bonus**\n"
"✨ 70\n\n",
                color = discord.Color.blue()
            )
            await interaction.response.edit_message(
                embed = embed,
                view = CoinPackView(20000, 170)
            )
        if pack == "Medium Pack":
            embed = discord.Embed(
                title = f"💴 {self.values[0]}",
                description = "**Cost**\n"
"🪙 55000\n\n"
"**Recieve**\n"
"💎 250\n\n"
"**Bonus**\n"
"✨ 150\n\n",
                color = discord.Color.blue()
            )
            await interaction.response.edit_message(
                embed = embed,
                view = CoinPackView(55000, 400)
            )
        if pack == "Large Pack":
            embed = discord.Embed(
                title = f"💶 {self.values[0]}",
                description = "**Cost**\n"
"🪙 500000\n\n"
"**Recieve**\n"
"💎 800\n\n"
"**Bonus**\n"
"✨ 350\n\n",
                color = discord.Color.blue()  
            )
            await interaction.response.edit_message(
                embed = embed,
                view = CoinPackView(500000, 1150)
            )
        if pack == "Epic Pack":
                embed = discord.Embed(
                    title = f"💷 {self.values[0]}",
                    description = "**Cost**\n"
"🪙 2000000\n\n"
"**Recieve**\n"
"💎 2799\n\n"
"**Bonus**\n"
"✨ 289\n\n",
                    color = discord.Color.blue()
                )
                await interaction.response.edit_message(
                    embed=embed,
                    view = CoinPackView(2000000, 3088)
                )
        if pack == "Legendary Pack":
                    embed = discord.Embed(
                        title = f"💰 {self.values[0]}",
                    description = "**Cost**\n"
"🪙 5000000\n\n"
"**Recieve**\n"
"💎 4899\n\n"
"**Bonus**\n"
"✨ 489\n\n",
                    color = discord.Color.blue()
                    )
                    await interaction.response.edit_message(
                    embed=embed,
                    view=CoinPackView(5000000, 5288)
)

class CoinExchangeView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CoinExchangeSelect())

class CoinPackView(discord.ui.View):

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
        if data[user_id]["coins"] < self.cost:
            await interaction.response.send_message(
                f"❌ You need **{self.cost}** 🪙 Coins.\nYou only have **{data[user_id]['coins']}**.",
                ephemeral=True
            )
            return

        # Exchange
        data[user_id]["coins"] -= self.cost
        data[user_id]["gems"] += self.reward
        data[user_id]["lifetime_earned"] += self.reward
        data[user_id]["lifetime_spent"] += self.cost

        with open("users.json", "w") as f:
            json.dump(data, f, indent=4)

        embed = discord.Embed(
            title="✅ Exchange Successful",
            description=(
                f"Spent: 🪙 **{self.cost}**\n"
                f"Received: 💎 **{self.reward}**\n\n"
                f"Remaining Coins: 🪙 **{data[user_id]['coins']}**\n"
                f"Current Gems: 💎 **{data[user_id]['gems']}**"
            ),
            color=discord.Color.green()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

    async def back_callback(self, interaction: discord.Interaction):

        from views.coin_exchange import build_coin_exchange

        await interaction.response.edit_message(
            embed=build_coin_exchange(),
            view=CoinExchangeView()
        )