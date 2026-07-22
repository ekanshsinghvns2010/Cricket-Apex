import os
import discord
from discord.ext import commands

from database import connect_db


# ============================================================
# PLAYER LOOKUP
# ============================================================

def find_player(identifier):
    """
    Finds a player by player ID or player name.
    """

    conn = connect_db()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM players
            WHERE id = ?
               OR LOWER(name) = LOWER(?)
               OR LOWER(display_name) = LOWER(?)
            """,
            (identifier, identifier, identifier)
        )

        row = cursor.fetchone()

        if row:
            return dict(row)

        return None

    finally:
        conn.close()


# ============================================================
# GET USER'S OWNED PLAYER IDS
# ============================================================

def get_owned_player_ids(user_id):

    conn = connect_db()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT cards
            FROM users
            WHERE user_id = ?
            """,
            (str(user_id),)
        )

        user = cursor.fetchone()

        if user is None:
            return []

        raw_cards = user["cards"]

        if not raw_cards:
            return []

        import json

        try:
            cards = json.loads(raw_cards)
        except (json.JSONDecodeError, TypeError):
            return []

        if not isinstance(cards, list):
            return []

        return cards

    finally:
        conn.close()


# ============================================================
# CHECK OWNERSHIP
# ============================================================

def user_owns_player(user_id, player_id):

    owned_ids = get_owned_player_ids(user_id)

    return str(player_id) in [str(x) for x in owned_ids]


# ============================================================
# DISPLAY HELPERS
# ============================================================

def fmt(value):
    """
    Returns '—' for missing/None data, otherwise the value as-is.
    Used for any stat whose source column doesn't exist yet.
    """
    if value is None:
        return "—"
    return value


def row(label, value, width=13):
    """
    Builds one aligned line for the monospace stat table.
    """
    return f"{label:<{width}}{fmt(value)}"


RARITY_COLORS = {
    "Common": discord.Color.light_grey(),
    "Rare": discord.Color.blue(),
    "Epic": discord.Color.purple(),
    "Legendary": discord.Color.gold(),
    "Icon": discord.Color.red()
}


# ============================================================
# BATTING STATS
# ============================================================

def calculate_batting_stats(player):

    matches = player.get("matches") or 0
    runs = player.get("runs") or 0

    # NOTE: the following columns do not currently exist in the
    # `players` table. Add them to enable real calculations instead
    # of the "—" placeholder / documented fallback below.
    innings = player.get("innings")          # requires: innings
    balls_faced = player.get("balls_faced")  # requires: balls_faced
    fours = player.get("fours")              # requires: fours
    sixes = player.get("sixes")              # requires: sixes
    fifties = player.get("fifties")          # requires: fifties
    hundreds = player.get("hundreds")        # requires: hundreds
    highest_score = player.get("highest_score")  # requires: highest_score
    highest_score_not_out = player.get("highest_score_not_out")  # requires: highest_score_not_out (bool)
    not_outs = player.get("not_outs")        # requires: not_outs
    outs = player.get("outs")                # requires: outs (dismissals)
    ducks = player.get("ducks")              # requires: ducks
    potm = player.get("player_of_match")     # requires: player_of_match

    # Batting average: prefer runs/outs (real dismissals) when available.
    # Falls back to runs/matches ONLY because this database has no
    # innings/dismissals data yet, per design requirement.
    if outs:
        batting_average = round(runs / outs, 2)
    elif matches > 0:
        batting_average = round(runs / matches, 2)
    else:
        batting_average = 0

    # Strike rate needs balls_faced, which isn't stored yet.
    if balls_faced:
        strike_rate = round((runs / balls_faced) * 100, 2)
    else:
        strike_rate = None

    # Highest score display, e.g. "157*"
    if highest_score is not None:
        hs_display = f"{highest_score}*" if highest_score_not_out else str(highest_score)
    else:
        hs_display = None

    return {
        "matches": matches,
        "innings": innings,
        "runs": runs,
        "balls_faced": balls_faced,
        "average": batting_average,
        "strike_rate": strike_rate,
        "fours": fours,
        "sixes": sixes,
        "fifties": fifties,
        "hundreds": hundreds,
        "highest_score": hs_display,
        "not_outs": not_outs,
        "outs": outs,
        "ducks": ducks,
        "potm": potm
    }


