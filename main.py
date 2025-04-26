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
import game_logic
import card_actions
import combat_manager
import utils
from card_logic import Card, create_shuffled_deck, suits as card_suits, ranks_string as card_ranks_string
from player import Player

# (create_tk_images function remains the same)
def create_tk_images(root, pil_assets):
    """Creates Tkinter PhotoImage objects from loaded PIL images."""
    print("Creating Tkinter PhotoImages...")
    tk_images = {}
    try:
        tk_images["tk_photo_back"] = ImageTk.PhotoImage(pil_assets["card_back_pil_scaled"], master=root)
    except Exception as e: exit(f"FATAL ERROR creating Tkinter image for card back: {e}")

    tk_images["tk_faces"] = {}
    missing_faces = []
    for key, pil_img in pil_assets["pil_faces_scaled"].items():
        try:
            tk_images["tk_faces"][key] = ImageTk.PhotoImage(pil_img, master=root)
        except Exception as e:
            print(f"Warning: Could not create Tkinter image for face {key}: {e}")
            missing_faces.append(key)
    if missing_faces:
        print(f"Warning: Missing Tk face images for: {', '.join(missing_faces)}")
    print(f"- Tkinter PhotoImages created ({len(tk_images['tk_faces'])} faces).")
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
    player_id_text = f"Playing as Jack of {config.PLAYER_SUIT.title()}"
    info_text_var = ui_manager.setup_info_panel_content(info_frame, player_id_text)

    # 7. Setup Hand Display
    hand_frame, hand_card_slots = ui_manager.setup_hand_display(info_frame, scaled_width, scaled_height)

    # 8. Initialize Game State Components
    card_data_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    button_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    # Initialize all states to FACE_DOWN initially, will be set during dealing
    card_state_grid = [[config.STATE_FACE_DOWN for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    hand_card_data = [[None for _ in range(config.HAND_COLS)] for _ in range(config.HAND_ROWS)]

    # Create the Player
    player_start_row = 0 # Placeholder - Adjust based on corner placement rule
    player_start_col = 1
    player = Player(player_start_row, player_start_col)
    player.suit = config.PLAYER_SUIT

    # --- 9. Prepare Deck (MODIFIED - Separate Red Joker, include Black Joker) ---
    print("Preparing deck for the Dungeon...")
    full_deck = create_shuffled_deck() # Start with 52 shuffled
    print(f"- Started with {len(full_deck)} standard cards.")

    # Define cards to remove/exclude
    card_to_remove_obj = Card(suit=config.CARD_TO_REMOVE_SUIT, rank=config.CARD_TO_REMOVE_RANK, rank_string=config.CARD_TO_REMOVE_RANK_STR)
    jack_rank_string = "jack"

    # Build the deck for grid shuffling (excluding Jacks, 2C, and Red Joker initially)
    deck_for_grid = []
    removed_count = 0
    jacks_removed_count = 0
    for card in full_deck:
        is_jack = card.get_rank_string() is not None and card.get_rank_string().lower() == jack_rank_string
        is_two_of_clubs = card == card_to_remove_obj

        if is_jack:
            # print(f"- Excluding Jack: {card}") # Optional log
            jacks_removed_count += 1
        elif is_two_of_clubs:
            # print(f"- Excluding Two of Clubs: {card}") # Optional log
            removed_count += 1
        else:
            deck_for_grid.append(card)

    print(f"- Excluded {jacks_removed_count} Jacks.")
    if removed_count > 0: print(f"- Excluded {card_to_remove_obj}.")
    else: print(f"- Warning: {card_to_remove_obj} not found to exclude.")

    # Create Joker Card objects using corrected rank strings from config
    black_joker_card = Card(config.BLACK_JOKER_SUIT, config.BLACK_JOKER_RANK, config.BLACK_JOKER_RANK_STR)
    red_joker_card = Card(config.RED_JOKER_SUIT, config.RED_JOKER_RANK, config.RED_JOKER_RANK_STR)

    # Add ONLY the Black Joker to the deck to be shuffled for random placement
    deck_for_grid.append(black_joker_card)
    print(f"- Added Black Joker ({black_joker_card}) to the shuffling pool.")

    # Shuffle the deck containing standard cards (minus exclusions) + Black Joker
    random.shuffle(deck_for_grid)
    print(f"- Shuffled the deck for grid placement ({len(deck_for_grid)} cards).")

    # The Red Joker is kept separate for center placement.
    print(f"- Red Joker ({red_joker_card}) kept separate for center placement.")

    expected_grid_deck_size = (config.ROWS * config.COLUMNS) - 1 # Grid size minus the center spot
    if len(deck_for_grid) != expected_grid_deck_size:
        exit(f"FATAL ERROR: Deck size for grid ({len(deck_for_grid)}) doesn't match expected ({expected_grid_deck_size}). Check logic.")
    # --------------------------------------------------------------------------

    # --- 10. Deal Cards (MODIFIED - Place Red Joker in center, deal others) ---
    print(f"Dealing cards onto the {config.ROWS}x{config.COLUMNS} grid...")
    center_r, center_c = config.ROWS // 2, config.COLUMNS // 2
    card_index = 0 # Index for the shuffled deck_for_grid

    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            if r == center_r and c == center_c:
                # Place Red Joker in the center
                card_data_grid[r][c] = red_joker_card
                card_state_grid[r][c] = config.STATE_FACE_DOWN # Ensure center is face down
                print(f"- Placed Red Joker at center ({r},{c}).")
            else:
                # Deal from the shuffled deck (containing Black Joker)
                if card_index < len(deck_for_grid):
                    card_data_grid[r][c] = deck_for_grid[card_index]
                    card_state_grid[r][c] = config.STATE_FACE_DOWN # Ensure non-center is face down
                    card_index += 1
                else:
                    # Error case - should not happen if deck size check passed
                    print(f"ERROR: Ran out of grid deck cards at ({r},{c})!")
                    card_data_grid[r][c] = None
                    card_state_grid[r][c] = config.STATE_ACTION_TAKEN

    total_dealt = card_index + 1 # +1 for the Red Joker
    expected_total = config.ROWS * config.COLUMNS
    if total_dealt == expected_total:
        print(f"- Successfully placed all {total_dealt} cards.")
    else:
        print(f"- Warning: Placed {total_dealt} cards, but expected {expected_total}.")
    # ----------------------------------------------------------------------

    # 11. Create Grid Buttons (Logic remains the same)
    print("Creating button grid...")
    button_bg = grid_frame.cget('bg')
    buttons_created = 0
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            card = card_data_grid[r][c]
            current_state = card_state_grid[r][c]

            # Create button if there's a card and it's face down
            if card is not None and current_state == config.STATE_FACE_DOWN:
                click_command = lambda row=r, col=c: game_logic.handle_card_click(
                    row, col,
                    root, player,
                    card_data_grid, button_grid, card_state_grid,
                    hand_card_data, hand_card_slots,
                    assets, info_frame_bg
                )
                button = tk.Button(grid_frame, image=tk_photo_back,
                                   command=click_command,
                                   borderwidth=0, highlightthickness=0, relief=tk.FLAT,
                                   bg=button_bg, activebackground=button_bg,
                                   state=tk.NORMAL)
                button.image = tk_photo_back
                button.grid(row=r, column=c, padx=1, pady=1)
                button_grid[r][c] = button
                buttons_created += 1
            else:
                # Should only happen if dealing failed somehow
                print(f"Warning: No button created for grid cell ({r},{c}). Card: {card}, State: {current_state}")
                placeholder = tk.Frame(grid_frame, width=scaled_width, height=scaled_height, bg=grid_frame.cget('bg'))
                placeholder.grid(row=r, column=c, padx=1, pady=1)
                button_grid[r][c] = None
    print(f"- Created {buttons_created} buttons.")

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