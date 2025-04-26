# --- START OF FILE combat/setup.py ---

import config
# Needs Card definition if type hinting or checking card properties
# from card_logic import Card # Assuming card_logic.py is at the project root

def get_value_cards_from_hand(hand_card_data, player_suit):
    """Finds valid value cards (Red Numbers OR Friendly Q/K) in the hand."""
    value_cards = []
    for r in range(config.HAND_ROWS):
        for c in range(config.HAND_COLS):
            card = hand_card_data[r][c]
            if not card: continue

            card_color = card.get_color()
            card_rank = card.get_rank()
            card_suit = card.get_suit()

            # Equipment: Red numbers 2-10
            is_equipment = (card_color == "red" and card_rank is not None and 2 <= card_rank <= 10)
            # Friendly Face: Q/K matching player suit
            is_friendly_face = (card_rank in [12, 13] and card_suit == player_suit)

            if is_equipment or is_friendly_face:
                value_cards.append((card, r, c)) # Store card and original hand coords

    return value_cards

# Note: prepare_combat_resolution depends heavily on logic and UI calls,
# so it might fit better in the main manager or logic file. Let's move it later.

# --- END OF FILE combat/setup.py ---