import json
import discord

def setup_debut(bot):

    @bot.command()
    async def debut(ctx):

        user_id = str(ctx.author.id)

        with open("users.json", "r") as f:
            users = json.load(f)

        if user_id in users:
            embed = discord.Embed(
                title="❌ Debut Already Completed",
                description="You have already made your professional debut!",
                color=discord.Color.red()
            )

            embed.add_field(
                name="📊 Next Step",
                value="Use `g!profile` to view your career.",
                inline=False
            )

            await ctx.send(embed=embed)
            return

        users[user_id] = {
            "coins": 5000,
            "wins": 0,
            "losses": 0,
            "level": 1,
            "xp": 0,
            "club": "Beginner Cricket Club",
            "contracts": 1
        }

        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)

        embed = discord.Embed(
            title="🏏 OFFICIAL DEBUT",
            description=f"Welcome to Cricket Bot, **{ctx.author.name}**!",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="📢 Career Announcement",
            value="Today marks the beginning of your cricket journey.",
            inline=False
        )

        embed.add_field(
            name="🎁 Debut Rewards",
            value=(
                "💰 **5,000 Coins**\n"
                "⭐ **Level 1 Account**\n"
                "🏏 **Beginner Cricket Club**\n"
                "🎟 **1 Rookie Contract**\n"
                "📊 **Career Profile Unlocked**"
            ),
            inline=False
        )

        embed.add_field(
            name="🚀 What's Next?",
            value=(
                "`g!profile` - View your career\n"
                "`g!help` - View all commands"
            ),
            inline=False
        )

        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        embed.set_footer(
            text="Your journey to becoming a cricket legend starts now!"
        )

        await ctx.send(embed=embed)