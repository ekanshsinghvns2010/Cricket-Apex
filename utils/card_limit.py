MAX_CARDS = 25


def _cards(profile: dict) -> list:
    """Safely return the user's card list."""
    return profile.get("cards", [])


def collection_count(profile: dict) -> int:
    """Return the number of cards owned."""
    return len(_cards(profile))


def remaining_card_space(profile: dict) -> int:
    """Return remaining collection space."""
    return max(0, MAX_CARDS - collection_count(profile))


def is_collection_full(profile: dict) -> bool:
    """Return True if the collection has reached its limit."""
    return collection_count(profile) >= MAX_CARDS


def can_receive_card(profile: dict) -> tuple[bool, str | None]:
    """
    Returns:
        (True, None) if another card can be added.
        (False, reason) if the collection is full.
    """
    count = collection_count(profile)

    if count >= MAX_CARDS:
        return (
            False,
            f"❌ Your card collection is full ({count}/{MAX_CARDS}).\n"
            "Sell unwanted cards before buying or opening new players."
        )

    return True, None