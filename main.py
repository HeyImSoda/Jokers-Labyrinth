# main.py
import pygame
import sys
import random
import os
import time # For potential delays
from constants import *
from card import Card, Deck
from player import Player
from board import Board

# --- Asset Loading Function ---
def load_individual_card_images():
    """Loads all card face and back images from individual PNG files."""
    images = {}
    
    try:
        # Check if asset directories exist
        if not os.path.exists(CARD_ASSET_PATH):
            print(f"Creating directory: {CARD_ASSET_PATH}")
            os.makedirs(CARD_ASSET_PATH)
        if not os.path.exists(CARD_FACES_PATH):
            print(f"Creating directory: {CARD_FACES_PATH}")
            os.makedirs(CARD_FACES_PATH)
        if not os.path.exists(JOKER_PATH):
            print(f"Creating directory: {JOKER_PATH}")
            os.makedirs(JOKER_PATH)
    except Exception as e:
        print(f"Error creating asset directories: {e}")
    
    print(f"Loading card images from: {CARD_FACES_PATH}")
    
    # Load card back image
    try:
        if os.path.exists(CARD_BACK_PATH):
            card_back = pygame.image.load(CARD_BACK_PATH).convert_alpha()
            card_back = pygame.transform.scale(card_back, (CARD_WIDTH, CARD_HEIGHT))
            images["card_back"] = card_back
            print(f"Loaded card back from: {CARD_BACK_PATH}")
        else:
            print(f"Warning: Card back image not found at {CARD_BACK_PATH}")
            # Create placeholder card back
            card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            card_back.fill(BLUE)
            images["card_back"] = card_back
    except Exception as e:
        print(f"Error loading card back: {e}")
        # Create placeholder card back
        card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        card_back.fill(BLUE)
        images["card_back"] = card_back
    
    # Load regular card faces (using SUITS and RANKS from constants)
    for suit in SUITS:
        suit_lower = suit.lower()
        for rank in RANKS:
            if rank != "Jack":  # Exclude Jacks as they're special in this game
                rank_key = RANK_MAPPING.get(rank, rank.lower())
                card_filename = f"{suit_lower}_{rank_key}.png"
                card_path = os.path.join(CARD_FACES_PATH, card_filename)
                
                try:
                    if os.path.exists(card_path):
                        card_image = pygame.image.load(card_path).convert_alpha()
                        card_image = pygame.transform.scale(card_image, (CARD_WIDTH, CARD_HEIGHT))
                        card_key = f"{suit_lower}_{rank_key}"
                        images[card_key] = card_image
                        print(f"Loaded card: {card_key}")
                    else:
                        print(f"Warning: Card image not found at {card_path}")
                        # Create placeholder card with text
                        card_image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
                        card_image.fill(WHITE)
                        card_key = f"{suit_lower}_{rank_key}"
                        images[card_key] = card_image
                except Exception as e:
                    print(f"Error loading {card_path}: {e}")
                    # Create placeholder
                    card_image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
                    card_image.fill(WHITE)
                    card_key = f"{suit_lower}_{rank_key}"
                    images[card_key] = card_image
    
    # Load Jokers
    for joker_num in [1, 2]:
        joker_filename = f"joker_{joker_num}.png"
        joker_path = os.path.join(JOKER_PATH, joker_filename)
        
        try:
            if os.path.exists(joker_path):
                joker_image = pygame.image.load(joker_path).convert_alpha()
                joker_image = pygame.transform.scale(joker_image, (CARD_WIDTH, CARD_HEIGHT))
                images[f"joker_{joker_num}"] = joker_image
                print(f"Loaded joker: joker_{joker_num}")
            else:
                print(f"Warning: Joker image not found at {joker_path}")
                # Create placeholder joker
                joker_image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
                joker_image.fill(GOLD)
                images[f"joker_{joker_num}"] = joker_image
        except Exception as e:
            print(f"Error loading {joker_path}: {e}")
            # Create placeholder
            joker_image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            joker_image.fill(GOLD)
            images[f"joker_{joker_num}"] = joker_image
    
    print(f"Finished loading card images. Total loaded: {len(images)}")
    if "card_back" not in images:
        print("CRITICAL WARNING: Card back image failed to load!")
    
    return images

# --- Pygame Initialization ---
pygame.init()
# Font initialization
if not pygame.font.get_init():
    pygame.font.init()

# Set up the display with proper dimensions
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Joker's Labyrinth")

clock = pygame.time.Clock()
try:
    game_font = pygame.font.SysFont("Arial", 24) # Primary font
    title_font = pygame.font.SysFont("Impact", 60) # Font for titles
