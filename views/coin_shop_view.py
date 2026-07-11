import discord
from utils.emoji import GEM
from views.gem_exchange import build_gem_exchange
from views.gem_exchange_view import GemExchangeView

class CoinsMethodSelect(discord.ui.Select):

    def __init__(self):

        options = [
            discord.SelectOption(
                label="Gem Exchange",
                emoji=GEM,
                description="Exchange Gems for Coins"
            ),
            discord.SelectOption(
                label="Coin Store",
                emoji="💳",
                description="Purchase Coins using real money"
            )
        ]

        super().__init__(
            placeholder="Choose a purchase method...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        if self.values[0] == "Gem Exchange":
            await interaction.response.edit_message(
                embed=build_gem_exchange(),
                view=GemExchangeView() 
            )
            return
            if self.values[0] == "Coin Store":
                embed = discord.Embed(
                    title = "💳 Coin Store",
                    description = "Purchase Coins using real money",
                    color = discord.Color.gold()
                )
                await interaction.response.edit_message(
                    embed = embed,
                    view =None
                )
                return


class CoinsShopView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CoinsMethodSelect())