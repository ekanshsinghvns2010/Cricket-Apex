import json


def add_card(user_id, card_name):

    with open("users.json", "r") as f:
        data = json.load(f)

    if "cards" not in data[user_id]:
        data[user_id]["cards"] = []

    data[user_id]["cards"].append(card_name)

    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)