def build_batting_table(player):

    s = calculate_batting_stats(player)

    lines = [
        row("Matches", s["matches"]),
        row("Innings", s["innings"]),
        row("Runs", s["runs"]),
        row("Balls Faced", s["balls_faced"]),
        row("Average", s["average"]),
        row("Strike Rate", s["strike_rate"]),
        row("4s", s["fours"]),
        row("6s", s["sixes"]),
        row("50s", s["fifties"]),
        row("100s", s["hundreds"]),
        row("Highest Score", s["highest_score"]),
        row("Not Outs", s["not_outs"]),
        row("Outs", s["outs"]),
        row("Ducks", s["ducks"]),
        row("POTM", s["potm"]),
    ]

    return "```\n" + "\n".join(lines) + "\n```"


# ============================================================
# BOWLING STATS
# ============================================================

def calculate_bowling_stats(player):

    matches = player.get("matches") or 0
    wickets = player.get("wickets") or 0

    # NOTE: none of the following exist in the `players` table yet.
    innings = player.get("innings")                # requires: innings
    overs = player.get("overs")                     # requires: overs (or balls_bowled)
    balls_bowled = player.get("balls_bowled")        # requires: balls_bowled
    runs_conceded = player.get("runs_conceded")      # requires: runs_conceded
    maidens = player.get("maidens")                  # requires: maidens
    four_wicket_hauls = player.get("four_wicket_hauls")  # requires: four_wicket_hauls
    five_wicket_hauls = player.get("five_wicket_hauls")  # requires: five_wicket_hauls
    best_bowling = player.get("best_bowling")        # requires: best_bowling (e.g. "5/24")
    dot_balls = player.get("dot_balls")              # requires: dot_balls
    no_balls = player.get("no_balls")                # requires: no_balls
    wides = player.get("wides")                      # requires: wides

    # Prefer balls_bowled for overs if overs isn't stored directly.
    effective_overs = overs
    if effective_overs is None and balls_bowled:
        effective_overs = round(balls_bowled / 6, 1)

    if runs_conceded is not None and wickets:
        bowling_average = round(runs_conceded / wickets, 2)
    else:
        bowling_average = None

    if runs_conceded is not None and effective_overs:
        economy = round(runs_conceded / effective_overs, 2)
    else:
        economy = None

    if balls_bowled is not None and wickets:
        bowling_strike_rate = round(balls_bowled / wickets, 2)
    else:
        bowling_strike_rate = None

    return {
        "matches": matches,
        "innings": innings,
        "overs": effective_overs,
        "balls_bowled": balls_bowled,
        "runs_conceded": runs_conceded,
        "wickets": wickets,
        "average": bowling_average,
        "economy": economy,
        "strike_rate": bowling_strike_rate,
        "maidens": maidens,
        "four_wicket_hauls": four_wicket_hauls,
        "five_wicket_hauls": five_wicket_hauls,
        "best_bowling": best_bowling,
        "dot_balls": dot_balls,
        "no_balls": no_balls,
        "wides": wides
    }


def build_bowling_table(player):

    s = calculate_bowling_stats(player)

    lines = [
        row("Matches", s["matches"]),
        row("Innings", s["innings"]),
        row("Overs", s["overs"]),
        row("Balls Bowled", s["balls_bowled"]),
        row("Runs Conceded", s["runs_conceded"]),
        row("Wickets", s["wickets"]),
        row("Average", s["average"]),
        row("Economy", s["economy"]),
        row("Strike Rate", s["strike_rate"]),
        row("Maidens", s["maidens"]),
        row("4-Wkt Hauls", s["four_wicket_hauls"]),
        row("5-Wkt Hauls", s["five_wicket_hauls"]),
        row("Best Bowling", s["best_bowling"]),
        row("Dot Balls", s["dot_balls"]),
        row("No Balls", s["no_balls"]),
        row("Wides", s["wides"]),
    ]

    return "```\n" + "\n".join(lines) + "\n```"


