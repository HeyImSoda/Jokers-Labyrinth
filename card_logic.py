# --- START OF FILE card_logic.py ---

# card_logic.py
import random

# --- Define Standard Suits and Ranks ---
# These are fundamental properties of a standard deck
suits = ["hearts", "diamonds", "clubs", "spades"]
# --- MODIFICATION: Added Jack to ranks_string and ranks_int ---
ranks_string = ["two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "jack", "queen", "king", "ace"] # Jack added
ranks_int = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 1] # Jack=11, Ace=1 (adjust if Ace high)

# --- Card Class ---
class Card:
    """ Represents a single playing card. """
    def __init__(self, suit=None, rank=None, rank_string=None):
        # Ensure rank is integer if provided
        try:
            self.rank = int(rank) if rank is not None else None
        except (ValueError, TypeError):
             print(f"Warning: Invalid rank '{rank}' provided for suit '{suit}'. Setting rank to None.")
             self.rank = None

        self.flipped = False # Can track if the card object itself thinks it's flipped
        self.suit = suit
        # self.rank = rank # The integer value (e.g., 1-13)
        self.rank_string = rank_string # The string value ("two", "ace", etc.)

    def get_rank(self):
        """ Returns the integer rank of the card. """
        return self.rank

    def get_rank_string(self):
        """ Returns the string representation of the rank (e.g., 'ace'). """
        return self.rank_string

    def get_suit(self):
        """ Returns the suit of the card (e.g., 'hearts', 'black_joker'). """
        return self.suit

    def get_color(self):
        """ Returns the color of the card ('red', 'black', or 'joker'). """
        if self.suit in ["hearts", "diamonds"]:
            return "red"
        elif self.suit in ["clubs", "spades"]:
            return "black"
        elif "joker" in str(self.suit).lower():
             return "joker" # Special case for Jokers
        else:
            return None # Should not happen for standard cards

    # Add a __repr__ for easier printing/debugging
    def __repr__(self):
        """ Returns a human-readable string representation of the card. """
        # Handle potential None values gracefully
        rank_str = str(self.rank_string).capitalize() if self.rank_string else "NoRank"
        suit_str = str(self.suit).capitalize().replace('_', ' ') if self.suit else "NoSuit"

        # Special formatting for Jokers
        if "joker" in str(self.suit).lower():
             return f"{suit_str}" # e.g., "Black Joker"
        else:
             # Check if rank is valid before printing "of"
             if self.rank_string and self.suit:
                 return f"{rank_str} of {suit_str}"
             else:
                 # Fallback if data is incomplete
                 return f"Card({suit_str}, {rank_str})"


    def __eq__(self, other):
        """ Checks for equality based on suit and rank. Handles None types. """
        if not isinstance(other, Card):
            return NotImplemented # Let Python handle comparison with other types
        # Both suits and ranks must match (or both be None)
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        """ Allows Cards to be used in sets or as dictionary keys. """
        return hash((self.suit, self.rank))


# --- Deck Creation Function ---
def create_shuffled_deck():
    """
    Creates a standard 52-card deck and shuffles it.

    Returns:
        list: A list of Card objects, shuffled.
    """
    deck = []
    print("Creating standard deck...")
    if len(ranks_int) != len(ranks_string):
        raise ValueError(f"Internal Error: ranks_int ({len(ranks_int)}) and ranks_string ({len(ranks_string)}) must have the same number of elements.")

    for suit_value in suits:
        for i in range(len(ranks_int)):
            rank_int_value = ranks_int[i]
            rank_string_value = ranks_string[i]
            # Validate before creating card - ensure rank/string aren't None unexpectedly
            if rank_int_value is None or rank_string_value is None:
                 print(f"Warning: Skipping card creation due to None rank/string for suit {suit_value} at index {i}")
                 continue
            card = Card(suit=suit_value, rank=rank_int_value, rank_string=rank_string_value)
            deck.append(card)

    print(f"Standard deck created with {len(deck)} cards.")
    random.shuffle(deck)
    print("Deck shuffled.")
    return deck

# Example of using the function (optional, for testing this file directly)
if __name__ == "__main__":
    try:
        my_deck = create_shuffled_deck()
        if my_deck:
            print("\nFirst 5 cards in shuffled deck:")
            for card in my_deck[:5]: print(f"  - {card}") # Use repr
            print("\nLast 5 cards in shuffled deck:")
            for card in my_deck[-5:]: print(f"  - {card}") # Use repr

        # Test specific cards
        print("\nTesting Card creation and methods:")
        c1 = Card("hearts", 1, "ace")
        c2 = Card("spades", 11, "jack")
        joker = Card("red_joker", 14, "fourteen") # Assuming joker setup
        print(f" Card 1: {c1}, Rank: {c1.get_rank()}, Color: {c1.get_color()}")
        print(f" Card 2: {c2}, Rank: {c2.get_rank()}, Color: {c2.get_color()}")
        print(f" Joker: {joker}, Rank: {joker.get_rank()}, Color: {joker.get_color()}")
        print(f" c1 == c2: {c1 == c2}")
        c3 = Card("hearts", 1, "ace")
        print(f" c1 == c3: {c1 == c3}")

    except Exception as e:
        print(f"\nAn error occurred during testing: {e}")

# --- END OF FILE card_logic.py ---