
import discord

from utils.match_utils import load_matches, save_matches
from utils.match_engine import (
    bowling_variations,
    BOWLING_LENGTHS,
    BATTING_SHOTS,
    BATTING_INTENTS,
    delivery_result,
)


def get_match(match_id):
    return load_matches().get(str(match_id))


def overs_text(balls):
    balls = max(0, int(balls or 0))
    return f"{balls // 6}.{balls % 6}"


def team_label(team):
    return "🔴 Red Team" if team == "red" else "🔵 Blue Team"


def build_match_embed(match_id):
    match = get_match(match_id)

    if not match:
        return discord.Embed(
            title="Match not found",
            color=discord.Color.red(),
        )

    batting_team = match.get("batting_team", "red")
    bowling_team = match.get("bowling_team", "blue")
    runs = int(match.get("runs", 0))
    wickets = int(match.get("wickets", 0))
    balls = int(match.get("balls", 0))
    overs = int(match.get("overs", 5))
    target = match.get("target")

    embed = discord.Embed(
        title="🏏 CRICKET APEX • LIVE MATCH",
        description=(
            f"**{team_label(batting_team)}**\n"
            f"## {runs}/{wickets}\n"
            f"Overs: **{overs_text(balls)}/{overs}.0**\n"
            f"Target: **{target if target else '—'}**"
        ),
        color=discord.Color.gold(),
    )

    batters = match.get("batters", [])
    if batters:
        lines = []
        for index, player in enumerate(batters[:2]):
            marker = "🏏" if index == 0 else "　"
            lines.append(
                f"{marker} **{player.get('display_name', player.get('name', 'Batter'))}**"
                f" — {player.get('runs', 0)}"
                f" ({player.get('balls', 0)})"
            )
        embed.add_field(
            name="BATTERS",
            value="\n".join(lines),
            inline=False,
        )

    bowler = match.get("current_bowler")
    if bowler:
        embed.add_field(
            name="CURRENT BOWLER",
            value=(
                f"**{bowler.get('display_name', bowler.get('name', 'Bowler'))}**\n"
                f"{bowler.get('wickets', 0)} wickets • "
                f"{bowler.get('runs_conceded', 0)} runs"
            ),
            inline=False,
        )

    recent = match.get("recent_balls", [])
    embed.add_field(
        name="RECENT BALLS",
        value="  ".join(
            f"`{ball.get('display', ball.get('runs', 0))}`"
            for ball in recent[-12:]
        ) or "Waiting for first delivery...",
        inline=False,
    )

    embed.set_footer(
        text=f"Match {match_id} • Cricket Apex"
    )
    return embed