except Exception as e:
    print(f"Warning: Could not load system fonts ({e}). Using pygame default.")
    game_font = pygame.font.Font(None, 30) # Pygame's default font
    title_font = pygame.font.Font(None, 70)

# --- Asset Loading ---
print("Loading assets...")
CARD_IMAGES = load_individual_card_images() # Call the new function
if not CARD_IMAGES or "card_back" not in CARD_IMAGES: # Check critical load failure
    print("CRITICAL ERROR: Failed to load card images or card back. Check constants.py and asset path. Exiting.")
    pygame.quit()
    sys.exit()
print("Assets loaded.")

# --- Game State Variables ---
game_state = "menu" # "menu", "setup", "playing", "combat", "game_over"
players = []
current_player_index = 0
board = Board(CARD_IMAGES) # Create Board instance, passing the loaded images
selected_card_hand = None # Track which card in hand is clicked
card_being_flipped = None # Track card during flip animation for interaction
action_in_progress = False # Prevent multiple actions from one click during animation
message = "Welcome! Select a game mode." # Display messages to the player
winner = None

# --- UI Positioning ---
# Board positioning (allows margin around it)
board_margin_x = (BOARD_AREA_WIDTH - board.board_rect.width) // 2 + 10 # Center board within its area
board_margin_y = (SCREEN_HEIGHT - board.board_rect.height) // 2
board.board_rect.topleft = (board_margin_x, board_margin_y)

# Define other UI areas using the constants
info_area_rect = pygame.Rect(
    BOARD_AREA_WIDTH + 20,  # Start to the right of the board area
    20,  # Start near the top of the screen
    INFO_AREA_WIDTH - 40,  # Use the defined width for the info area
    SCREEN_HEIGHT - HAND_AREA_HEIGHT - 40  # Height excluding hand area
)

hand_area_rect = pygame.Rect(
    BOARD_AREA_WIDTH + 20,  # Start to the right of the board area
    SCREEN_HEIGHT - HAND_AREA_HEIGHT - 10,  # Start above the bottom of the screen
    INFO_AREA_WIDTH - 40,  # Use the remaining width
    HAND_AREA_HEIGHT  # Use the defined height for the hand area
)

# --- Helper Functions ---
def draw_text(text, font, color, surface, x, y, center=False, wrap_width=None):
    """Draws text, optionally centered or wrapped."""
    if wrap_width:
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            test_text_surf = font.render(test_line, True, color)
            if test_text_surf.get_width() <= wrap_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line) # Add the last line

        line_height = font.get_linesize()
        for i, line in enumerate(lines):
            textobj = font.render(line, True, color)
            textrect = textobj.get_rect()
            if center: textrect.center = (x, y + i * line_height)
            else: textrect.topleft = (x, y + i * line_height)
            surface.blit(textobj, textrect)
    else:
        textobj = font.render(text, True, color)
        textrect = textobj.get_rect()
        if center: textrect.center = (x, y)
        else: textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

def get_player_by_id(player_id):
    """Finds a player object by their ID."""
    for p in players:
        if p.id == player_id:
            return p
    return None

def next_turn():
    """Advances the game to the next player's turn."""
    global current_player_index, message, selected_card_hand, action_in_progress, card_being_flipped
    if not players: return # Should not happen
    players[current_player_index].is_turn = False
    current_player_index = (current_player_index + 1) % len(players)
    players[current_player_index].is_turn = True
    players[current_player_index].actions_left = STARTING_ACTIONS
    message = f"Player {players[current_player_index].id + 1}'s Turn ({players[current_player_index].jack_suit})"
    selected_card_hand = None # Deselect hand card
    action_in_progress = False # Reset action lock
    card_being_flipped = None # Clear flipping card tracker
    print(f"\n--- {message} ---") # Console output for turn change

def handle_post_flip_interaction(player, card, row, col):
    global message, game_state, winner, action_in_progress, card_being_flipped
    print(f"Post-flip interaction with {card} at ({row}, {col})")

    if card.card_type == TYPE_EQUIPMENT:
        message = f"Revealed Equipment: {card}. Added to hand."
        board.remove_card_at(row, col)
        player.add_card_to_hand(card)
    # Handle other card types...

