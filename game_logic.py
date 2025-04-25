# --- START OF FILE game_logic.py ---

import tkinter as tk
import config
import animation # Import animation functions
import hand_manager # Import hand management functions

# --- Global references ---
game_state = {
    "root": None, "assets": None, "card_data_grid": None, "button_grid": None,
    "card_state_grid": None, "hand_card_data": None, "hand_card_slots": None,
    "info_frame_bg": None
}

# --- Callback function after flip animation ---
def on_card_revealed(row, col):
    """Finalizes reveal, sets final image, RE-ENABLES button for second click."""
    # Access shared state (ensure robust checks)
    button = game_state["button_grid"][row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS and game_state["button_grid"][row][col]) else None
    card = game_state["card_data_grid"][row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS) else None
    assets = game_state["assets"]
    card_state_grid = game_state["card_state_grid"]

    if button and card and button.winfo_exists():
        suit_key = str(card.get_suit()).lower()
        rank_key = str(card.get_rank_string()).lower()
        image_key = f"{suit_key}_{rank_key}"
        tk_photo_final = assets["tk_faces"].get(image_key) # Look in the Tk faces dict

        if tk_photo_final:
            button.config(image=tk_photo_final, state=tk.NORMAL) # Set image and re-enable
            button.image = tk_photo_final
            card_state_grid[row][col] = config.STATE_FACE_UP # State: Face Up
        else:
            print(f"Error: Could not find Tk image for key: {image_key} in on_card_revealed")
            # Use Tk back image from assets
            tk_back_image = assets.get("tk_photo_back")
            if tk_back_image:
                 button.config(image=tk_back_image, state=tk.DISABLED) # Fallback, disable
                 button.image = tk_back_image
            else:
                 # Absolute fallback if back image somehow missing
                 button.config(text="Error", state=tk.DISABLED)
            card_state_grid[row][col] = config.STATE_ACTION_TAKEN # State: Disabled (Error)

    elif card and not button:
         # This case means the button was likely removed (e.g. card sent to hand)
         # but the callback still fired. Ensure state is correct.
         if card_state_grid[row][col] != config.STATE_ACTION_TAKEN:
             # print(f"Note: Button missing in on_card_revealed for ({row},{col}), syncing state.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN

# --- Function to Handle Action on Revealed Card ---
def handle_card_action(row, col):
    """Determines and executes action for a revealed card (pickup, battle, etc.)."""
    # Access shared state
    button = game_state["button_grid"][row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS and game_state["button_grid"][row][col]) else None
    card = game_state["card_data_grid"][row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS) else None
    card_state_grid = game_state["card_state_grid"]
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]
    tk_card_face_images = game_state["assets"]["tk_faces"] # Use Tk faces dict
    info_frame_bg = game_state["info_frame_bg"]

    # Validate card/button state before proceeding
    if not card:
         print(f"Error: No card data at ({row},{col}) for action.")
         if 0 <= row < config.ROWS and 0 <= col < config.COLUMNS:
             if card_state_grid[row][col] != config.STATE_ACTION_TAKEN: card_state_grid[row][col] = config.STATE_ACTION_TAKEN
         if button and button.winfo_exists(): button.config(state=tk.DISABLED)
         return
    if not button or not button.winfo_exists():
        print(f"Error: Button missing or destroyed at ({row},{col}) for action.")
        if 0 <= row < config.ROWS and 0 <= col < config.COLUMNS:
            if card_state_grid[row][col] != config.STATE_ACTION_TAKEN: card_state_grid[row][col] = config.STATE_ACTION_TAKEN
        return

    # Set state to Action Taken immediately
    card_state_grid[row][col] = config.STATE_ACTION_TAKEN
    print(f"--- Action triggered for card {card} at ({row}, {col}) ---")

    card_suit = card.get_suit().lower()
    card_rank = card.rank
    card_color = card.get_color()
    action_taken_or_processed = False

    # --- Determine Action Logic ---
    # Jokers
    if card_color == "joker":
        print("Action: Joker! (Special effect TBD)")
        action_taken_or_processed = True

    # --- MODIFICATION: Condition changed to exclude Ace (rank 1) ---
    # Number Cards (2-10 Only)
    elif card_rank is not None and 2 <= card_rank <= 10:
        if card_color == "red":
            print(f"Action: Attempting Pickup Red Number ({card})")
            # Call hand manager function
            if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
                button.grid_forget() # Remove button visually
                game_state["button_grid"][row][col] = None # Clear reference in main grid
                game_state["card_data_grid"][row][col] = None # Clear card data from grid
                action_taken_or_processed = True
                print(f"   - Successfully moved {card} to hand.")
            else:
                print(f"   - Could not add {card} to hand (Hand full?).")
                action_taken_or_processed = True # Still counts as processed
        elif card_color == "black":
            print(f"Action: Battle Black Number ({card})")
            action_taken_or_processed = True
        else:
             print(f"Warning: Unknown color '{card_color}' for number card {card}")
             action_taken_or_processed = True

    # --- MODIFICATION: Condition changed to include Ace (rank 1) ---
    # Face Cards (J, Q, K) AND Aces (Rank 1)
    elif card_rank is not None and (card_rank == 1 or 11 <= card_rank <= 13):
        is_player_suit = (card_suit == config.PLAYER_SUIT)
        # --- MODIFICATION: Adjust print statement for Ace/Face ---
        card_type = "Ace" if card_rank == 1 else "Face Card"
        print(f"Action: {card_type} ({card})")
        if is_player_suit:
            print(f"   - Option: Pickup ({card_type} - Player Suit)") # Placeholder
            print(f"   - Option: Battle ({card_type} - Player Suit)") # Placeholder
            # Future: Implement choice/rules
        else:
            print(f"   - Action: Battle ({card_type} - Other Suit)") # Placeholder
            # Future: Implement battle logic
        action_taken_or_processed = True

    # Unknown Card Type
    else:
        print(f"Action: Unknown card type - {card} (Rank: {card_rank}, Color: {card_color})")
        action_taken_or_processed = True

    # Final check: Ensure button is disabled if it wasn't removed
    current_button = game_state["button_grid"][row][col] # Re-check reference
    if current_button and current_button.winfo_exists():
        current_button.config(state=tk.DISABLED)

    print("-------------------------------------------------")


