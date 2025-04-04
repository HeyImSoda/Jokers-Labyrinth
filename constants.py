# constants.py
import os

# --- Screen Dimensions ---
SCREEN_WIDTH = 1920  # Adjust to a larger width
SCREEN_HEIGHT = 1080  # Adjust to a larger height
BOARD_AREA_WIDTH = 900  # Adjusted board area width
BOARD_AREA_HEIGHT = 900  # Adjusted board area height
HAND_AREA_HEIGHT = 200  # Increased hand area height
INFO_AREA_WIDTH = SCREEN_WIDTH - BOARD_AREA_WIDTH

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 150, 0)
BLUE = (0, 0, 200)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)
GOLD = (255, 215, 0)
LIGHT_GREEN = (150, 200, 150)
DARK_GREEN = (0, 100, 0)
INFO_PANEL_BG = (30, 30, 50)
HAND_AREA_BG = (40, 40, 40)

# --- Board Settings ---
GRID_ROWS = 7
GRID_COLS = 7
GRID_MARGIN = 5

# --- Card Asset Settings ---
CARD_ASSET_PATH = 'assets'
CARD_FACES_PATH = os.path.join(CARD_ASSET_PATH, 'card_faces')
CARD_BACK_PATH = os.path.join(CARD_ASSET_PATH, 'card_back.png')
JOKER_PATH = os.path.join(CARD_ASSET_PATH, 'jokers')

# --- Game Card Dimensions ---
CARD_WIDTH = 80  # Increased card size
CARD_HEIGHT = 120

# --- Player Settings ---
PLAYER_TOKEN_RADIUS = 15
PLAYER_COLORS = [(255, 50, 50), (50, 100, 255), (50, 200, 50), (255, 215, 0)]  # Brighter colors

# --- Game Settings ---
FPS = 60
STARTING_ACTIONS = 2
GAME_MODES = ["standard", "advanced", "expedition"]

# --- Card Types ---
TYPE_EQUIPMENT = "Equipment"
TYPE_HAZARD = "Hazard"
TYPE_NPC = "NPC"
TYPE_ACE = "Ace"
TYPE_QUEEN = "Queen"
TYPE_KING = "King"
TYPE_JACK = "Jack"
TYPE_JOKER = "Joker"

# --- Suits & Ranks ---
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
RANK_MAPPING = {
    "Ace": "ace",
    "2": "two",
    "3": "three", 
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "10": "ten",
    "Jack": "jack",
    "Queen": "queen",
    "King": "king"
}

# --- Animation ---
FLIP_SPEED = 10  # Slightly faster flip
ANIMATION_SPEED = 8  # For general animations

# --- UI Elements ---
BUTTON_BG = (80, 80, 120)
BUTTON_HOVER = (100, 100, 160)
BUTTON_TEXT = WHITE
BUTTON_BORDER_RADIUS = 10

# --- Font Settings ---
FONT_LARGE = 60
FONT_MEDIUM = 28
FONT_SMALL = 20