# ============================================================
# OTHER STATS
# ============================================================

def build_other_stats_embed(player):

    matches = player.get("matches") or 0
    catches = player.get("catches") or 0

    # NOTE: not currently stored — requires: run_outs, stumpings, player_of_match
    run_outs = player.get("run_outs")
    stumpings = player.get("stumpings")
    potm = player.get("player_of_match")

    embed = discord.Embed(
        title="📊 OTHER STATS",
        color=discord.Color.blue()
    )

    embed.description = (
        "```\n"
        + "\n".join([
            row("Catches", catches),
            row("Run-Outs", run_outs),
            row("Stumpings", stumpings),
            row("POTM Awards", potm),
            row("Appearances", matches),
        ])
        + "\n```"
    )

    return embed


# ============================================================
# SKILLS (placeholder — no skill system table exists yet)
# ============================================================

def get_equipped_skills(player):
    # NOTE: requires a `skills` table / column linking skills to a
    # player's card instance. Returns [] until that system exists.
    return []


def build_skills_embed(player):

    skills = get_equipped_skills(player)

    embed = discord.Embed(
        title="✨ MANAGE SKILLS",
        color=discord.Color.blue()
    )

    if skills:
        embed.description = "\n".join(f"• {s}" for s in skills)
    else:
        embed.description = (
            "🔻 No skills equipped\n\n"
            "Skill management isn't connected yet — this menu is "
            "ready to be wired up once the skill system exists."
        )

    return embed


# ============================================================
# NEWS (placeholder — no news system exists yet)
# ============================================================

def build_news_embed(player):

    embed = discord.Embed(
        title="📰 PLAYER NEWS",
        description="No recent news available for this player.",
        color=discord.Color.blue()
    )

    return embed


# ============================================================
# CARD IMAGE
# ============================================================

def get_card_image(player):
    """
    Returns (image_reference, discord.File_or_None).
    Supports either a full URL or a local file path, stored under
    either 'image' or 'image_url' — whichever column exists.
    """

    value = player.get("image") or player.get("image_url")

    if not value:
        return None, None

    if value.startswith("http://") or value.startswith("https://"):
        return value, None

    if os.path.isfile(value):
        filename = os.path.basename(value)
        file = discord.File(value, filename=filename)
        return f"attachment://{filename}", file

    return None, None


# ============================================================
# MAIN STATS PANEL
# ============================================================

def build_main_embed(player, target_user, mode="batting"):

    rarity = player.get("rarity", "Common")
    color = RARITY_COLORS.get(rarity, discord.Color.blue())

    skills = get_equipped_skills(player)
    skills_text = (
        "\n".join(f"• {s}" for s in skills)
        if skills
        else "🔻 No skills equipped"
    )

    stats_table = (
        build_batting_table(player)
        if mode == "batting"
        else build_bowling_table(player)
    )

    embed = discord.Embed(
        title=f"🏏 {player['display_name']}",
        description=(
            f"⭐ OVR **{fmt(player.get('ovr'))}** • {rarity}\n"
            f"👤 Owned by **{target_user.display_name}**"
        ),
        color=color
    )

    embed.add_field(
        name="PLAYER SKILLS",
        value=skills_text,
        inline=False
    )

    embed.add_field(
        name=f"PLAYER STATS — {'Batting' if mode == 'batting' else 'Bowling'}",
        value=stats_table,
        inline=False
    )

    image_ref, file = get_card_image(player)

    if image_ref:
        embed.set_image(url=image_ref)

    embed.set_footer(text="Cricket Apex • Career Statistics")

    return embed, file


# ============================================================
# DROPDOWN
# ============================================================

