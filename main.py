# --- START OF FILE main.py ---

import tkinter as tk
from PIL import ImageTk # Need ImageTk here now
import random
import time

# --- Local Modules ---
import config
import assets_manager # Will load PIL assets
import ui_manager
import animation
import hand_manager
import game_logic       # Handles initial click routing
import card_actions     # Handles actions on revealed cards
import utils
from card_logic import Card, create_shuffled_deck
from player import Player # Import the new Player class

# --- NEW Helper Function to Create Tkinter Images ---
# (Keep create_tk_images function as it was)
def create_tk_images(root, pil_assets):
    """Creates Tkinter PhotoImage objects from loaded PIL images."""
    print("Creating Tkinter PhotoImages...")
    tk_images = {}
    # Create Tkinter image for card back
    try:
        tk_images["tk_photo_back"] = ImageTk.PhotoImage(pil_assets["card_back_pil_scaled"], master=root)
    except Exception as e:
        print(f"FATAL ERROR creating Tkinter image for card back: {e}")
        exit()

    # Create Tkinter images for card faces
    tk_images["tk_faces"] = {}
    for key, pil_img in pil_assets["pil_faces_scaled"].items():
        try:
            tk_images["tk_faces"][key] = ImageTk.PhotoImage(pil_img, master=root)
        except Exception as e:
            print(f"Warning: Could not create Tkinter image for face {key}: {e}")
            # Decide how to handle missing face images - skip? placeholder? exit?
            # For now, we just won't have that image in tk_faces

    print("- Tkinter PhotoImages created.")
    return tk_images


