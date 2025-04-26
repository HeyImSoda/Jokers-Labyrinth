# --- START OF FILE card_actions.py ---

import tkinter as tk
import config
import hand_manager # Import hand management functions
from card_logic import Card # Keep Card import if needed for type checking or comparisons

def handle_card_action(
    row, col,
    card_data_grid, button_grid, card_state_grid, # Grids
    hand_card_data, hand_card_slots, # Hand components
    assets, info_frame_bg # UI/Asset components
    # Add 'player' argument if actions depend on player state/suit later
    ):
    """
    Determines and executes the action for a revealed card (pickup, battle, etc.).
    This function is called AFTER a card has been revealed and clicked again.

    Args:
        row, col: Coordinates of the clicked card.
        card_data_grid: 2D list holding Card objects or None.
        button_grid: 2D list holding Tkinter Button widgets or None.
        card_state_grid: 2D list holding card state constants.
        hand_card_data: 2D list tracking cards in the hand display.
        hand_card_slots: 2D list of Tkinter Labels used for hand display.
        assets: Dictionary containing all loaded image assets (PIL and Tk).
        info_frame_bg: Background color of the info frame (for hand card display).
    """
    # Access required data using arguments
    button = button_grid[row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS and button_grid[row][col]) else None
    card = card_data_grid[row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS) else None

    # Validate card/button state before proceeding
    if not card:
        print(f"Error in handle_card_action: No card data at ({row},{col}).")
        if 0 <= row < config.ROWS and 0 <= col < config.COLUMNS:
            if card_state_grid[row][col] != config.STATE_ACTION_TAKEN: card_state_grid[row][col] = config.STATE_ACTION_TAKEN
        if button and button.winfo_exists(): button.config(state=tk.DISABLED)
        return
    if not button or not button.winfo_exists():
        print(f"Error in handle_card_action: Button missing or destroyed at ({row},{col}).")
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
    tk_card_face_images = assets.get("tk_faces", {}) # Safely get Tk faces dict

    # --- Determine Action Logic ---
    # Jokers
    if card_color == "joker":
        print("Action: Joker! (Special effect TBD)")
        action_taken_or_processed = True

    # Number Cards (2-10 Only)
    elif card_rank is not None and 2 <= card_rank <= 10:
        if card_color == "red":
            print(f"Action: Attempting Pickup Red Number ({card})")
            # Call hand manager function, passing necessary arguments
            if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
                button.grid_forget() # Remove button visually
                button_grid[row][col] = None # Clear reference in main grid
                card_data_grid[row][col] = None # Clear card data from grid (handled card)
                action_taken_or_processed = True
                print(f"   - Successfully moved {card} to hand.")
            else:
                print(f"   - Could not add {card} to hand (Hand full?).")
                action_taken_or_processed = True # Still counts as processed
        elif card_color == "black":
            print(f"Action: Battle Black Number ({card})")
            # Future: Implement battle logic
            action_taken_or_processed = True
        else:
             print(f"Warning: Unknown color '{card_color}' for number card {card}")
             action_taken_or_processed = True

    # Face Cards (J, Q, K) AND Aces (Rank 1)
    elif card_rank is not None and (card_rank == 1 or 11 <= card_rank <= 13):
        is_player_suit = (card_suit == config.PLAYER_SUIT) # Check against player's designated suit
        card_type = "Ace" if card_rank == 1 else "Face Card"
        print(f"Action: {card_type} ({card})")
        if is_player_suit:
            print(f"   - Option: Pickup ({card_type} - Player Suit)") # Placeholder
            print(f"   - Option: Battle ({card_type} - Player Suit)") # Placeholder
            # Future: Implement choice mechanism (e.g., context menu, buttons)
            # For now, default to battle or just log options
        else:
            print(f"   - Action: Battle ({card_type} - Other Suit)") # Placeholder
            # Future: Implement battle logic
        action_taken_or_processed = True

    # Unknown Card Type
    else:
        print(f"Action: Unknown card type - {card} (Rank: {card_rank}, Color: {card_color})")
        action_taken_or_processed = True

    # Final check: Ensure button is disabled if it wasn't removed
    # Re-check reference in case it was set to None above
    current_button = button_grid[row][col]
    if current_button and current_button.winfo_exists():
        current_button.config(state=tk.DISABLED)

    print("-------------------------------------------------")

# --- END OF FILE card_actions.py ---