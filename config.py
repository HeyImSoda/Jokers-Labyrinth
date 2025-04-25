# --- START OF FILE config.py ---

import os

# --- File Paths ---
ASSETS_BASE_PATH = r"C:\Users\stell\Desktop\Python Files\Jokers_Labyrinth\assets" # <<< Use your actual path
CARD_FACES_PATH = os.path.join(ASSETS_BASE_PATH, "card_faces")
CARD_BACK_PATH = os.path.join(ASSETS_BASE_PATH, "card_back.png")

# --- Grid Dimensions ---
ROWS = 7
COLUMNS = 7

# --- Animation ---
ANIMATION_DELAY = 6 # Milliseconds between animation steps
ANIMATION_STEPS = 36 # How many steps for shrink/grow

# --- Card Visuals ---
CARD_SCALE_FACTOR = 1.5

# --- UI Layout ---
INFO_PANEL_WIDTH = 350
GRID_PADDING_FACTOR = 1.0 # How many card dimensions to pad around the grid (1.0 = one card width/height)

# --- Hand Layout ---
HAND_ROWS = 2
HAND_COLS = 8
HAND_OVERLAP_FACTOR = 0.45 # Show 45% of the card width for overlap
HAND_VERTICAL_PADDING = 10 # Pixels between hand rows

# --- Game Rules ---
PLAYER_SUIT = "spades" # Example: Player is the Jack of Spades.

# --- Card States ---
STATE_FACE_DOWN = 0
STATE_FACE_UP = 1
STATE_ACTION_TAKEN = 2

# --- Joker Settings ---
# Define how jokers are represented in Card objects and image filenames
# Ensure these match your Card class and asset naming convention
BLACK_JOKER_SUIT = "black_joker"
BLACK_JOKER_RANK = 14
BLACK_JOKER_RANK_STR = "fourteen"

RED_JOKER_SUIT = "red_joker"
RED_JOKER_RANK = 14
RED_JOKER_RANK_STR = "fourteen"

# Card to remove (optional, ensure it exists in create_shuffled_deck output)
CARD_TO_REMOVE_SUIT = "clubs"
CARD_TO_REMOVE_RANK = 2
CARD_TO_REMOVE_RANK_STR = "two"

# --- END OF FILE config.py ---