class MatchView(discord.ui.View):
    def __init__(self, match_id):
        super().__init__(timeout=300)
        self.match_id = str(match_id)

    def load(self):
        matches = load_matches()
        return matches, matches.get(self.match_id)

    async def refresh(self, interaction, match, content=None):
        embed = build_match_embed(self.match_id)
        view = MatchView(self.match_id)

        await interaction.response.edit_message(
            content=content or self.stage_text(match),
            embed=embed,
            view=view,
        )

    def stage_text(self, match):
        stage = match.get("interaction_stage", "variation")
        if stage == "variation":
            return "⚡ **Bowler's turn — choose a bowling variation.**"
        if stage == "length":
            return "🎯 **Choose the delivery length.**"
        if stage == "shot":
            return "🏏 **Batter's turn — choose a shot.**"
        if stage == "intent":
            return "🔥 **Choose your batting intent.**"
        return "🏏 Preparing the next delivery..."

    async def choose(self, interaction, category, value):
        matches, match = self.load()

        if not match or match.get("status") != "live":
            await interaction.response.send_message(
                "This match is not live.",
                ephemeral=True,
            )
            return

        stage = match.get("interaction_stage", "variation")

        if category == "variation":
            if stage != "variation":
                await interaction.response.send_message(
                    "That choice is no longer active.",
                    ephemeral=True,
                )
                return

            bowler = match.get("current_bowler") or {}
            options = bowling_variations(bowler)
            if value not in options:
                await interaction.response.send_message(
                    "That variation isn't available for this bowler.",
                    ephemeral=True,
                )
                return

            match["selected_variation"] = value
            match["interaction_stage"] = "length"

        elif category == "length":
            if stage != "length" or value not in BOWLING_LENGTHS:
                await interaction.response.send_message(
                    "That choice is no longer active.",
                    ephemeral=True,
                )
                return

            match["selected_length"] = value
            match["interaction_stage"] = "shot"

        elif category == "shot":
            if stage != "shot" or value not in BATTING_SHOTS:
                await interaction.response.send_message(
                    "That choice is no longer active.",
                    ephemeral=True,
                )
                return

            match["selected_shot"] = value
            match["interaction_stage"] = "intent"

        elif category == "intent":
            if stage != "intent" or value not in BATTING_INTENTS:
                await interaction.response.send_message(
                    "That choice is no longer active.",
                    ephemeral=True,
                )
                return

            match["selected_intent"] = value
            self.resolve_ball(match)
            match["interaction_stage"] = "variation"

        save_matches(matches)
        await self.refresh(interaction, match)

    def resolve_ball(self, match):
        batters = match.setdefault("batters", [])
        bowler = match.get("current_bowler") or {}

        if not batters:
            # Temporary fallback until the XI selection system is connected.
            batters.extend([
                {
                    "name": "Batter 1",
                    "display_name": "Batter 1",
                    "batting_ovr": 60,
                    "runs": 0,
                    "balls": 0,
                    "team": match.get("batting_team"),
                },
                {
                    "name": "Batter 2",
                    "display_name": "Batter 2",
                    "batting_ovr": 60,
                    "runs": 0,
                    "balls": 0,
                    "team": match.get("batting_team"),
                },
            ])

        if not bowler:
            bowler = {
                "name": "Bowler",
                "display_name": "Bowler",
                "bowling_ovr": 60,
                "fitness": 80,
                "wickets": 0,
                "runs_conceded": 0,
                "team": match.get("bowling_team"),
            }
            match["current_bowler"] = bowler

        striker = batters[0]

        result = delivery_result(
            striker,
            bowler,
            match.get("selected_variation", "Seam"),
            match.get("selected_length", "Good length"),
            match.get("selected_shot", "Defensive block"),
            match.get("selected_intent", "Balanced"),
            match.get("pitch", "Normal"),
        )

        runs = int(result.get("runs", 0))
        striker["runs"] = int(striker.get("runs", 0)) + runs

        if result.get("legal"):
            striker["balls"] = int(striker.get("balls", 0)) + 1
            match["balls"] = int(match.get("balls", 0)) + 1

        match["runs"] = int(match.get("runs", 0)) + runs
        bowler["runs_conceded"] = (
            int(bowler.get("runs_conceded", 0))
            + (0 if result.get("extra") == "wide" else runs)
        )

        if result.get("wicket"):
            match["wickets"] = int(match.get("wickets", 0)) + 1
            bowler["wickets"] = int(bowler.get("wickets", 0)) + 1

        if result.get("extra"):
            display = result["extra"].upper()
        elif result.get("wicket"):
            display = "W"
        else:
            display = str(runs)

        recent = match.setdefault("recent_balls", [])
        recent.append({
            "runs": runs,
            "display": display,
            "wicket": result.get("wicket", False),
            "extra": result.get("extra"),
            "description": result.get("description", ""),
        })
        match["recent_balls"] = recent[-24:]
        match["last_commentary"] = result.get("description", "")

        # Change striker after an odd number of runs.
        if runs % 2 == 1 and len(batters) >= 2:
            batters[0], batters[1] = batters[1], batters[0]

        # Swap ends at the end of a completed over.
        if result.get("legal") and match["balls"] % 6 == 0:
            if len(batters) >= 2:
                batters[0], batters[1] = batters[1], batters[0]

        overs_limit = int(match.get("overs", 5))
        if (
            match["wickets"] >= 10
            or match["balls"] >= overs_limit * 6
        ):
            match["status"] = "completed"
            match["state"] = "MATCH_END"
            match["result"] = (
                f"Innings ended: {match['runs']}/{match['wickets']}."
            )

    @discord.ui.button(
        label="Inswing",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def variation_1(self, interaction, button):
        await self.choose(interaction, "variation", "Inswing")

    @discord.ui.button(
        label="Outswing",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def variation_2(self, interaction, button):
        await self.choose(interaction, "variation", "Outswing")

    @discord.ui.button(
        label="Seam",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def variation_3(self, interaction, button):
        await self.choose(interaction, "variation", "Seam")

    @discord.ui.button(
        label="Slower ball",
        style=discord.ButtonStyle.primary,
        row=1,
    )
    async def variation_4(self, interaction, button):
        await self.choose(interaction, "variation", "Slower ball")

    @discord.ui.button(
        label="Yorker",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def length_1(self, interaction, button):
        await self.choose(interaction, "length", "Yorker")

    @discord.ui.button(
        label="Good length",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def length_2(self, interaction, button):
        await self.choose(interaction, "length", "Good length")

    @discord.ui.button(
        label="Bouncer",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def length_3(self, interaction, button):
        await self.choose(interaction, "length", "Bouncer")

    @discord.ui.button(
        label="Defend",
        style=discord.ButtonStyle.success,
        row=3,
    )
    async def shot_1(self, interaction, button):
        await self.choose(interaction, "shot", "Defensive block")

    @discord.ui.button(
        label="Cover drive",
        style=discord.ButtonStyle.success,
        row=3,
    )
    async def shot_2(self, interaction, button):
        await self.choose(interaction, "shot", "Cover drive")

    @discord.ui.button(
        label="Pull shot",
        style=discord.ButtonStyle.success,
        row=3,
    )
    async def shot_3(self, interaction, button):
        await self.choose(interaction, "shot", "Pull shot")

    @discord.ui.button(
        label="Lofted drive",
        style=discord.ButtonStyle.danger,
        row=4,
    )
    async def shot_4(self, interaction, button):
        await self.choose(interaction, "shot", "Lofted drive")

    @discord.ui.button(
        label="Defensive",
        style=discord.ButtonStyle.secondary,
        row=4,
    )
    async def intent_1(self, interaction, button):
        await self.choose(interaction, "intent", "Defensive")

    @discord.ui.button(
        label="Balanced",
        style=discord.ButtonStyle.secondary,
        row=4,
    )
    async def intent_2(self, interaction, button):
        await self.choose(interaction, "intent", "Balanced")

    @discord.ui.button(
        label="Aggressive",
        style=discord.ButtonStyle.danger,
        row=4,
    )
    async def intent_3(self, interaction, button):
        await self.choose(interaction, "intent", "Aggressive")
