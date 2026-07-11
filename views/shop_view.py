import discord

from utils.emoji import COIN, GEM, CRATE, PASS, EQUIPMENT
from views.coin_shop import build_coins_shop
from views.coin_shop_view import CoinsShopView
from views.coin_exchange import build_coin_exchange
from views.coin_exchange_view import CoinExchangeView


class ShopCategorySelect(discord.ui.Select):

    def __init__(self):

        options = [
            discord.SelectOption(
                label="Coins",
                emoji=COIN,
                description="Buy coins or exchange them for gems"
            ),
            discord.SelectOption(
                label="Gems",
                emoji=GEM,
                description="Buy gems or exchange them for coins"
            ),
            discord.SelectOption(
                label="Passes",
                emoji=PASS,
                description="Buy a pass to unlock special perks"
            ),
            discord.SelectOption(
                label="Crates",
                emoji=CRATE,
                description="Open crates for exciting rewards"
            ),
            discord.SelectOption(
                label="Equipment (Coming Soon)",
                emoji=EQUIPMENT,
                description="Under Construction"
            )
        ]

        super().__init__(
            placeholder="Select a shop category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        # Coins Shop
        if self.values[0] == "Coins":
            await interaction.response.edit_message(
                embed=build_coins_shop(),
                view=CoinsShopView()
            )
            return
        # Gems Shop
        if self.values[0] == "Gems":
            await interaction.response.edit_message(
                embed=build_coin_exchange(),
                view=CoinExchangeView()
            )
            return

        # Placeholder for other categories
        embed = discord.Embed(
            title=f"🛒 {self.values[0]} Shop",
            description=(
                f"Welcome to the **{self.values[0]}** category!\n\n"
                "Items will be added here soon."
            ),
            color=discord.Color.green()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=BackView()
        )


class BackButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Back",
            emoji="⬅️",
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🛒 Cricket 11 Shop",
            description=(
                "Welcome to the Cricket 11 Shop!\n\n"
                "Buy passes, gems, coins, crates and much more.\n\n"
                "Select a category below."
            ),
            color=discord.Color.green()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=ShopView()
        )


class ShopView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ShopCategorySelect())


class BackView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BackButton())