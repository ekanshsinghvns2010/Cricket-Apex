import json
import discord

def setup_debut(bot):

    @bot.command()
    async def debut(ctx):

        user_id = str(ctx.author.id)

        with open("users.json", "r") as f:
            users = json.load(f)

        if user_id in users:
            await ctx.send("❌ You have already made your debut!")
            return

        # Create basic account (NO ROLE YET)
        users[user_id] = {
            "coins": 5000,
            "wins": 0,
            "losses": 0,
            "level": 1,
            "xp": 0,

            "trophies": 0,
            "matches_played": 0,

            "role": None,
            "team": None,

            "batting": 40,
            "bowling": 40,
            "fitness": 40,
            "experience": 40,
            #Economy
            "coins": 500,
            "gems": 0,
            "lifetime_earned": 500,
             "lifetime_spent": 0
        }

        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)

        embed = discord.Embed(
            title="🏏 OFFICIAL DEBUT CEREMONY",
            description=f"Welcome **{ctx.author.name}** to Cricket Career Mode!",
            color=0x00ffcc
        )

        embed.add_field(
            name="🎁 Starting Rewards",
            value=(
                "💰 5000 Coins\n"
                "⭐ Level 1 Player\n"
                "🏆 Rookie Status\n"
                "📊 Career Profile Created"
            ),
            inline=False
        )

        embed.add_field(
            name="🎭 Choose Your Role",
            value=(
                "Reply with:\n"
                "`1` Aggressive Batter\n"
                "`2` Finisher Batter\n"
                "`3` Anchor Batter\n"
                "`4` Fast Swing Bowler\n"
                "`5` Spinner\n"
                "`6` All-Rounder"
            ),
            inline=False
        )

        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        msg = await ctx.send(embed=embed)

        # ROLE SELECTION CHECK (simple version)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            reply = await bot.wait_for("message", check=check, timeout=60)

            role_map = {
                "1": "Aggressive Batter",
                "2": "Finisher Batter",
                "3": "Anchor Batter",
                "4": "Fast Swing Bowler",
                "5": "Spinner",
                "6": "All-Rounder"
            }

            if reply.content not in role_map:
                await ctx.send("❌ Invalid role selection. Use g!debut again.")
                return

            users[user_id]["role"] = role_map[reply.content]

            with open("users.json", "w") as f:
                json.dump(users, f, indent=4)

            await ctx.send(
                f"✅ Role assigned: **{role_map[reply.content]}**\n"
                "🏏 Your career has officially begun!"
            )

        except:
            await ctx.send("⏰ Role selection timed out. Use `g!debut` again.")