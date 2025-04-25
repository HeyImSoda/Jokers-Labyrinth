# card_logic.py
import random

# --- Define Standard Suits and Ranks ---
# These are fundamental properties of a standard deck
suits = ["hearts", "diamonds", "clubs", "spades"]
ranks_string = ["two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "queen", "king", "ace"]
# Integer ranks (e.g., for comparison or scoring later)
# Aligning indices (0-12) with ranks_string can be useful, but 1-13 is also common.
# Let's stick with 1-13 as used previously.
ranks_int = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13]

# --- Card Class ---
class Card:
    """ Represents a single playing card. """
    def __init__(self, suit=None, rank=None, rank_string=None):
        self.flipped = False # Can track if the card object itself thinks it's flipped
        self.suit = suit
        self.rank = rank # The integer value (1-13)
        self.rank_string = rank_string # The string value ("two", "ace", etc.)

    def get_rank(self):
        """ Returns the integer rank of the card (1-13). """
        return self.rank

    def get_rank_string(self):
        """ Returns the string representation of the rank (e.g., 'ace'). """
        return self.rank_string

    def get_suit(self):
        """ Returns the suit of the card (e.g., 'hearts'). """
        return self.suit

    def get_color(self):
        """ Returns the color of the card ('red' or 'black'). """
        return "red" if self.suit in ["hearts", "diamonds"] else "black"

    # Add a __repr__ for easier printing/debugging
    def __repr__(self):
        """ Returns a human-readable string representation of the card. """
        rank_str = self.rank_string.capitalize() if self.rank_string else "UnknownRank"
        suit_str = self.suit.capitalize() if self.suit else "UnknownSuit"
        return f"{rank_str} of {suit_str}"
    
    def __eq__(self, other):
        if isinstance(other, Card):
            return self.suit == other.suit and self.rank == other.rank
        return False

# --- Deck Creation Function ---
def create_shuffled_deck():
    """
    Creates a standard 52-card deck and shuffles it.

    Returns:
        list: A list of Card objects, shuffled.
    """
    deck = []
    print("Creating standard deck...")
    # Use the constants defined in this module
    for suit_value in suits:
        # Ensure ranks_int and ranks_string have the same length
        if len(ranks_int) != len(ranks_string):
            raise ValueError("ranks_int and ranks_string must have the same number of elements.")

        for i in range(len(ranks_int)):
            rank_int_value = ranks_int[i]
            rank_string_value = ranks_string[i]
            card = Card(suit=suit_value, rank=rank_int_value, rank_string=rank_string_value)
            deck.append(card)

    print(f"Deck created with {len(deck)} cards.")
    random.shuffle(deck) # Shuffle the list of Card objects
    print("Deck shuffled.")
    return deck

# Example of using the function (optional, for testing this file directly)
if __name__ == "__main__":
    my_deck = create_shuffled_deck()
    print("\nFirst 5 cards in shuffled deck:")
    print(my_deck[:5])
    print("\nLast 5 cards in shuffled deck:")
    print(my_deck[-5:])