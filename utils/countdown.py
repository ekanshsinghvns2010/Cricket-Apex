import asyncio

from utils.match_utils import load_matches, save_matches


async def start_countdown(message, match_id):

    from views.matches_lobby import (
        build_lobby_embed,
        MatchLobbyView
    )

    print(">>> Countdown function entered")

    matches = load_matches()
    match = matches.get(str(match_id))

    if match is None:
        print("❌ Match not found")
        return

    print("Status before:", repr(match["status"]))

    if match.get("status") == "live":
        print("❌ Match already live")
        return

    match["status"] = "starting"
    save_matches(matches)

    print("✅ Status changed to starting")

    guild = message.guild

    view = MatchLobbyView(match_id)

    for child in view.children:
        child.disabled = True

    for i in [5, 4, 3, 2, 1]:

        embed = await

        embed.set_field_at(
            8,
            name="Status",
            value=f"⏳ Match starts in **{i}**...",
            inline=False
        )

        await message.edit(
            embed=embed,
            view=view
        )

        print(f"✅ Edited countdown {i}")

        await asyncio.sleep(1)

    try:
        from views.toss_view import build_toss_embed

        embed = await build_toss_embed(
            guild,
            match_id
        )

        matches = load_matches()
        match = matches[str(match_id)]

        match["status"] = "toss"

        save_matches(matches)

        await message.edit(
            embed=embed,
            view=None
        )

        print("✅ Toss screen shown")

    except Exception as e:
        print("❌ FINAL EDIT ERROR:", e)
        raise