# --- Main Application Setup ---
def main():
    # 1. Create Main Window FIRST
    root = ui_manager.create_main_window()

    # 2. Load PIL Assets
    pil_assets = assets_manager.load_pil_assets() # Loads only PIL images now
    scaled_width = pil_assets["width"]
    scaled_height = pil_assets["height"]

    # 3. Create Tkinter Images (using the root window and PIL assets)
    tk_assets = create_tk_images(root, pil_assets)

    # 4. Combine all assets into a single dictionary
    # This 'assets' dict holds both PIL and Tk images, plus dimensions
    assets = {**pil_assets, **tk_assets}
    if "tk_photo_back" not in assets:
        print("FATAL ERROR: Tkinter card back image not available after creation.")
        exit()
    tk_photo_back = assets["tk_photo_back"] # Get reference for button creation

    # 5. Setup Layout (needs dimensions from assets)
    grid_frame, info_frame = ui_manager.setup_layout(root, scaled_width, scaled_height)
    info_frame_bg = info_frame.cget('bg') # Store info frame background color

    # 6. Setup Info Panel Content
    info_text_var = ui_manager.setup_info_panel_content(info_frame)

    # 7. Setup Hand Display (needs dimensions from assets)
    hand_frame, hand_card_slots = ui_manager.setup_hand_display(info_frame, scaled_width, scaled_height)

    # --- 8. Initialize Game State Components (managed here in main) ---
    card_data_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    button_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    # Initialize state grid - center is FACE_DOWN (Red Joker), others ACTION_TAKEN until dealt
    card_state_grid = [[config.STATE_ACTION_TAKEN for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    hand_card_data = [[None for _ in range(config.HAND_COLS)] for _ in range(config.HAND_ROWS)]

    # --- Create the Player ---
    # Player starts near the center, but not on it (e.g., one step away)
    player_start_row = config.ROWS // 2
    player_start_col = (config.COLUMNS // 2) -1 # Start left of center
    player = Player(player_start_row, player_start_col)
    # Future: Add visual representation of player on the grid_frame

    # --- No longer using game_logic.game_state dictionary ---

    # 9. Prepare Deck
    print("Preparing deck...")
    full_deck = create_shuffled_deck()
    # Remove specific card
    try:
        card_to_remove = Card(suit=config.CARD_TO_REMOVE_SUIT, rank=config.CARD_TO_REMOVE_RANK, rank_string=config.CARD_TO_REMOVE_RANK_STR)
        initial_len = len(full_deck)
        full_deck = [card for card in full_deck if card != card_to_remove]
        if len(full_deck) < initial_len: print(f"- Removed: {card_to_remove}")
        else: print(f"- Card to remove ({card_to_remove}) not found in deck.")
    except Exception as e: print(f"Warning: Error removing card: {e}")
    # Add Black Joker
    black_joker_card = Card(config.BLACK_JOKER_SUIT, config.BLACK_JOKER_RANK, config.BLACK_JOKER_RANK_STR)
    if black_joker_card not in full_deck:
        full_deck.append(black_joker_card)
        print("- Added Black Joker")
        random.shuffle(full_deck)
        print("- Shuffled Black Joker into deck.")
    else: print("- Black Joker already in deck?")
    # Red Joker is handled separately (placed in center)
    red_joker_card = Card(config.RED_JOKER_SUIT, config.RED_JOKER_RANK, config.RED_JOKER_RANK_STR)
    print(f"Deck ready for dealing (excluding Red Joker): {len(full_deck)} cards")


    # 10. Deal Cards
    print("Dealing cards...")
    center_r, center_c = config.ROWS // 2, config.COLUMNS // 2
    card_index = 0
    dealt_count = 0
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            # Skip center - Red Joker goes there
            if r == center_r and c == center_c:
                card_state_grid[r][c] = config.STATE_FACE_DOWN # Center starts face down
                continue
            # Deal from prepared deck
            if card_index < len(full_deck):
                card_data_grid[r][c] = full_deck[card_index]
                card_state_grid[r][c] = config.STATE_FACE_DOWN # Dealt cards are face down
                card_index += 1
                dealt_count += 1
            else:
                # Should not happen if ROWS*COLUMNS-1 <= len(full_deck)
                print(f"Warning: Ran out of cards in deck while dealing at ({r},{c})")
                card_state_grid[r][c] = config.STATE_ACTION_TAKEN # Mark empty slot as taken

    # Place Red Joker in the center
    card_data_grid[center_r][center_c] = red_joker_card
    print(f"- Dealt {dealt_count} cards. Red Joker placed in center. Total active cards: {dealt_count + 1}")


    # 11. Create Grid Buttons
    print("Creating button grid...")
    button_bg = grid_frame.cget('bg')
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            card = card_data_grid[r][c]
            current_state = card_state_grid[r][c]

            if card is not None and current_state == config.STATE_FACE_DOWN:
                # --- IMPORTANT: Lambda now captures all needed state for the handler ---
                # Pass all necessary components from main's scope to handle_card_click
                click_command = lambda row=r, col=c: game_logic.handle_card_click(
                    row, col,
                    root, player, # Core components
                    card_data_grid, button_grid, card_state_grid, # Grids
                    hand_card_data, hand_card_slots, # Hand components
                    assets, info_frame_bg # UI/Asset components
                )

                button = tk.Button(grid_frame, image=tk_photo_back, # Use loaded tk image
                                   command=click_command, # Use the lambda capturing state
                                   borderwidth=0, highlightthickness=0, relief=tk.FLAT,
                                   bg=button_bg, activebackground=button_bg,
                                   state=tk.NORMAL) # Start enabled if face down
                button.image = tk_photo_back # Keep reference
                button.grid(row=r, column=c, padx=1, pady=1)
                button_grid[r][c] = button
            else:
                # Create a placeholder for empty slots or already processed cards
                # Check if it's the initial empty center or a dealt card that failed etc.
                bg_color = grid_frame.cget('bg') # Use grid background for placeholders
                placeholder = tk.Frame(grid_frame,
                                       width=scaled_width, height=scaled_height,
                                       bg=bg_color)
                placeholder.grid(row=r, column=c, padx=1, pady=1)
                # Ensure button_grid entry is None for non-button slots
                button_grid[r][c] = None


    # Optional: Print initial state for debugging
    utils.simple_print_grid(card_data_grid, title="Card Data Grid (Initial)", cols=config.COLUMNS)
    # utils.simple_print_grid(card_state_grid, title="Card State Grid (Initial)", cols=config.COLUMNS)


    # 12. Start Tkinter Main Loop
    print("Starting Tkinter main loop...")
    root.mainloop()

    print("Window closed.")

# --- Run the application ---
if __name__ == "__main__":
    main()

# --- END OF FILE main.py ---