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
import game_logic
import utils
from card_logic import Card, create_shuffled_deck

# --- NEW Helper Function to Create Tkinter Images ---
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
    assets = {**pil_assets, **tk_assets} # Merge PIL and Tk dictionaries
    # Ensure essential tk images exist before proceeding
    if "tk_photo_back" not in assets:
        print("FATAL ERROR: Tkinter card back image not available after creation.")
        exit()
    tk_photo_back = assets["tk_photo_back"] # Get reference for button creation


    # 5. Setup Layout (needs dimensions from assets)
    grid_frame, info_frame = ui_manager.setup_layout(root, scaled_width, scaled_height)

    # 6. Setup Info Panel Content
    info_text_var = ui_manager.setup_info_panel_content(info_frame)

    # 7. Setup Hand Display (needs dimensions from assets)
    hand_frame, hand_card_slots = ui_manager.setup_hand_display(info_frame, scaled_width, scaled_height)

    # 8. Initialize Game Data Structures
    card_data_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    button_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    card_state_grid = [[config.STATE_ACTION_TAKEN for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    hand_card_data = [[None for _ in range(config.HAND_COLS)] for _ in range(config.HAND_ROWS)]

    # 9. Share necessary state with game_logic module
    # Pass the *complete* assets dictionary
    game_logic.game_state["root"] = root
    game_logic.game_state["assets"] = assets # Now contains both PIL and Tk images
    game_logic.game_state["card_data_grid"] = card_data_grid
    game_logic.game_state["button_grid"] = button_grid
    game_logic.game_state["card_state_grid"] = card_state_grid
    game_logic.game_state["hand_card_data"] = hand_card_data
    game_logic.game_state["hand_card_slots"] = hand_card_slots
    game_logic.game_state["info_frame_bg"] = info_frame.cget('bg')


    # 10. Prepare Deck
    print("Preparing deck...")
    # ... (Deck preparation logic remains the same) ...
    full_deck = create_shuffled_deck()
    try:
        card_to_remove = Card(suit=config.CARD_TO_REMOVE_SUIT, rank=config.CARD_TO_REMOVE_RANK, rank_string=config.CARD_TO_REMOVE_RANK_STR)
        initial_len = len(full_deck)
        full_deck = [card for card in full_deck if card != card_to_remove]
        if len(full_deck) < initial_len: print(f"- Removed: {card_to_remove}")
    except Exception as e: print(f"Warning: Error removing card: {e}")
    black_joker_card = Card(config.BLACK_JOKER_SUIT, config.BLACK_JOKER_RANK, config.BLACK_JOKER_RANK_STR)
    if black_joker_card not in full_deck:
        full_deck.append(black_joker_card)
        print("- Added Black Joker")
        random.shuffle(full_deck)
        print("- Shuffled Black Joker into deck.")
    red_joker_card = Card(config.RED_JOKER_SUIT, config.RED_JOKER_RANK, config.RED_JOKER_RANK_STR)
    print(f"Deck ready for dealing (excluding Red Joker): {len(full_deck)} cards")

    # 11. Deal Cards
    print("Dealing cards...")
    # ... (Dealing logic remains the same) ...
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
    card_data_grid[center_r][center_c] = red_joker_card
    print(f"- Dealt {dealt_count} cards. Total cards on grid: {dealt_count + 1}")

    # 12. Create Grid Buttons (uses tk_photo_back from the complete 'assets')
    print("Creating button grid...")
    # ... (Button creation logic remains the same, uses tk_photo_back) ...
    button_bg = grid_frame.cget('bg')
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            card = card_data_grid[r][c]
            if card is not None:
                button = tk.Button(grid_frame, image=tk_photo_back, # Use loaded tk image
                                   command=lambda row=r, col=c: game_logic.handle_card_click(row, col),
                                   borderwidth=0, highlightthickness=0, relief=tk.FLAT,
                                   bg=button_bg, activebackground=button_bg,
                                   state=tk.NORMAL)
                button.image = tk_photo_back
                button.grid(row=r, column=c, padx=1, pady=1)
                button_grid[r][c] = button
            else:
                placeholder = tk.Frame(grid_frame,
                                       width=scaled_width, height=scaled_height,
                                       bg=grid_frame.cget('bg'))
                placeholder.grid(row=r, column=c, padx=1, pady=1)


    # Optional: Print initial state for debugging
    # utils.simple_print_grid(card_data_grid, title="Card Data Grid (Initial)", cols=config.COLUMNS)
    # utils.simple_print_grid(card_state_grid, title="Card State Grid (Initial)", cols=config.COLUMNS)


    # 13. Start Tkinter Main Loop
    print("Starting Tkinter main loop...")
    root.mainloop()

    print("Window closed.")

# --- Run the application ---
if __name__ == "__main__":
    main()

# --- END OF FILE main.py ---