def handle_move_interaction(player, card, row, col):
    """Handles interactions when a player *moves onto* a revealed card's space."""
    global message, game_state, winner, action_in_progress
    print(f"Move interaction with {card} at ({row}, {col})")

    interaction_message = ""
    should_end_turn = False
    lost_action = True # Moving always costs an action

    # --- Determine Interaction Type ---
    if card.card_type == TYPE_EQUIPMENT:
        interaction_message = f"Picked up Equipment: {card}."
        board.remove_card_at(row, col) # Remove from board
        player.add_card_to_hand(card) # Add to hand
        player.position = (row, col) # Finalize move

    elif card.card_type == TYPE_JOKER:
        interaction_message = f"Moved onto Joker space. Collected (Standard Mode)."
        board.remove_card_at(row, col)
        player.add_card_to_hand(card)
        player.position = (row, col)
        # Check win condition
        if player.check_win_condition():
             game_state = "game_over"
             winner = player
             message = f"Player {player.id + 1} found both Jokers!"
             return

    elif card.card_type == TYPE_NPC:
        is_friendly = card.suit == player.jack_suit
        if is_friendly:
             interaction_message = f"Moved onto friendly {card.rank}. Added to hand."
             board.remove_card_at(row, col)
             player.add_card_to_hand(card)
             player.position = (row, col)
        else: # Hostile NPC - Should have been blocked by can_move_to, but check again
             interaction_message = f"Blocked by hostile {card.rank}! Cannot move here without fighting."
             print("Error: Player somehow tried to move onto hostile NPC space.")
             lost_action = False # Penalize move attempt? Or refund action? Let's refund for now.

    elif card.card_type == TYPE_HAZARD:
         interaction_message = f"Moved onto Hazard: {card}! Must Fight (Not Implemented)."
         # TODO: Initiate Combat
         print("Combat initiation needed!")
         # Player technically occupies space, but combat needs resolving
         player.position = (row, col)

    elif card.card_type == TYPE_ACE:
         interaction_message = f"Moved onto Ace: {card}."
         # No pickup in standard mode, player just occupies space
         player.position = (row, col)

    else: # Jack or Unknown - Player just occupies space
         interaction_message = f"Moved onto {card}."
         player.position = (row, col)

    # --- Update Game State ---
    message = interaction_message
    if lost_action:
         player.actions_left -= 1
         print(f"Action used for move. Actions left: {player.actions_left}")

    if player.actions_left <= 0 and game_state == "playing":
         should_end_turn = True

    # Reset action lock
    action_in_progress = False

    if should_end_turn:
         next_turn()

def handle_mouse_click(pos):
    """Handles mouse click events based on the current game state."""
    global game_state, selected_card_hand, card_being_flipped, action_in_progress, message
    
    if action_in_progress:
        print("Action in progress, ignoring click")
        return
    
    if game_state == "menu":
        # Handle menu clicks
        # Example: Start button check
        start_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 50, 200, 50)
        if start_btn.collidepoint(pos):
            game_state = "setup"
            setup_game("standard")  # Default to standard mode
    
    elif game_state == "playing":
        current_player = players[current_player_index]
        
        # Check if click is on a card in the grid
        grid_pos = board.get_grid_pos_from_screen(pos[0], pos[1])
        if grid_pos:
            row, col = grid_pos
            card = board.get_card_at(row, col)
            
            if card and not card.is_animating_flip and current_player.actions_left > 0:
                # Case 1: Card is face-down, try to reveal it
                if not card.is_face_up and current_player.can_reveal(grid_pos, board):
                    print(f"Player {current_player.id + 1} revealing card at {grid_pos}")
                    action_in_progress = True
                    card.start_flip()
                    card_being_flipped = (card, row, col)
                    current_player.actions_left -= 1
                    
                # Case 2: Card is face-up, try to move onto it
                elif card.is_face_up and current_player.can_move_to(grid_pos, board):
                    print(f"Player {current_player.id + 1} moving to {grid_pos}")
                    handle_move_interaction(current_player, card, row, col)
                
                # Case 3: Card is face-up and player wants to fight it
                elif card.is_face_up and current_player.can_fight(grid_pos, board):
                    print(f"Player {current_player.id + 1} initiating combat at {grid_pos}")
                    # TODO: Implement combat logic
                    message = f"Combat not implemented yet!"
                
                else:
                    message = "Cannot interact with that card!"
        
        # Check if click is on a card in hand (not implemented in this fix)
        # ...
        
        # Check if click is on an "end turn" button
        end_turn_btn = pygame.Rect(info_area_rect.x + 20, info_area_rect.y + 250, 120, 40)
        if end_turn_btn.collidepoint(pos):
            next_turn()

