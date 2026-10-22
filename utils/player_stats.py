
# utils/player_stats.py

def player_id(player):
    if isinstance(player, dict):
        value = player.get("id")
        return str(value) if value is not None else ""
    return str(player) if player is not None else ""


def ensure_stats(match):
    """Initialize innings statistics without overwriting existing figures."""
    match.setdefault("batting_stats", {})
    match.setdefault("bowling_stats", {})
    match.setdefault("fall_of_wickets", [])

    return match


def get_batting_stats(match, player):
    ensure_stats(match)
    pid = player_id(player)

    if not pid:
        raise ValueError("Player must have a valid ID.")

    stats = match["batting_stats"]
    stats.setdefault(
        pid,
        {
            "name": (
                player.get("display_name") or player.get("name", "Unknown")
                if isinstance(player, dict)
                else str(player)
            ),
            "runs": 0,
            "balls": 0,
            "fours": 0,
            "sixes": 0,
            "out": False,
            "dismissal": None,
        },
    )

    return stats[pid]


def get_bowling_stats(match, player):
    ensure_stats(match)
    pid = player_id(player)

    if not pid:
        raise ValueError("Bowler must have a valid ID.")

    stats = match["bowling_stats"]
    stats.setdefault(
        pid,
        {
            "name": (
                player.get("display_name") or player.get("name", "Unknown")
                if isinstance(player, dict)
                else str(player)
            ),
            "balls": 0,
            "runs_conceded": 0,
            "wickets": 0,
            "maidens": 0,
            "wides": 0,
            "no_balls": 0,
        },
    )

    return stats[pid]


def record_batting_delivery(
    match,
    batter,
    batter_runs,
    legal,
    dismissal=False,
    dismissal_type=None,
):
    """
    Record the batter's contribution from a single delivery.

    batter_runs excludes extras.
    legal indicates whether the delivery counts as a legal ball.
    """
    if not isinstance(batter_runs, int) or batter_runs < 0:
        raise ValueError("batter_runs must be a non-negative integer.")

    stats = get_batting_stats(match, batter)

    if stats["out"]:
        raise ValueError("A dismissed batter cannot bat again.")

    stats["runs"] += batter_runs

    if legal:
        stats["balls"] += 1

    if batter_runs == 4:
        stats["fours"] += 1
    elif batter_runs == 6:
        stats["sixes"] += 1

    if dismissal:
        stats["out"] = True
        stats["dismissal"] = dismissal_type or "out"

        match["fall_of_wickets"].append(
            {
                "wicket": sum(
                    1
                    for item in match["batting_stats"].values()
                    if item["out"]
                ),
                "score": int(match.get("runs", 0)),
                "batter": stats["name"],
                "dismissal": stats["dismissal"],
            }
        )

    return stats


def record_bowling_delivery(
    match,
    bowler,
    total_runs,
    legal,
    wicket=False,
    extra_type=None,
    bowler_charged_runs=None,
):
    """
    Record a bowler's figures.

    total_runs is the team's total from the delivery.
    bowler_charged_runs may be supplied explicitly because some extras
    are not charged to the bowler.
    """
    if not isinstance(total_runs, int) or total_runs < 0:
        raise ValueError("total_runs must be a non-negative integer.")

    stats = get_bowling_stats(match, bowler)

    charged = (
        total_runs
        if bowler_charged_runs is None
        else bowler_charged_runs
    )

    if not isinstance(charged, int) or charged < 0:
        raise ValueError("bowler_charged_runs must be non-negative.")

    stats["runs_conceded"] += charged

    if legal:
        stats["balls"] += 1

    if extra_type == "wide":
        stats["wides"] += total_runs
    elif extra_type == "no_ball":
        stats["no_balls"] += 1

    if wicket:
        stats["wickets"] += 1

    return stats


def batting_strike_rate(stats):
    balls = int(stats.get("balls", 0))
    runs = int(stats.get("runs", 0))

    if balls == 0:
        return 0.0

    return round(runs * 100 / balls, 2)


def bowling_economy(stats, balls_per_over=6):
    balls = int(stats.get("balls", 0))
    runs = int(stats.get("runs_conceded", 0))

    if balls_per_over <= 0:
        raise ValueError("balls_per_over must be positive.")

    if balls == 0:
        return 0.0

    return round(runs * balls_per_over / balls, 2)


def format_batting_scorecard(match):
    ensure_stats(match)
    lines = [
        "**Batter — R (B), 4s, 6s, SR**",
    ]

    for stats in match["batting_stats"].values():
        status = (
            f"out ({stats['dismissal']})"
            if stats["out"]
            else "not out"
        )

        lines.append(
            f"{stats['name']} — "
            f"{stats['runs']} ({stats['balls']}), "
            f"{stats['fours']}, {stats['sixes']}, "
            f"{batting_strike_rate(stats)} · {status}"
        )

    return "\n".join(lines)


def format_bowling_scorecard(match, balls_per_over=6):
    ensure_stats(match)
    lines = [
        "**Bowler — O, R, W, Econ**",
    ]

    for stats in match["bowling_stats"].values():
        overs = (
            f"{stats['balls'] // balls_per_over}."
            f"{stats['balls'] % balls_per_over}"
        )

        lines.append(
            f"{stats['name']} — "
            f"{overs}, {stats['runs_conceded']}, "
            f"{stats['wickets']}, "
            f"{bowling_economy(stats, balls_per_over)}"
        )

    return "\n".join(lines)
