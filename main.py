# --- START OF FILE main.py ---

import tkinter as tk
from PIL import ImageTk
import random
import time

# --- Local Modules ---
import config
import assets_manager
import ui_manager
# Removed animation, hand_manager, combat_manager direct imports here if not used directly in main
import game_logic
# import card_actions # Imported by game_logic
import utils
from card_logic import Card, create_shuffled_deck # Keep specific imports
from player import Player

# --- Helper Function to Create Tkinter Images (Cards & Dice) ---
# (This function remains the same)
def create_tk_images(root, pil_assets):
    """Creates Tkinter PhotoImage objects from loaded PIL images (cards and dice)."""
    print("Creating Tkinter PhotoImages...")
    tk_images = {}

    # Card Back
    try:
        if "card_back_pil_scaled" not in pil_assets or pil_assets["card_back_pil_scaled"] is None:
             raise ValueError("Scaled PIL card back image is missing in assets.")
        tk_images["tk_photo_back"] = ImageTk.PhotoImage(pil_assets["card_back_pil_scaled"], master=root)
    except Exception as e: exit(f"FATAL ERROR creating Tkinter image for card back: {e}")

    # Card Faces
    tk_images["tk_faces"] = {}
    missing_faces = []
    pil_faces = pil_assets.get("pil_faces_scaled", {})
    for key, pil_img in pil_faces.items():
        if pil_img is None: # Skip if PIL loading failed for this key
             print(f"Skipping Tk image creation for face '{key}' due to missing PIL image.")
             missing_faces.append(key)
             continue
        try:
            tk_images["tk_faces"][key] = ImageTk.PhotoImage(pil_img, master=root)
        except Exception as e:
            print(f"Warning: Could not create Tkinter image for face {key}: {e}")
            missing_faces.append(key)
    if missing_faces: print(f"Warning: Missing/failed Tk face images for: {', '.join(missing_faces)}")
    print(f"- Tk Card Faces created ({len(tk_images['tk_faces'])}).")

    # Dice Faces (including icon)
    tk_images["tk_dice"] = {}
    pil_dice = pil_assets.get("pil_dice_scaled", {})
    for value, pil_img in pil_dice.items():
         if pil_img is None: # Skip if PIL loading failed for this key
             print(f"Skipping Tk image creation for dice '{value}' due to missing PIL image.")
             continue
         try:
            tk_images["tk_dice"][value] = ImageTk.PhotoImage(pil_img, master=root)
         except Exception as e:
            print(f"Warning: Could not create Tkinter image for dice face {value}: {e}")
    print(f"- Tk Dice Faces created ({len(tk_images['tk_dice'])}).")

    return tk_images

# --- UI State Management Helpers ---
# Keep track of the currently displayed combat view frame
current_combat_view = None

def hide_hand(hand_frame):
    """Hides the hand display."""
    if hand_frame and hand_frame.winfo_ismapped():
        print("Hiding hand frame.")
        hand_frame.pack_forget()

def show_hand(hand_frame):
    """Shows the hand display."""
    if hand_frame and not hand_frame.winfo_ismapped():
        print("Showing hand frame.")
        # Re-pack it where it belongs (adjust if layout changes)
        hand_frame.pack(pady=(40, 20), anchor='n')

def disable_grid(button_grid):
    """Disables all buttons currently in the grid."""
    print("Disabling grid buttons.")
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            button = button_grid[r][c]
            if button and isinstance(button, tk.Button) and button.winfo_exists():
                button.config(state=tk.DISABLED)

def enable_grid(button_grid, card_state_grid):
    """Enables grid buttons that are not in an ACTION_TAKEN state."""
    print("Enabling active grid buttons.")
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            button = button_grid[r][c]
            state = card_state_grid[r][c]
            if button and isinstance(button, tk.Button) and button.winfo_exists():
                # Only enable if the card hasn't had its final action taken
                if state != config.STATE_ACTION_TAKEN:
                    button.config(state=tk.NORMAL)
                else:
                    # Ensure buttons for completed actions remain disabled
                    button.config(state=tk.DISABLED)

def clear_combat_view(info_frame):
    """Destroys any combat-related widgets in the info frame."""
    global current_combat_view
    print("Clearing combat view from info panel.")
    if current_combat_view and current_combat_view.winfo_exists():
        current_combat_view.destroy()
    current_combat_view = None
    # Alternative: Iterate through info_frame children if structure is simple
    # for widget in info_frame.winfo_children():
    #     # Be careful not to destroy permanent labels, separators etc.
    #     # Maybe tag combat widgets specifically? Or destroy only frames?
    #     if isinstance(widget, tk.Frame) and widget != hand_frame: # Example logic
    #          widget.destroy()