def update_game():
    """Updates game state, handles animations, etc."""
    global card_being_flipped, action_in_progress, message
    
    # Update all cards on the board
    board.update_cards()
    
    # Check if a card is done flipping
    if card_being_flipped:
        card, row, col = card_being_flipped
        if not card.is_animating_flip:
            player = players[current_player_index]
            handle_post_flip_interaction(player, card, row, col)
            card_being_flipped = None
            action_in_progress = False
            
            # Check if player's turn is over
            if player.actions_left <= 0 and game_state == "playing":
                message += " - Turn ending."
                # Allow the message to show for a moment before changing turns
                pygame.display.flip()  # Update display
                pygame.time.delay(1000)  # Delay for 1 second
                next_turn()

def draw_game():
    """Draws the game according to the current game state."""
    screen.fill(WHITE)
    
    if game_state == "menu":
        # Draw menu UI
        title_text = "Joker's Labyrinth"
        draw_text(title_text, title_font, BLACK, screen, SCREEN_WIDTH//2, SCREEN_HEIGHT//4, center=True)
        
        start_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 50, 200, 50)
        pygame.draw.rect(screen, BUTTON_BG, start_btn, 0, BUTTON_BORDER_RADIUS)
        draw_text("Start Game", game_font, WHITE, screen, start_btn.centerx, start_btn.centery, center=True)
        
    elif game_state in ["setup", "playing", "combat", "game_over"]:
        # Draw board
        screen.fill(DARK_GREEN, (0, 0, BOARD_AREA_WIDTH, SCREEN_HEIGHT))
        board.draw(screen)
        
        # Draw UI areas
        pygame.draw.rect(screen, INFO_PANEL_BG, info_area_rect)
        pygame.draw.rect(screen, HAND_AREA_BG, hand_area_rect)
        
        # Draw player tokens on the board
        for player in players:
            player.update_token_position(board.board_rect.left, board.board_rect.top)
            player.draw_token(screen)
        
        # Draw current player's hand
        if players and game_state != "setup":
            players[current_player_index].draw_hand(screen, hand_area_rect)
        
        # Draw game info
        if players and game_state != "setup":
            current_player = players[current_player_index]
            draw_text(f"Player {current_player.id + 1}'s Turn ({current_player.jack_suit})", 
                     game_font, WHITE, screen, info_area_rect.x + 10, info_area_rect.y + 10)
            draw_text(f"Actions Left: {current_player.actions_left}", 
                     game_font, WHITE, screen, info_area_rect.x + 10, info_area_rect.y + 40)
            draw_text(message, game_font, WHITE, screen, info_area_rect.x + 10, 
                     info_area_rect.y + 80, wrap_width=info_area_rect.width - 20)
            
            # Draw "End Turn" button
            end_turn_btn = pygame.Rect(info_area_rect.x + 20, info_area_rect.y + 250, 120, 40)
            pygame.draw.rect(screen, BUTTON_BG, end_turn_btn, 0, BUTTON_BORDER_RADIUS)
            draw_text("End Turn", game_font, WHITE, screen, end_turn_btn.centerx, end_turn_btn.centery, center=True)
        
        if game_state == "game_over" and winner:
            win_text = f"Player {winner.id + 1} Wins!"
            draw_text(win_text, title_font, GOLD, screen, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, center=True)

def setup_game(game_mode):
    """Sets up a new game with the specified mode."""
    global players, current_player_index, board, game_state, message
    
    # Clear any existing game data
    players = []
    current_player_index = 0
    
    # Set up the board
    jacks = board.setup_board(game_mode)
    if not jacks:
        print("Failed to set up board. Returning to menu.")
        game_state = "menu"
        message = "Error setting up game. Please try again."
        return
    
    # Create 4 players with different Jacks
    for i in range(4):
        jack_card = jacks[i] if i < len(jacks) else None
        if jack_card:
            player = Player(i, jack_card.suit, PLAYER_COLORS[i], CARD_IMAGES)
            players.append(player)
    
    # Set first player active
    players[0].is_turn = True
    players[0].actions_left = STARTING_ACTIONS
    
    # Set all players at the central Joker
    center = (GRID_ROWS // 2, GRID_COLS // 2)
    for player in players:
        player.position = center
    
    game_state = "playing"
    message = f"Game started! Player 1's turn ({players[0].jack_suit})"
    print("\n--- GAME STARTED ---")
    print(message)

# --- Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Handle mouse clicks
            handle_mouse_click(event.pos)
    
    # Update game state
    update_game()
    
    # Draw everything
    draw_game()
    
    # Update display
    pygame.display.flip()
    clock.tick(FPS)

# --- Quit Pygame ---
print("Exiting game.")
pygame.quit()
sys.exit()