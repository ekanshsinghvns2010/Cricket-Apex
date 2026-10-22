import discord
from utils.match_utils import load_matches


# Optional custom emoji IDs from your scoreboard reference.
# The bot will use normal text if an emoji is unavailable.
EMOJIS = {
    "bat": "<:cricketbat:1513814304183422986>",
    "ball": "<:cricketball:1513814352023523490>",
    "zero": "<:zero:1523621205574156441>",
    "one": "<:one:1523620385977925742>",
    "two": "2️⃣",
    "three": "<:Three:1523620715834773686>",
    "four": "<a:FOUR:1533348879771369572>",
    "six": "<a:SIX:1533350349430198333>",
    "wicket": "🟥",
}


def get_match(match_id):
    """Load a match without changing the saved match data."""
    matches = load_matches()
    return matches.get(str(match_id))


def overs_text(legal_balls):
    """Convert legal balls into cricket notation, e.g. 5.2 overs."""
    legal_balls = max(0, int(legal_balls or 0))
    return f"{legal_balls // 6}.{legal_balls % 6}"


def run_rate(runs, legal_balls):
    if not legal_balls:
        return "0.00"
    return f"{runs * 6 / legal_balls:.2f}"


def format_batter(player, index):
    name = player.get("display_name") or player.get("name") or "Batter"
    runs = int(player.get("runs", 0) or 0)
    balls = int(player.get("balls", 0) or 0)
    sr = (runs * 100 / balls) if balls else 0.0
    team = player.get("team", "")

    marker = "🏏" if index == 0 else "  "

    return (
        f"{marker} **`{name[:18]:<18}`** ◇ "
        f"**`{team[:12]:<12}`**\n"
        f"└─ **`{runs:>3} ({balls:<3})`** ◇ "
        f"**`{sr:>6.2f} SR`**"
    )


def format_bowler(bowler):
    if not bowler:
        return "Bowler not selected yet."

    name = bowler.get("display_name") or bowler.get("name") or "Bowler"
    wickets = int(bowler.get("wickets", 0) or 0)
    runs = int(bowler.get("runs_conceded", 0) or 0)
    balls = int(bowler.get("legal_balls", 0) or 0)
    economy = (runs * 6 / balls) if balls else 0.0
    team = bowler.get("team", "")

    return (
        f"🎯 **`{name[:18]:<18}`** ◇ **`{team[:12]:<12}`**\n"
        f"└─ **`{wickets}-{runs} ({overs_text(balls)})`** ◇ "
        f"**`{economy:.2f} ECO`**"
    )


def format_recent_balls(balls):
    if not balls:
        return "No deliveries yet."

    formatted = []

    for ball in balls[-12:]:
        value = str(ball.get("display", ball.get("runs", 0)))

        if ball.get("wicket"):
            value = "W"
        elif ball.get("extra"):
            value = str(ball["extra"]).upper()

        formatted.append(f"`{value}`")

    return "  ".join(formatted)


def build_match_embed(match_id):
    """
    Build the live scoreboard from the saved match dictionary.

    Expected optional match keys:
      batting_team, bowling_team, runs, wickets, balls,
      target, batters, current_bowler, recent_balls,
      status, overs_limit, innings
    """
    match = get_match(match_id)

    if not match:
        return discord.Embed(
            title="🏏 Match not found",
            description="This match ID does not exist in the saved matches.",
            color=discord.Color.red(),
        )

    runs = int(match.get("runs", 0) or 0)
    wickets = int(match.get("wickets", 0) or 0)
    balls = int(match.get("balls", 0) or 0)
    target = match.get("target")
    overs_limit = int(match.get("overs_limit", 10) or 10)

    batting_team = str(match.get("batting_team") or "Batting Team")
    bowling_team = str(match.get("bowling_team") or "Bowling Team")
    status = str(match.get("status", match.get("state", "LIVE"))).upper()

    embed = discord.Embed(
        title="🏏 CRICKET APEX • LIVE MATCH CENTER",
        color=discord.Color.gold(),
    )

    embed.description = (
        f"**{batting_team} {runs}-{wickets} "
        f"({overs_text(balls)}/{overs_limit}.0)**\n"
        f"**{bowling_team}**"
    )

    embed.add_field(
        name="TARGET",
        value=str(target if target is not None else "—"),
        inline=True,
    )
    embed.add_field(
        name="CRR",
        value=run_rate(runs, balls),
        inline=True,
    )

    if target is not None:
        runs_needed = max(0, int(target) - runs)
        balls_left = max(0, overs_limit * 6 - balls)
        rrr = (runs_needed * 6 / balls_left) if balls_left else 0
        rrr_text = f"{rrr:.2f}"
    else:
        rrr_text = "—"

    embed.add_field(name="RRR", value=rrr_text, inline=True)

    batters = match.get("batters", [])
    if batters:
        batter_lines = [
            format_batter(player, index)
            for index, player in enumerate(batters[:2])
        ]
        partnership = match.get("partnership", {})
        partnership_runs = int(partnership.get("runs", 0) or 0)
        partnership_balls = int(partnership.get("balls", 0) or 0)

        embed.add_field(
            name=f"BATTERS {EMOJIS['bat']}  •  "
                 f"P'SHIP: {partnership_runs}({partnership_balls})",
            value="\n".join(batter_lines),
            inline=False,
        )
    else:
        embed.add_field(
            name=f"BATTERS {EMOJIS['bat']}",
            value="Batting lineup has not been initialized yet.",
            inline=False,
        )

    embed.add_field(
        name=f"BOWLER {EMOJIS['ball']}",
        value=format_bowler(match.get("current_bowler")),
        inline=False,
    )

    embed.add_field(
        name="RECENT DELIVERIES",
        value=format_recent_balls(match.get("recent_balls", [])),
        inline=False,
    )

    result = match.get("result")
    if result:
        embed.add_field(
            name="🏆 MATCH RESULT",
            value=str(result),
            inline=False,
        )

    embed.set_footer(
        text=f"Match {match_id} • {status} • Cricket Apex"
    )

    return embed