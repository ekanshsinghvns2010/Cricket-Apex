import discord
from database import connect_db


def setup_debut(bot):

    @bot.command()
    async def debut(ctx):

        user_id = str(ctx.author.id)

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )

        if cursor.fetchone():
            conn.close()
            await ctx.send("❌ You have already made your debut!")
            return

        cursor.execute("""
            INSERT INTO users (
                user_id,
                coins,
                gems,
                wins,
                losses,
                level,
                xp,
                trophies,
                matches_played,
                role,
                team,
                batting,
                bowling,
                fitness,
                experience,
                lifetime_earned,
                lifetime_spent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            500,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            None,
            None,
            40,
            40,
            40,
            40,
            500,
            0
        ))

        conn.commit()

        embed = discord.Embed(
            title="🏏 OFFICIAL DEBUT CEREMONY",
            description=f"Welcome **{ctx.author.name}** to Cricket Career Mode!",
            color=0x00ffcc
        )

        embed.add_field(
            name="🎁 Starting Rewards",
            value=(
                "💰 500 Coins\n"
                "⭐ Level 1 Player\n"
                "🏆 Rookie Status\n"
                "📊 Career Profile Created"
            ),
            inline=False
        )

        embed.add_field(
            name="🎭 Choose Your Role",
            value=(
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

        await ctx.send(embed=embed)

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
                cursor.execute(
                    "DELETE FROM users WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                conn.close()

                await ctx.send("❌ Invalid role selection. Use `g!debut` again.")
                return

            cursor.execute(
                "UPDATE users SET role = ? WHERE user_id = ?",
                (role_map[reply.content], user_id)
            )

            conn.commit()
            conn.close()

            await ctx.send(
                f"✅ Role assigned: **{role_map[reply.content]}**\n🏏 Your career has officially begun!"
            )

        except:
            cursor.execute(
                "DELETE FROM users WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            conn.close()

            await ctx.send("⏰ Role selection timed out. Use `g!debut` again.")