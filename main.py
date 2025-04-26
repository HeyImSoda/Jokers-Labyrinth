# --- START OF FILE main.py ---

import tkinter as tk
from PIL import ImageTk
import random
import time

# --- Local Modules ---
import config
import assets_manager
import ui_manager
import animation
import hand_manager
import game_logic       # Handles initial click routing
import card_actions     # Handles actions on revealed cards
import combat_manager   # Import the new combat module (though not used directly here)
import utils
from card_logic import Card, create_shuffled_deck
from player import Player

# (create_tk_images function remains the same)
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

    print("- Tkinter PhotoImages created.")
    return tk_images

# --- Main Application Setup ---
def main():
    # 1. Create Main Window
    root = ui_manager.create_main_window()

    # 2. Load PIL Assets
    pil_assets = assets_manager.load_pil_assets()
    scaled_width = pil_assets["width"]
    scaled_height = pil_assets["height"]

    # 3. Create Tkinter Images
    tk_assets = create_tk_images(root, pil_assets)

    # 4. Combine Assets
    assets = {**pil_assets, **tk_assets}
    if "tk_photo_back" not in assets: exit("FATAL ERROR: Tkinter card back image missing.")
    tk_photo_back = assets["tk_photo_back"]

    # 5. Setup Layout
    grid_frame, info_frame = ui_manager.setup_layout(root, scaled_width, scaled_height)
    info_frame_bg = info_frame.cget('bg')

    # 6. Setup Info Panel
    info_text_var = ui_manager.setup_info_panel_content(info_frame)

    # 7. Setup Hand Display
    hand_frame, hand_card_slots = ui_manager.setup_hand_display(info_frame, scaled_width, scaled_height)

    # 8. Initialize Game State Components
    card_data_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    button_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    card_state_grid = [[config.STATE_ACTION_TAKEN for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    hand_card_data = [[None for _ in range(config.HAND_COLS)] for _ in range(config.HAND_ROWS)]

    # --- Create the Player ---
    player_start_row = config.ROWS // 2
    player_start_col = (config.COLUMNS // 2) - 1
    player = Player(player_start_row, player_start_col)
    # --- ADD PLAYER SUIT (Needed for Hostile NPC check) ---
    player.suit = config.PLAYER_SUIT # Assign the suit from config to the player instance
    # -----------------------------------------------------

    # 9. Prepare Deck (Logic remains the same)
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
    # Red Joker is handled separately
    red_joker_card = Card(config.RED_JOKER_SUIT, config.RED_JOKER_RANK, config.RED_JOKER_RANK_STR)
    print(f"Deck ready for dealing (excluding Red Joker): {len(full_deck)} cards")


    # 10. Deal Cards (Logic remains the same)
    print("Dealing cards...")
    center_r, center_c = config.ROWS // 2, config.COLUMNS // 2
    card_index = 0
    dealt_count = 0
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            if r == center_r and c == center_c:
                card_state_grid[r][c] = config.STATE_FACE_DOWN
                continue
            if card_index < len(full_deck):
                card_data_grid[r][c] = full_deck[card_index]
                card_state_grid[r][c] = config.STATE_FACE_DOWN
                card_index += 1
                dealt_count += 1
            else:
                card_state_grid[r][c] = config.STATE_ACTION_TAKEN
    card_data_grid[center_r][center_c] = red_joker_card
    print(f"- Dealt {dealt_count} cards. Red Joker placed in center. Total active cards: {dealt_count + 1}")

    # 11. Create Grid Buttons (Lambda passes all necessary state)
    print("Creating button grid...")
    button_bg = grid_frame.cget('bg')
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            card = card_data_grid[r][c]
            current_state = card_state_grid[r][c]

            if card is not None and current_state == config.STATE_FACE_DOWN:
                # Lambda captures all state needed by handle_card_click -> handle_card_action -> initiate_combat
                click_command = lambda row=r, col=c: game_logic.handle_card_click(
                    row, col,
                    root, player, # Core components (incl player with suit)
                    card_data_grid, button_grid, card_state_grid, # Grids
                    hand_card_data, hand_card_slots, # Hand components
                    assets, info_frame_bg # UI/Asset components
                )

                button = tk.Button(grid_frame, image=tk_photo_back,
                                   command=click_command,
                                   borderwidth=0, highlightthickness=0, relief=tk.FLAT,
                                   bg=button_bg, activebackground=button_bg,
                                   state=tk.NORMAL)
                button.image = tk_photo_back
                button.grid(row=r, column=c, padx=1, pady=1)
                button_grid[r][c] = button
            else:
                # Placeholder Frame
                placeholder = tk.Frame(grid_frame, width=scaled_width, height=scaled_height, bg=grid_frame.cget('bg'))
                placeholder.grid(row=r, column=c, padx=1, pady=1)
                button_grid[r][c] = None

    # Optional Debug Prints
    # utils.simple_print_grid(card_data_grid, title="Card Data Grid (Initial)", cols=config.COLUMNS)
    # utils.simple_print_grid(card_state_grid, title="Card State Grid (Initial)", cols=config.COLUMNS)

    # 12. Start Main Loop
    print("Starting Tkinter main loop...")
    root.mainloop()
    print("Window closed.")

# --- Run ---
if __name__ == "__main__":
    main()

# --- END OF FILE main.py ---