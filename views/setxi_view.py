import discord

# NOTE: The 25-card collection cap is enforced elsewhere (see the
# reusable card-limit helper used by buy/open/reward commands). This
# file only handles Playing XI selection UI.

MAX_SELECT_OPTIONS = 25


def build_player_option(player):
    """
    Builds a single discord.SelectOption for a player.
    Kept as a standalone function so future pagination logic
    can reuse it without touching RoleSelect internals.
    """
    country = player.get("country", "Unknown")
    ovr = player.get("ovr", 0)
    batting_ovr = player.get("batting_ovr", 0)
    bowling_ovr = player.get("bowling_ovr", 0)

    description = f"🌍 {country} • ⭐ {ovr} • 🏏 {batting_ovr} • 🎯 {bowling_ovr}"

    return discord.SelectOption(
        label=player["name"],
        description=description,
        value=player["id"]
    )


def build_role_options(players, page=0, page_size=MAX_SELECT_OPTIONS):
    """
    Returns the SelectOptions for a given page of players.

    Currently always called with page=0 (single-page behavior), but the
    signature already supports pagination so a future page-switch button
    can call this with page=page+1 without changing this function.
    """
    start = page * page_size
    end = start + page_size
    page_players = players[start:end]

    return [build_player_option(p) for p in page_players]


def role_page_count(players, page_size=MAX_SELECT_OPTIONS):
    """
    Returns how many pages a role's player list would need.
    Not used yet (single-page behavior), but ready for future pagination
    controls (e.g. enabling/disabling next/previous buttons).
    """
    if not players:
        return 1
    return -(-len(players) // page_size)  # ceil division


class RoleSelect(discord.ui.Select):

    def __init__(self, role_label, role_key, players, min_select, max_select, row, page=0):
        self.role_key = role_key
        self.role_label = role_label
        self.players = players
        self.min_select = min_select
        self.max_select = max_select
        self.page = page

        options = build_role_options(players, page=page)

        super().__init__(
            placeholder=f"Select {role_label} ({min_select}-{max_select})",
            min_values=min_select if options else 0,
            max_values=min(max_select, len(options)) if options else 0,
            options=options if options else [
                discord.SelectOption(label="No players available", value="none", default=False)
            ],
            disabled=not options,
            row=row
        )

    async def callback(self, interaction: discord.Interaction):
        view: "SetXIView" = self.view

        if not await view.authorize(interaction):
            return

        view.selections[self.role_key] = list(self.values)

        await interaction.response.defer()


class ConfirmButton(discord.ui.Button):

    def __init__(self, row):
        super().__init__(
            label="Confirm",
            style=discord.ButtonStyle.green,
            row=row
        )

    async def callback(self, interaction: discord.Interaction):
        view: "SetXIView" = self.view

        if not await view.authorize(interaction):
            return

        is_valid, error_message = view.validate_selections()

        if not is_valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        view.selected_ids = view.combined_selection()

        await view.finalize(interaction, "✅ Playing XI confirmed.")


class CancelButton(discord.ui.Button):

    def __init__(self, row):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.red,
            row=row
        )

    async def callback(self, interaction: discord.Interaction):
        view: "SetXIView" = self.view

        if not await view.authorize(interaction):
            return

        view.selected_ids = None

        await view.finalize(interaction, "❌ Playing XI selection cancelled.")


class SetXIView(discord.ui.View):

    ROLE_RULES = {
        "WK": (1, 2, "Wicket Keepers"),
        "BAT": (3, 6, "Batters"),
        "AR": (1, 4, "All-Rounders"),
        "BOWL": (3, 6, "Bowlers"),
    }

    def __init__(self, user, owned_players, timeout=180):
        super().__init__(timeout=timeout)

        self.user = user
        self.owned_players = owned_players
        self.selected_ids = None
        self.message = None  # optionally set by the caller for timeout edits

        self.selections = {role: [] for role in self.ROLE_RULES}

        players_by_role = self._group_by_role(owned_players)

        for row, (role_key, (min_select, max_select, role_label)) in enumerate(self.ROLE_RULES.items()):
            self.add_item(
                RoleSelect(
                    role_label,
                    role_key,
                    players_by_role.get(role_key, []),
                    min_select,
                    max_select,
                    row=row
                )
            )

        self.add_item(ConfirmButton(row=4))
        self.add_item(CancelButton(row=4))

    def _group_by_role(self, players):
        grouped = {role: [] for role in self.ROLE_RULES}
        for p in players:
            role = p.get("role")
            if role in grouped:
                grouped[role].append(p)
        return grouped

    def combined_selection(self):
        combined = []
        for role in self.ROLE_RULES:
            combined.extend(self.selections.get(role, []))
        return combined

    def validate_selections(self):
        """
        Validates role counts, exact total of 11, and duplicates.
        Returns (True, None) if valid, otherwise (False, error_message).
        """
        for role_key, (min_select, max_select, role_label) in self.ROLE_RULES.items():
            count = len(self.selections.get(role_key, []))
            if not (min_select <= count <= max_select):
                return False, f"❌ You must select {min_select}–{max_select} {role_label}."

        combined = self.combined_selection()

        if len(combined) != 11:
            return False, f"❌ You must select exactly 11 players. You selected {len(combined)}."

        if len(set(combined)) != len(combined):
            return False, "❌ Duplicate players detected across selections."

        return True, None

    def disable_all(self):
        for child in self.children:
            child.disabled = True

    async def finalize(self, interaction: discord.Interaction, content: str):
        """
        Shared finish-up logic for Confirm and Cancel: disables all
        components, edits the message, and stops the view.
        """
        self.disable_all()

        await interaction.response.edit_message(content=content, view=self)

        self.stop()

    async def authorize(self, interaction: discord.Interaction) -> bool:
        """
        Shared authorization check used by every component callback
        as well as interaction_check.
        """
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "❌ You are not allowed to interact with this menu.", ephemeral=True
            )
            return False
        return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.authorize(interaction)

    async def on_timeout(self):
        self.disable_all()

        if self.message is not None:
            try:
                await self.message.edit(content="⌛ Playing XI selection timed out.", view=self)
            except discord.HTTPException:
                pass

        self.stop()
        