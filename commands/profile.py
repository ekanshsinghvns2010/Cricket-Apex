import json
import discord

def setup_profile(bot):

    @bot.command()
    async def profile(ctx):

        user_id = str(ctx.author.id)

        with open("users.json", "r") as f:
            users = json.load(f)

        if user_id not in users:
            await ctx.send("❌ You haven't made your debut yet! Use `g!debut`")
            return

        user = users[user_id]

        # BASIC DATA
        coins = user.get("coins", 0)
        wins = user.get("wins", 0)
        losses = user.get("losses", 0)
        level = user.get("level", 1)
        xp = user.get("xp", 0)
        trophies = user.get("trophies", 0)
        matches = user.get("matches_played", 0)

        role = user.get("role", "Not Selected")
        team = user.get("team", "Free Agent")

        # WIN RATE
        win_rate = round((wins / matches) * 100, 1) if matches > 0 else 0

        # 🏆 TROPHY LEAGUE SYSTEM
        if trophies < 100:
            league = "Rookie I"
        elif trophies < 250:
            league = "Rookie II"
        elif trophies < 500:
            league = "Rookie III"
        elif trophies < 800:
            league = "Club I"
        elif trophies < 1200:
            league = "Club II"
        elif trophies < 1700:
            league = "Club III"
        elif trophies < 2300:
            league = "District I"
        elif trophies < 3000:
            league = "District II"
        elif trophies < 3800:
            league = "District III"
        elif trophies < 4700:
            league = "State I"
        elif trophies < 5700:
            league = "State II"
        elif trophies < 7000:
            league = "State III"
        elif trophies < 8500:
            league = "National I"
        elif trophies < 10000:
            league = "National II"
        elif trophies < 12000:
            league = "National III"
        elif trophies < 14500:
            league = "International I"
        elif trophies < 17000:
            league = "International II"
        elif trophies < 20000:
            league = "International III"
        else:
            league = "🏆 Hall of Fame"

        # ROLE DISPLAY STYLE
        role_display = {
            "Aggressive Batter": "💥 Aggressive Batter",
            "Finisher Batter": "🎯 Finisher Batter",
            "Anchor Batter": "🧱 Anchor Batter",
            "Fast Swing Bowler": "⚡ Fast Swing Bowler",
            "Spinner": "🌀 Spinner",
            "All-Rounder": "🔥 All-Rounder"
        }.get(role, "❔ Not Selected")

        # EMBED
        embed = discord.Embed(
            title=f"🏏 {ctx.author.name.upper()}'S CAREER PROFILE",
            color=0x00ffcc
        )

        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        # 🏆 TROPHIES
        embed.add_field(
            name="🏆 Trophies & League",
            value=f"🏆 **{trophies}**\n🎖 **{league}**",
            inline=False
        )

        # ⭐ CAREER STATS
        embed.add_field(
            name="⭐ Career Stats",
            value=(
                f"⭐ Level: {level}\n"
                f"✨ XP: {xp}\n"
                f"📅 Matches: {matches}"
            ),
            inline=True
        )

        # 💰 ECONOMY
        embed.add_field(
            name="💰 Economy",
            value=f"💰 Coins: {coins}",
            inline=True
        )

        # 📊 PERFORMANCE
        embed.add_field(
            name="📊 Performance",
            value=(
                f"🏆 Wins: {wins}\n"
                f"❌ Losses: {losses}\n"
                f"📈 Win Rate: {win_rate}%"
            ),
            inline=False
        )

        # 🎭 ROLE + TEAM
        embed.add_field(
            name="🎭 Career Role",
            value=(
                f"🏏 Role: {role_display}\n"
                f"🏟 Team: {team}"
            ),
            inline=False
        )

        # STATUS
        embed.add_field(
            name="🏏 Career Status",
            value="🔥 Active Professional Cricketer",
            inline=False
        )

        embed.set_footer(text="Train with g!play | Improve with g!train | Rise in leagues 🏆")

        await ctx.send(embed=embed)