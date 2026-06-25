import discord

def setup_help(bot):

    @bot.command(name="help")
    async def help_command(ctx):

        commands_list = []

        for command in sorted(bot.commands, key=lambda c: c.name):
            if command.name == "help":
                continue

            commands_list.append(
                f"➜ `{bot.command_prefix}{command.name}`"
            )

        command_text = "\n".join(commands_list)

        embed = discord.Embed(
            title="🏏 CRICKET BOT HELP",
            color=0x00ff99
        )

        embed.add_field(
            name="📖 Commands",
            value=command_text,
            inline=False
        )

        await ctx.send(embed=embed)