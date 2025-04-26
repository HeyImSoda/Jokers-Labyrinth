# --- START OF FILE config.py ---

import os

# --- File Paths ---
ASSETS_BASE_PATH = r"C:\Users\stell\Desktop\Python Files\Jokers_Labyrinth\assets" # <<< Use your actual path
CARD_FACES_PATH = os.path.join(ASSETS_BASE_PATH, "card_faces")
CARD_BACK_PATH = os.path.join(ASSETS_BASE_PATH, "card_back.png")
DICE_FACES_PATH = os.path.join(ASSETS_BASE_PATH, "dice_faces")

# --- Grid Dimensions ---
ROWS = 7
COLUMNS = 7

# --- Animation ---
ANIMATION_DELAY = 6 # Milliseconds between animation steps (Card Flip)
ANIMATION_STEPS = 36 # How many steps for shrink/grow (Card Flip)

# --- Card Visuals ---
CARD_SCALE_FACTOR = 1.6

# --- UI Layout ---
INFO_PANEL_WIDTH = 450
GRID_PADDING_FACTOR = 1.0

# --- Hand Layout ---
HAND_ROWS = 2
HAND_COLS = 8
HAND_OVERLAP_FACTOR = 0.45
HAND_VERTICAL_PADDING = 10

# --- Game Rules ---
PLAYER_SUIT = "spades"

# --- Card States ---
STATE_FACE_DOWN = 0
STATE_FACE_UP = 1
STATE_ACTION_TAKEN = 2

# --- Joker Settings ---
BLACK_JOKER_SUIT = "black_joker"
BLACK_JOKER_RANK = 14
BLACK_JOKER_RANK_STR = "fourteen"
RED_JOKER_SUIT = "red_joker"
RED_JOKER_RANK = 14
RED_JOKER_RANK_STR = "fourteen"

# --- Card to Remove ---
CARD_TO_REMOVE_SUIT = "clubs"
CARD_TO_REMOVE_RANK = 2
CARD_TO_REMOVE_RANK_STR = "two"

# --- Dice Visuals ---
DICE_SCALE_FACTOR = 0.3

# --- Combat Animation Timings (NEW) ---

DICE_ROLL_DELAY = 350       # Milliseconds between each difference die appearing (NO LONGER USED FOR DIFF DICE)
DICE_SHUFFLE_DELAY = 60     # Milliseconds between danger die shuffle frames
DICE_SHUFFLE_STEPS = 14     # How many times the danger die image changes rapidly
DICE_STOP_DELAY_FRAMES = 4  # Extra shuffle frames between each diff die stopping sequentially


# --- NEW: Sequential Shuffle Steps ---
DICE_BASE_SHUFFLE_STEPS = 10       # Minimum shuffle frames for the first die
DICE_INCREMENTAL_SHUFFLE_STEPS = 4 # Additional frames for each subsequent die
# Example: Die 1: 10 frames, Die 2: 13, Die 3: 16, etc.
# Danger Die will use DICE_BASE_SHUFFLE_STEPS + DICE_INCREMENTAL_SHUFFLE_STEPS for consistency
# ------------------------------------


# --- END OF FILE config.py ---