# --- Main Click Handler ---
def handle_card_click(row, col):
    """Called when a button is clicked, routes to flip or action."""
    # Access shared state
    root = game_state["root"]
    assets = game_state["assets"]
    card_data_grid = game_state["card_data_grid"]
    button_grid = game_state["button_grid"]
    card_state_grid = game_state["card_state_grid"]

    # Bounds check
    if not (0 <= row < config.ROWS and 0 <= col < config.COLUMNS):
         print(f"Error: Click coordinates ({row},{col}) out of bounds.")
         return

    button = button_grid[row][col] # Might be None
    card = card_data_grid[row][col] # Might be None
    # Safely access state grid element
    try:
        current_state = card_state_grid[row][col]
    except IndexError:
        print(f"Error: State grid index out of bounds for ({row},{col})")
        return


    button_exists = button is not None and button.winfo_exists()
    button_state = button['state'] if button_exists else None

    # Ignore clicks on fully processed/removed slots
    if current_state == config.STATE_ACTION_TAKEN:
        return

    # Handle clicks based on state
    if current_state == config.STATE_FACE_DOWN: # Face Down
        if button_exists and button_state == tk.NORMAL:
            print(f"First click on ({row},{col}). Flipping card...")
            button.config(state=tk.DISABLED) # Disable during animation
            animation.animate_flip(root, button, card, assets, on_card_revealed, row, col)
        elif button_exists:
             print(f"Ignoring click on ({row},{col}) - Button not normal (State: {button_state})")
        else:
             print(f"Error: Clicked face-down slot ({row},{col}) but button is missing.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as error/disabled

    elif current_state == config.STATE_FACE_UP: # Face Up / Actionable
        if button_exists and button_state == tk.NORMAL:
            print(f"Second click on ({row},{col}). Performing action...")
            handle_card_action(row, col) # Handles state change and disabling
        elif button_exists:
             print(f"Ignoring click on face-up card ({row},{col}) - Button not normal (State: {button_state})")
        else:
             # Button gone after reveal? Should not happen unless reveal failed badly.
             print(f"Error: Clicked face-up slot ({row},{col}) but button is missing.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as error/disabled

    else: # Should not happen if state checks are correct
        print(f"Warning: Unhandled click state for ({row},{col}) - GridState: {current_state}, Button Exists: {button_exists}, ButtonState: {button_state}")

# --- END OF FILE game_logic.py ---