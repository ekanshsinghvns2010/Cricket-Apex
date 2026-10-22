
import random


PACE_VARIATIONS = [
    "Inswing",
    "Outswing",
    "Seam",
    "Reverse swing",
    "Off-cutter",
    "Leg-cutter",
    "Slower ball",
    "Knuckleball",
    "Cross-seam",
]

SPIN_VARIATIONS = [
    "Off-spin",
    "Leg-spin",
    "Googly",
    "Doosra",
    "Arm ball",
    "Top-spinner",
    "Slider",
    "Flighted",
    "Faster ball",
]

BOWLING_LENGTHS = [
    "Yorker",
    "Full",
    "Good length",
    "Back of a length",
    "Bouncer",
    "Short",
    "Half-volley",
]

BATTING_SHOTS = [
    "Defensive block",
    "Leave",
    "Straight drive",
    "Cover drive",
    "Pull shot",
    "Hook shot",
    "Sweep",
    "Lofted drive",
    "Late cut",
]

BATTING_INTENTS = [
    "Defensive",
    "Balanced",
    "Aggressive",
]


def bowling_variations(bowler):
    style = str(
        bowler.get("bowling_style", "")
    ).lower()

    spin_terms = (
        "spin",
        "orthodox",
        "chinaman",
        "offspin",
        "legspin",
    )

    if any(term in style for term in spin_terms):
        return SPIN_VARIATIONS

    return PACE_VARIATIONS


def rating(player, key, default=60):
    try:
        return max(1, min(100, int(player.get(key, default))))
    except (ValueError, TypeError):
        return default


def delivery_result(
    batter,
    bowler,
    variation,
    length,
    shot,
    intent,
    pitch="Normal",
):
    """
    Resolve one delivery.

    Returns a dictionary describing the result.
    This function does not save match data itself.
    """

    batting = rating(batter, "batting_ovr")
    bowling = rating(bowler, "bowling_ovr")
    fielding = rating(bowler, "fielding_ovr", 60)

    fitness_bat = rating(batter, "fitness", 80)
    fitness_bowl = rating(bowler, "fitness", 80)

    attack_bonus = {
        "Defensive": -12,
        "Balanced": 0,
        "Aggressive": 12,
    }.get(intent, 0)

    shot_bonus = {
        "Defensive block": -8,
        "Leave": -10,
        "Straight drive": 3,
        "Cover drive": 3,
        "Pull shot": 2,
        "Hook shot": 1,
        "Sweep": 2,
        "Lofted drive": 8,
        "Late cut": 1,
    }.get(shot, 0)

    length_bonus = {
        "Yorker": 7,
        "Full": 0,
        "Good length": 3,
        "Back of a length": 2,
        "Bouncer": 6,
        "Short": 4,
        "Half-volley": -8,
    }.get(length, 0)

    variation_bonus = {
        "Slower ball": 5,
        "Knuckleball": 6,
        "Reverse swing": 4,
        "Googly": 6,
        "Doosra": 5,
        "Top-spinner": 3,
        "Slider": 4,
    }.get(variation, 0)

    pitch_text = str(pitch).lower()
    if "spin" in pitch_text and variation in SPIN_VARIATIONS:
        variation_bonus += 3

    if "fast" in pitch_text and variation in PACE_VARIATIONS:
        variation_bonus += 2

    batting_power = (
        batting
        + fitness_bat * 0.10
        + attack_bonus
        + shot_bonus
    )

    bowling_power = (
        bowling
        + fitness_bowl * 0.10
        + length_bonus
        + variation_bonus
    )

    # A small random element prevents identical ratings from
    # producing identical outcomes on every delivery.
    batting_power += random.randint(-12, 12)
    bowling_power += random.randint(-12, 12)

    # A leave is normally a dot ball unless the delivery is wide.
    if shot == "Leave":
        return {
            "runs": 0,
            "wicket": False,
            "extra": None,
            "legal": True,
            "description": "The batter leaves it alone.",
        }

    # Rare extras. Extras are not legal deliveries.
    extra_roll = random.random()
    if extra_roll < 0.025:
        return {
            "runs": 1,
            "wicket": False,
            "extra": "wide",
            "legal": False,
            "description": "Wide! The batter cannot reach it.",
        }

    if extra_roll < 0.035:
        return {
            "runs": 1,
            "wicket": False,
            "extra": "no-ball",
            "legal": False,
            "description": "No-ball! An extra run is awarded.",
        }

    difference = batting_power - bowling_power

    wicket_chance = 0.035
    wicket_chance += max(0, -difference) * 0.0015

    if intent == "Aggressive":
        wicket_chance += 0.035

    if length in ("Yorker", "Bouncer"):
        wicket_chance += 0.015

    wicket_chance = min(0.25, max(0.01, wicket_chance))

    if random.random() < wicket_chance:
        dismissal = random.choice([
            "bowled",
            "caught",
            "lbw",
            "run out",
        ])

        return {
            "runs": 0,
            "wicket": True,
            "dismissal": dismissal,
            "extra": None,
            "legal": True,
            "description": f"WICKET! The batter is {dismissal}.",
        }

    # Run distribution responds to the ratings and decisions.
    score = difference + random.randint(-18, 18)

    if intent == "Defensive":
        score -= 8
    elif intent == "Aggressive":
        score += 8

    if score < -18:
        runs = 0
    elif score < 0:
        runs = random.choice([0, 0, 1])
    elif score < 15:
        runs = random.choice([0, 1, 1, 2])
    elif score < 30:
        runs = random.choice([1, 2, 2, 3, 4])
    elif score < 43:
        runs = random.choice([1, 2, 3, 4, 4, 6])
    else:
        runs = random.choice([2, 3, 4, 4, 6, 6])

    # Lofted attacking shots carry extra risk.
    if shot == "Lofted drive" and runs >= 4:
        if random.random() < 0.08:
            return {
                "runs": 0,
                "wicket": True,
                "dismissal": "caught",
                "extra": None,
                "legal": True,
                "description": "Caught in the deep! WICKET!",
            }

    return {
        "runs": runs,
        "wicket": False,
        "extra": None,
        "legal": True,
        "description": (
            f"{shot}! The batter scores {runs} run(s)."
        ),
    }
