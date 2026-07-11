import discord

def build_crate_open(crate_name: str, rewards_left: int):

    embed = discord.Embed(
        title=f"🎁 {crate_name}",
        description=(
            "Press **OPEN** to reveal your rewards!\n\n"
            f"🎁 **Rewards Left:** {rewards_left}"
        ),
        color=discord.Color.gold()
    )

    # Change this later to your actual crate image
    embed.set_image(url="attachment://common_closed.png")

    embed.set_footer(text="Good luck!")

    return embed