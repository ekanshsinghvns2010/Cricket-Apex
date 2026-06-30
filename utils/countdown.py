import asyncio

from utils.match_utils import load_matches, save_matches


async def start_countdown(message, match_id):
    print("Countdown started")
    matches = load_matches()
    match = matches.get(str(match_id))

    if match is None:
        return

    if match.get("status") == "starting":
        return

    match["status"] = "starting"
    save_matches(matches)

    try:
        embed = message.embeds[0]

        embed.set_field_at(
            len(embed.fields) - 1,
            name="Status",
            value="✅ Both teams full! Match starting in **5** seconds...",
            inline=False
        )

        await message.edit(embed=embed)
        print("First message edited")

        await asyncio.sleep(5)
        print("5 seaconds finished")

        embed = message.embeds[0]

        embed.set_field_at(
            len(embed.fields) - 1,
            name="Status",
            value="🪙 Toss Time!",
            inline=False
        )

        await message.edit(embed=embed)
        print("Toss message edited")

    except Exception as e:
        print(f"COUNTDOWN ERROR:{type(e).__name__}: {e}")
        raise
        
        
