import discord
import json

from utils.emoji import COIN, GEM, CRATE, COMMON, RARE, EPIC, LEGENDARY, DAILY, BAG, LEVEL, XP, BOX, TROPHY, WALLET, EQUIPMENT, BAT_ITEM, BALL_ITEM, GLOVES, PADS, HELMET, SHOES


class InventoryView(discord.ui.View):

    def __init__(self, user):

        super().__init__(timeout=120)

        self.user = user
        self.owner_id = int(user["user_id"])

    @discord.ui.button(
        label="Economy",
        emoji="💰",
        style=discord.ButtonStyle.green
    )
    async def economy(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ This inventory isn't yours.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{WALLET} Economy",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Currency",
            value=(
                f"{COIN} Coins: **{self.user['coins']:,}**\n"
                f"{GEM} Gems: **{self.user['gems']}**"
            ),
            inline=False
        )

        embed.add_field(
            name="Lifetime",
            value=(
                f"📈 Earned: **{self.user['lifetime_earned']:,}**\n"
                f"📉 Spent: **{self.user['lifetime_spent']:,}**"
            ),
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="Crates",
        emoji="📦",
        style=discord.ButtonStyle.blurple
    )
    async def crates(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ This inventory isn't yours.",
                ephemeral=True
            )
            return

        crates = json.loads(self.user["crates"])

        embed = discord.Embed(
            title=f"{CRATE} Crates",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Owned Crates",
            value=(
                f"{COMMON} Common : **{crates['common']}**\n"
                f"{RARE} Rare : **{crates['rare']}**\n"
                f"{EPIC} Epic : **{crates['epic']}**\n"
                f"{LEGENDARY} Legendary : **{crates['legendary']}**"
            ),
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="Stats",
        emoji="📊",
        style=discord.ButtonStyle.gray,
        row=1
    )
    async def stats(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ This inventory isn't yours.",
                ephemeral=True
            )
            return

        cards = json.loads(self.user["cards"])

        embed = discord.Embed(
            title="📊 Inventory Stats",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Collection",
            value=(
                f"{BAG} Players: **{len(cards)} / 25**\n"
                f"{DAILY} Daily Streak: **{self.user['daily_streak']}**"
            ),
            inline=False
        )

        embed.add_field(
            name="Progress",
            value=(
                f"{LEVEL} Level: **{self.user['level']}**\n"
                f"{XP} XP: **{self.user['xp']}**\n"
                f"{TROPHY} Trophies: **{self.user['trophies']}**"
            ),
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="Items",
        emoji="🎁",
        style=discord.ButtonStyle.green,
        row=1
    )
    async def items(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ This inventory isn't yours.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{BOX} Items",
            description=(
                "🚧 **Coming Soon!**\n\n"
                "This section will contain:\n"
                "• Luck Potions\n"
                "• Rename Tickets\n"
                "• Team Rename Tickets\n"
                "• Event Tokens\n"
                "• Keys\n"
                "• Passes"
            ),
            color=discord.Color.gold()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="Equipment",
        emoji="🏏",
        style=discord.ButtonStyle.red,
        row=1
    )
    async def equipment(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ This inventory isn't yours.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{EQUIPMENT} Equipment",
            description=(
                "🚧 **Coming Soon!**\n\n"
                f"{BAT_ITEM} Cricket Bats\n"
                f"{BALL_ITEM} Cricket Balls\n"
                f"{GLOVES} Gloves\n"
                f"{PADS} Pads\n"
                f"{HELMET} Helmets\n"
                f"{SHOES} Shoes\n\n"
                "Equipment system is under development."
            ),
            color=discord.Color.red()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )
        