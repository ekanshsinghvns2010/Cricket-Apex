import discord
from discord.ext import commands
import json
import os

from views.setxi_view import SetXIView

PLAYERS_FILE = "players.json"
PROFILES_FILE = "users.json"

def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f, indent=4)

    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_players():
    if not os.path.exists(PLAYERS_FILE):
        with open(PLAYERS_FILE, "w") as f:
            json.dump([], f, indent=4)

    with open(PLAYERS_FILE, "r") as f:
        return json.load(f)


def load_profiles():
    return load_json(PROFILES_FILE)


def save_profiles(profiles):
    save_json(PROFILES_FILE, profiles)


class PlayingXIBuilder:

    def __init__(self, user_id, profile, all_players):
        self.user_id = user_id
        self.profile = profile
        self.all_players = all_players

    def get_owned_players(self):
        owned_ids = self.profile.get("cards", [])
        owned_players = [p for p in self.all_players if p["id"] in owned_ids]
        return owned_players

    def has_minimum_cards(self):
        return len(self.profile.get("cards", [])) >= 11


class PlayingXIResult:

    def __init__(self, selected_players):
        self.selected_players = selected_players

    def is_valid(self):
        return len(self.selected_players) == 11

    def count_by_role(self):
        counts = {"BAT": 0, "WK": 0, "AR": 0, "BOWL": 0}
        for p in self.selected_players:
            role = p.get("role")
            if role in counts:
                counts[role] += 1
        return counts

    def is_valid_composition(self):
        counts = self.count_by_role()
        return (
            1 <= counts["WK"] <= 2 and
            3 <= counts["BAT"] <= 6 and
            1 <= counts["AR"] <= 4 and
            3 <= counts["BOWL"] <= 6
        )

    def average_ovr(self):
        if not self.selected_players:
            return 0
        total = sum(p.get("ovr", 0) for p in self.selected_players)
        return round(total / len(self.selected_players))


def setup_setxi(bot):

    @bot.command(name="setxi")
    async def setxi(ctx):

        user_id = str(ctx.author.id)

        profiles = load_profiles()

        if user_id not in profiles:
            await ctx.send("❌ You don't have a profile yet.")
            return

        profile = profiles[user_id]

        if "playing_xi" not in profile:
            profile["playing_xi"] = []

        if "substitutes" not in profile:
            profile["substitutes"] = []

        all_players = load_players()

        builder = PlayingXIBuilder(user_id, profile, all_players)

        if not builder.has_minimum_cards():
            await ctx.send("❌ You need at least 11 cards to set a Playing XI.")
            return

        owned_players = builder.get_owned_players()

        if len(owned_players) < 11:
            await ctx.send("❌ You need at least 11 valid cards to set a Playing XI.")
            return

        view = SetXIView(ctx.author, owned_players)

        message = await ctx.send(
            "🏏 **Select your Playing XI:**\n"
            "1–2 Wicket Keepers, 3–6 Batters, 1–4 All-Rounders, 3–6 Bowlers.",
            view=view
        )
        view.message = message
   
        timed_out = await view.wait()

        if timed_out:
            await ctx.send("❌ Playing XI selection timed out.")
            return

        selected_ids = getattr(view, "selected_ids", None)

        if not selected_ids:
            await ctx.send("❌ Playing XI selection was cancelled.")
            return

        if len(set(selected_ids)) != len(selected_ids):
            await ctx.send("❌ Duplicate players detected in selection.")
            return

        players_by_id = {p["id"]: p for p in owned_players}
        selected_players = []

        for pid in selected_ids:
            if pid not in players_by_id:
                await ctx.send("❌ Invalid player selection detected.")
                return
            selected_players.append(players_by_id[pid])

        result = PlayingXIResult(selected_players)

        if not result.is_valid():
            await ctx.send(f"❌ You must select exactly 11 players. You selected {len(selected_players)}.")
            return

        counts = result.count_by_role()

        if not result.is_valid_composition():
            await ctx.send(
                "❌ Invalid Playing XI.\n"
                "WK: 1–2\n"
                "BAT: 3–6\n"
                "AR: 1–4\n"
                "BOWL: 3–6"
            )
            return

        profile["playing_xi"] = selected_ids
        profiles[user_id] = profile
        save_profiles(profiles)

        team_ovr = result.average_ovr()

        embed = discord.Embed(
            title="✅ Playing XI Saved",
            description=f"{ctx.author.mention}'s Playing XI has been updated.",
            color=discord.Color.green()
        )

        embed.add_field(name="⭐ Team OVR", value=str(team_ovr), inline=True)
        embed.add_field(name="👥 Players", value=str(len(selected_players)), inline=True)
        embed.add_field(name="🏏 BAT", value=str(counts["BAT"]), inline=True)
        embed.add_field(name="🧤 WK", value=str(counts["WK"]), inline=True)
        embed.add_field(name="🎯 AR", value=str(counts["AR"]), inline=True)
        embed.add_field(name="🎳 BOWL", value=str(counts["BOWL"]), inline=True)

        await message.edit(view=None)
        await ctx.send(embed=embed)
    