import discord
import json
import logging
import os
from utils.logger import log_action
# NOTE: Player data is already loaded from SQLite by the caller and
# passed into this view as a plain dict (BuyView(player, buyer)). This
# file does not query the database directly — it only reads/writes the
# user's wallet and card collection in users.json.

USERS_FILE = "users.json"

logger = logging.getLogger(__name__)


def load_users():
    """
    Loads users.json, creating it if missing. Returns a dict.

    Raises:
        OSError: if the file cannot be read/created due to I/O issues.
    """
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f, indent=4)

    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.exception("users.json is corrupted; treating it as empty.")
        return {}


def save_users(users):
    """Saves the given users dict back to users.json."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def ensure_profile_defaults(profile):
    """
    Ensures a user profile has the fields this view depends on.
    Mutates and returns the profile dict.
    """
    if "cards" not in profile or not isinstance(profile["cards"], list):
        profile["cards"] = []

    if "playing_xi" not in profile or not isinstance(profile["playing_xi"], list):
        profile["playing_xi"] = []

    if "substitutes" not in profile or not isinstance(profile["substitutes"], list):
        profile["substitutes"] = []

    if "coins" not in profile or not isinstance(profile["coins"], (int, float)):
        profile["coins"] = 0

    if "lifetime_spent" not in profile or not isinstance(profile["lifetime_spent"], (int, float)):
        profile["lifetime_spent"] = 0

    return profile


class BuyButton(discord.ui.Button):

    def __init__(self):
        super().__init__(label="Buy", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        view: "BuyView" = self.view
        await view.handle_buy(interaction)


class CancelButton(discord.ui.Button):

    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        view: "BuyView" = self.view
        await view.handle_cancel(interaction)


class BuyView(discord.ui.View):

    MAX_CARDS = 25

    def __init__(self, player, buyer, timeout=60):
        super().__init__(timeout=timeout)

        self.player = player
        self.buyer = buyer
        self.buyer_id = buyer.id

        self.message = None  # optionally set by the caller for timeout edits

        self.add_item(BuyButton())
        self.add_item(CancelButton())

    def disable_all(self):
        for child in self.children:
            child.disabled = True

    async def authorize(self, interaction: discord.Interaction) -> bool:
        """Only the buyer this view was created for may use its buttons."""
        if interaction.user.id != self.buyer_id:
            await interaction.response.send_message(
                "❌ This purchase menu belongs to another user.", ephemeral=True
            )
            return False
        return True

    def _get_original_embed(self, interaction: discord.Interaction):
        """
        Returns a copy of the original message's first embed, or None
        if the message has no embed to preserve.
        """
        if interaction.message and interaction.message.embeds:
            return interaction.message.embeds[0].copy()
        return None

    async def _finalize(self, interaction: discord.Interaction, footer_text: str, content: str = None):
        """
        Shared finish-up logic for Buy/Cancel: preserves the original
        embed (only updating its footer), disables all components,
        edits the message, and stops the view.
        """
        embed = self._get_original_embed(interaction)

        if embed is not None:
            embed.set_footer(text=footer_text)

        self.disable_all()

        try:
            await interaction.response.edit_message(content=content, embed=embed, view=self)
        except discord.HTTPException:
            logger.exception("Failed to edit purchase message for user %s.", self.buyer_id)

        self.stop()

    async def handle_cancel(self, interaction: discord.Interaction):
        if not await self.authorize(interaction):
            return

        await self._finalize(interaction, footer_text="❌ Purchase cancelled.")

    async def handle_buy(self, interaction: discord.Interaction):
        if not await self.authorize(interaction):
            return

        try:
            success, error_message = self._process_purchase(interaction.user.id)
        except Exception:
            logger.exception("Unexpected error while processing purchase for user %s.", self.buyer_id)
            await interaction.response.send_message(
                "❌ Something went wrong while processing your purchase. Please try again.",
                ephemeral=True
            )
            return

        if not success:
            await interaction.response.send_message(error_message, ephemeral=True)
            return
            await log_action(
    bot=interaction.client,
    title="💰 Player Purchased",
    description=(
        f"**Player:** {self.player['name']}\n"
        f"**Price:** {self.player['price']:,} Coins"
    ),
    color=discord.Color.green(),
    user=interaction.user,
    guild=interaction.guild,
    channel=interaction.channel
)

        await self._finalize(
            interaction,
            footer_text="✅ Purchased successfully.",
            content="🎉 Purchase successful!"
        )

    def _process_purchase(self, user_id):
        """
        Performs all validation and the actual purchase.
        Returns (success: bool, error_message: str | None).
        """
        user_id = str(user_id)

        users = load_users()

        if user_id not in users:
            return False, "❌ You don't have a profile yet."

        profile = ensure_profile_defaults(users[user_id])

        player_id = self.player.get("id")
        price = self.player.get("price", 0)

        if player_id in profile["cards"]:
            return False, "❌ You already own this player."

        if len(profile["cards"]) >= self.MAX_CARDS:
            return False, (
                f"❌ Your collection is full ({len(profile['cards'])}/{self.MAX_CARDS}). "
                "Sell cards or free up space before buying another player."
            )

        if profile["coins"] < price:
            return False, (
                f"❌ You don't have enough coins. This player costs {price:,}, "
                f"but you only have {profile['coins']:,}."
            )

        profile["coins"] -= price
        profile["lifetime_spent"] += price
        profile["cards"].append(player_id)

        users[user_id] = profile
        save_users(users)

        return True, None

    async def on_timeout(self):
        self.disable_all()

        if self.message is not None:
            embed = self.message.embeds[0].copy() if self.message.embeds else None

            if embed is not None:
                embed.set_footer(text="⌛ Purchase expired.")

            try:
                await self.message.edit(embed=embed, view=self)
            except discord.HTTPException:
                logger.exception("Failed to edit purchase message on timeout for user %s.", self.buyer_id)

        self.stop()
        