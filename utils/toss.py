import random

from utils.match_utils import load_matches, save_matches


def perform_toss(match_id):

    matches = load_matches()
    match = matches[str(match_id)]

    winner = random.choice(["red", "blue"])
    choice = random.choice(["bat", "bowl"])

    match["toss_winner"] = winner
    match["toss_choice"] = choice

    if choice == "bat":
        match["batting_team"] = winner
        match["bowling_team"] = "blue" if winner == "red" else "red"
    else:
        match["bowling_team"] = winner
        match["batting_team"] = "blue" if winner == "red" else "red"

    save_matches(matches)

    return winner, choice