import discord
import json
import logging

from database import connect_db
from utils.logger import log_action

# NOTE: Player data is already loaded from SQLite by the caller and
# passed into this view as a plain dict (BuyView(player, buyer)). This
# file now also reads/writes the user's wallet and card collection
# directly in SQLite (the `users` table) instead of users.json.

logger = logging.getLogger(__name__)


def get_user(user_id):
    """
    Fetches a single user's row from the users table.

    Returns:
        sqlite3.Row | None: the user's row, or None if no profile exists.
    """
    conn = connect_db()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
        return cursor.fetchone()
    finally:
        conn.close()


def load_cards(user):
    """
    Parses the JSON-encoded `cards` column from a users row into a
    Python list. Falls back to an empty list if the value is missing
    or corrupted, so a bad row never crashes a purchase.
    """
    raw_cards = user["cards"] if user["cards"] is not None else "[]"

    try:
        cards = json.loads(raw_cards)
    except json.JSONDecodeError:
        logger.exception("Corrupted cards JSON for user %s; treating as empty.", user["user_id"])
        return []

    if not isinstance(cards, list):
        return []

    return cards


def update_user_purchase(user_id, coins, lifetime_spent, cards):
    """
    Persists the result of a purchase: new coin balance, new
    lifetime_spent total, and the updated cards list (JSON-encoded).
    """
    conn = connect_db()

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET coins = ?, lifetime_spent = ?, cards = ? WHERE user_id = ?",
            (coins, lifetime_spent, json.dumps(cards), str(user_id))
        )
        conn.commit()
    finally:
        conn.close()


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

        user = get_user(user_id)

        if user is None:
            return False, "❌ You don't have a profile yet."

        cards = load_cards(user)

        coins = user["coins"] if user["coins"] is not None else 0
        lifetime_spent = user["lifetime_spent"] if user["lifetime_spent"] is not None else 0

        player_id = self.player.get("id")
        price = self.player.get("price", 0)

        if player_id in cards:
            return False, "❌ You already own this player."

        if len(cards) >= self.MAX_CARDS:
            return False, (
                f"❌ Your collection is full ({len(cards)}/{self.MAX_CARDS}). "
                "Sell cards or free up space before buying another player."
            )

        if coins < price:
            return False, (
                f"❌ You don't have enough coins. This player costs {price:,}, "
                f"but you only have {coins:,}."
            )

        coins -= price
        lifetime_spent += price
        cards.append(player_id)

        update_user_purchase(user_id, coins, lifetime_spent, cards)

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
        