# --- Main Application Setup ---
def main():
    global current_combat_view # Allow modification by callbacks

    # 1. Create Main Window
    root = ui_manager.create_main_window()

    # 2. Load PIL Assets (includes dice now)
    pil_assets = assets_manager.load_pil_assets()
    if "width" not in pil_assets or "height" not in pil_assets:
         exit("FATAL ERROR: Card dimensions not loaded from assets.")
    scaled_width = pil_assets["width"]
    scaled_height = pil_assets["height"]

    # 3. Create Tkinter Images (includes dice now)
    tk_assets = create_tk_images(root, pil_assets)

    # 4. Combine Assets
    assets = {**pil_assets, **tk_assets}
    if "tk_photo_back" not in assets: exit("FATAL ERROR: Tkinter card back image missing.")
    tk_photo_back = assets["tk_photo_back"]

    # 5. Setup Layout
    grid_frame, info_frame = ui_manager.setup_layout(root, scaled_width, scaled_height)
    info_frame_bg = info_frame.cget('bg') # Get background for consistency

    # 6. Setup Info Panel (permanent elements)
    player_id_text = f"Playing as Jack of {config.PLAYER_SUIT.title()}"
    info_text_var = ui_manager.setup_info_panel_content(info_frame, player_id_text)
    # --- Store permanent info elements to avoid destroying them ---
    # (Assumes setup_info_panel_content returns them or they are packed first)
    # Example: title_label, separator, info_content_label = ui_manager.setup_info_panel_content(...)
    # --------------------------------------------------------------

    # 7. Setup Hand Display Frame (initially visible)
    hand_frame, hand_card_slots = ui_manager.setup_hand_display(info_frame, scaled_width, scaled_height)

    # 8. Initialize Game State Components
    card_data_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    button_grid = [[None for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    card_state_grid = [[config.STATE_FACE_DOWN for _ in range(config.COLUMNS)] for _ in range(config.ROWS)]
    hand_card_data = [[None for _ in range(config.HAND_COLS)] for _ in range(config.HAND_ROWS)]

    # Create the Player
    player_start_row, player_start_col = config.ROWS // 2, config.COLUMNS // 2 # Start middle? TBD by rules
    player = Player(player_start_row, player_start_col)
    player.suit = config.PLAYER_SUIT # Assign suit based on config
    # Update player info display
    info_text_var.set(f"{player_id_text}\nPosition: {player.position}\nTurn: 1 | Actions: 2") # Example update

    # 9. Prepare Deck (adjust according to rules PDF snapshot)
    print("Preparing deck for the Dungeon...")
    full_deck = create_shuffled_deck() # Standard 52 cards
    # --- Rulebook Setup ---
    # 1. Separate Jacks, one Joker, one Black 10. Shuffle rest.
    jacks = [card for card in full_deck if card.get_rank() == 11]
    other_cards = [card for card in full_deck if card.get_rank() != 11]

    # Define the specific black 10 (e.g., 10 of Clubs)
    black_10_card = Card(suit="clubs", rank=10, rank_string="ten") # Assuming Clubs is black
    black_joker_card = Card(config.BLACK_JOKER_SUIT, config.BLACK_JOKER_RANK, config.BLACK_JOKER_RANK_STR)
    red_joker_card = Card(config.RED_JOKER_SUIT, config.RED_JOKER_RANK, config.RED_JOKER_RANK_STR)

    # Remove the specific black 10 and one Joker (assume black joker for now) from 'other_cards'
    cards_for_shuffle = []
    black_10_removed = False
    black_joker_removed = False
    for card in other_cards:
         is_black_10 = card.get_suit() in ["clubs", "spades"] and card.get_rank() == 10
         # Use a more robust Joker check if suits/ranks vary
         is_black_joker = card.get_suit() == config.BLACK_JOKER_SUIT and card.get_rank() == config.BLACK_JOKER_RANK

         if is_black_10 and not black_10_removed:
              print(f"- Separated Black 10: {card}")
              black_10_separated = card # Keep ref if needed by rules later
              black_10_removed = True
         elif is_black_joker and not black_joker_removed:
              print(f"- Separated Black Joker: {card}")
              black_joker_separated = card
              black_joker_removed = True
         else:
              cards_for_shuffle.append(card)

    # Check if separation was successful (depends on Joker representation in deck)
    if not black_10_removed: print("Warning: Black 10 specified in rules was not found in the initial deck.")
    if not black_joker_removed: print("Warning: Black Joker specified in rules was not found in the initial deck.")


    # Shuffle the remaining cards
    random.shuffle(cards_for_shuffle)
    print(f"- Shuffled {len(cards_for_shuffle)} cards for the grid.")

    deck_for_grid = cards_for_shuffle # Use the shuffled cards

    # Rule 2 & 3: Place Red Joker face-up, Black 10 face-up on top. Arrange rest face down.
    # *Code currently places Red Joker middle face DOWN, adds Black Joker to shuffle pool.*
    # *Let's stick to the code's current logic for now as per user request (Red middle, Black shuffled)*
    # Add Black Joker back to the pool to be shuffled in
    deck_for_grid.append(black_joker_card)
    random.shuffle(deck_for_grid) # Shuffle again with black joker
    print(f"- Added Black Joker and re-shuffled grid deck ({len(deck_for_grid)} cards).")
    print(f"- Red Joker ({red_joker_card}) kept separate for center placement.")

    # Verify deck size
    expected_grid_deck_size = (config.ROWS * config.COLUMNS) - 1 # Grid size minus center
    if len(deck_for_grid) != expected_grid_deck_size:
        print(f"FATAL ERROR: Deck size for grid ({len(deck_for_grid)}) doesn't match expected ({expected_grid_deck_size}). Check setup logic.")
        print(f"Deck Content: {deck_for_grid}") # Debugging
        # sys.exit(1) # Or just print warning for testing

    # 10. Deal Cards
    print(f"Dealing cards onto the {config.ROWS}x{config.COLUMNS} grid...")
    center_r, center_c = config.ROWS // 2, config.COLUMNS // 2
    card_index = 0
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            if r == center_r and c == center_c:
                # Place Red Joker in the center, face down (as per current code)
                card_data_grid[r][c] = red_joker_card
                card_state_grid[r][c] = config.STATE_FACE_DOWN
            else:
                # Deal from the shuffled deck
                if card_index < len(deck_for_grid):
                    card_data_grid[r][c] = deck_for_grid[card_index]
                    card_state_grid[r][c] = config.STATE_FACE_DOWN
                    card_index += 1
                else:
                    # Should not happen if deck size is correct
                    print(f"Warning: Ran out of cards for grid at ({r},{c}). Leaving empty.")
                    card_state_grid[r][c] = config.STATE_ACTION_TAKEN # Mark as empty/done

    total_dealt = card_index + 1 # +1 for the center card
    expected_total = config.ROWS * config.COLUMNS
    print(f"- Placed {total_dealt} cards.")
    if total_dealt != expected_total:
        print(f"- Warning: Expected {expected_total} cards on grid.")

    # 11. Create Grid Buttons
    print("Creating button grid...")
    button_bg = grid_frame.cget('bg')
    buttons_created = 0
    for r in range(config.ROWS):
        for c in range(config.COLUMNS):
            card = card_data_grid[r][c]
            current_state = card_state_grid[r][c]

            if card is not None and current_state == config.STATE_FACE_DOWN:
                # --- Pass necessary UI frames and grids to click handler ---
                click_command = lambda row=r, col=c: game_logic.handle_card_click(
                    row, col,
                    root, player,
                    card_data_grid, button_grid, card_state_grid,
                    hand_card_data, hand_card_slots,
                    assets, # Pass the full assets dict
                    info_frame, # Pass the frame where combat will appear
                    hand_frame, # Pass the frame to hide/show
                    info_frame_bg # Pass bg color for consistency
                )
                # ---------------------------------------------------------
                button = tk.Button(grid_frame, image=tk_photo_back, command=click_command,
                                   borderwidth=0, highlightthickness=0, relief=tk.FLAT,
                                   bg=button_bg, activebackground=button_bg, state=tk.NORMAL)
                button.image = tk_photo_back # Keep reference
                button.grid(row=r, column=c, padx=1, pady=1)
                button_grid[r][c] = button
                buttons_created += 1
            else:
                # Create placeholder for empty/non-clickable slots (like center initially if face up)
                placeholder = tk.Frame(grid_frame, width=scaled_width, height=scaled_height, bg=grid_frame.cget('bg'))
                placeholder.grid(row=r, column=c, padx=1, pady=1)
                button_grid[r][c] = None # No button for this slot

    print(f"- Created {buttons_created} buttons.")

    # 12. Start Main Loop
    print("Starting Tkinter main loop...")
    root.mainloop()
    print("Window closed.")

# --- Run ---
if __name__ == "__main__":
    main()

# --- END OF FILE main.py ---