class StatsDropdown(discord.ui.Select):

    def __init__(self, player):

        options = [
            discord.SelectOption(
                label="Manage Skills", emoji="✨", value="manage_skills"
            ),
            discord.SelectOption(
                label="Player News", emoji="📰", value="player_news"
            ),
            discord.SelectOption(
                label="Other Stats", emoji="📊", value="other_stats"
            ),
        ]

        super().__init__(
            placeholder="Select an option",
            min_values=1,
            max_values=1,
            options=options,
            row=1
        )

        self.player = player

    async def callback(self, interaction: discord.Interaction):

        choice = self.values[0]

        if choice == "manage_skills":
            embed = build_skills_embed(self.player)
        elif choice == "player_news":
            embed = build_news_embed(self.player)
        else:
            embed = build_other_stats_embed(self.player)

        # First (and only) response to this interaction — ephemeral so
        # it never touches/edits the main stats panel.
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ============================================================
# MAIN VIEW
# ============================================================

class StatsView(discord.ui.View):

    def __init__(self, player, target_user, mode="batting"):
        super().__init__(timeout=180)

        self.player = player
        self.target_user = target_user
        self.mode = mode

        self.add_item(StatsDropdown(player))

    async def refresh(self, interaction: discord.Interaction):

        embed, file = build_main_embed(self.player, self.target_user, self.mode)

        if file:
            await interaction.response.edit_message(
                embed=embed, attachments=[file], view=self
            )
        else:
            await interaction.response.edit_message(
                embed=embed, attachments=[], view=self
            )

    @discord.ui.button(
        label="Batting Stats",
        emoji="🪶",
        style=discord.ButtonStyle.green,
        row=0
    )
    async def batting_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "batting"
        await self.refresh(interaction)

    @discord.ui.button(
        label="Bowling Stats",
        emoji="🔴",
        style=discord.ButtonStyle.red,
        row=0
    )
    async def bowling_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "bowling"
        await self.refresh(interaction)


# ============================================================
# SETUP COMMANDS
# ============================================================

def setup_stats(bot):

    @bot.command(
        name="stats",
        aliases=["show", "pi"]
    )
    async def stats(ctx, *args):

        # ----------------------------------------------------
        # NO PLAYER NAME
        # ----------------------------------------------------

        if not args:

            await ctx.send(
                "❌ Please specify a player.\n\n"
                "Examples:\n"
                "`g!stats Virat Kohli`\n"
                "`g!stats @User Virat Kohli`\n"
                "`g!stats Virat Kohli @User`"
            )

            return

        # ----------------------------------------------------
        # DETERMINE TARGET USER
        # ----------------------------------------------------

        target_user = ctx.author

        remaining_args = list(args)

        # First check mentions
        if ctx.message.mentions:

            mentioned_user = ctx.message.mentions[0]

            target_user = mentioned_user

            cleaned_args = []

            for arg in remaining_args:

                if not arg.startswith("<@"):
                    cleaned_args.append(arg)

            remaining_args = cleaned_args

        # ----------------------------------------------------
        # REPLY TARGET
        # ----------------------------------------------------

        elif ctx.message.reference:

            try:

                replied_message = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )

                target_user = replied_message.author

            except discord.HTTPException:

                pass

        # ----------------------------------------------------
        # PLAYER NAME
        # ----------------------------------------------------

        player_identifier = " ".join(remaining_args).strip()

        if not player_identifier:

            await ctx.send(
                "❌ Please specify a player name."
            )

            return

        # ----------------------------------------------------
        # FIND PLAYER
        # ----------------------------------------------------

        player = find_player(player_identifier)

        if player is None:

            await ctx.send(
                f"❌ Player **{player_identifier}** not found."
            )

            return

        # ----------------------------------------------------
        # CHECK OWNERSHIP
        # ----------------------------------------------------

        if not user_owns_player(
            target_user.id,
            player["id"]
        ):

            await ctx.send(
                "❌ Player not found in your collection."
            )

            return

        # ----------------------------------------------------
        # BUILD MAIN PANEL
        # ----------------------------------------------------

        embed, file = build_main_embed(player, target_user, mode="batting")
        view = StatsView(player, target_user, mode="batting")

        if file:
            await ctx.send(embed=embed, file=file, view=view)
        else:
            await ctx.send(embed=embed, view=view)
            