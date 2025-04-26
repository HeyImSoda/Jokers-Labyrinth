# --- START OF FILE card_actions.py ---

import tkinter as tk
import config
import hand_manager # Import hand management functions
from card_logic import Card # Keep Card import
import combat_manager # Import the new combat module

def handle_card_action(
    row, col,
    root, player, # Pass root and player now!
    card_data_grid, button_grid, card_state_grid, # Grids
    hand_card_data, hand_card_slots, # Hand components
    assets, info_frame_bg # UI/Asset components
    ):
    """
    Determines and executes the action for a revealed card.
    Initiates combat via combat_manager if appropriate.
    """
    # Access required data using arguments
    button = button_grid[row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS and button_grid[row][col]) else None
    card = card_data_grid[row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS) else None

    # Validate card/button state before proceeding
    if not card:
        print(f"Error in handle_card_action: No card data at ({row},{col}).")
        # (Error handling remains the same)
        if 0 <= row < config.ROWS and 0 <= col < config.COLUMNS:
            if card_state_grid[row][col] != config.STATE_ACTION_TAKEN: card_state_grid[row][col] = config.STATE_ACTION_TAKEN
        if button and button.winfo_exists(): button.config(state=tk.DISABLED)
        return
    if not button or not button.winfo_exists():
        print(f"Error in handle_card_action: Button missing or destroyed at ({row},{col}).")
        # (Error handling remains the same)
        if 0 <= row < config.ROWS and 0 <= col < config.COLUMNS:
            if card_state_grid[row][col] != config.STATE_ACTION_TAKEN: card_state_grid[row][col] = config.STATE_ACTION_TAKEN
        return

    # --- State Change Moved ---
    # Don't set state to ACTION_TAKEN immediately if combat might be initiated,
    # as combat needs the button enabled initially and might be cancelled.
    # Combat initiation / other actions will handle state changes.
    # print(f"--- Action triggered for card {card} at ({row}, {col}) ---") # Keep this log

    card_suit = card.get_suit().lower()
    card_rank = card.rank
    card_color = card.get_color()
    tk_card_face_images = assets.get("tk_faces", {}) # Safely get Tk faces dict

    # --- Prepare game_state dictionary for combat_manager ---
    # This bundles the necessary state components for easy passing
    game_state_for_combat = {
        "card_data_grid": card_data_grid,
        "button_grid": button_grid,
        "card_state_grid": card_state_grid,
        "hand_card_data": hand_card_data,
        "hand_card_slots": hand_card_slots,
        "assets": assets
        # info_frame_bg might be needed later if combat updates it
    }

    # --- Determine Action Logic ---

    # Jokers
    if card_color == "joker":
        print("Action: Joker! (Special effect TBD)")
        card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Set state
        button.config(state=tk.DISABLED) # Disable after action

    # --- MODIFIED: Black Number Cards (Hazards) ---
    elif card_color == "black" and card_rank is not None and 2 <= card_rank <= 10:
        print(f"Action: Initiate Combat vs Hazard ({card})")
        card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as 'busy' during combat setup
        button.config(state=tk.DISABLED) # Disable button during combat setup
        combat_manager.initiate_combat(root, player, card, row, col, game_state_for_combat)
        # Combat manager handles further state/button changes based on outcome/cancellation

    # Red Number Cards (Equipment)
    elif card_color == "red" and card_rank is not None and 2 <= card_rank <= 10:
        print(f"Action: Attempting Pickup Equipment ({card})")
        card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Set state
        if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
            button.grid_forget()
            button_grid[row][col] = None
            card_data_grid[row][col] = None
            print(f"   - Successfully moved {card} to hand.")
        else:
            print(f"   - Could not add {card} to hand (Hand full?).")
            button.config(state=tk.DISABLED) # Disable if not picked up

    # Face Cards (J, Q, K) AND Aces
    elif card_rank is not None and (card_rank == 1 or 11 <= card_rank <= 13):
        is_player_suit = (card_suit == player.suit) if hasattr(player, 'suit') else (card_suit == config.PLAYER_SUIT) # Use player.suit if defined, else config
        card_type = "Ace" if card_rank == 1 else ("Queen" if card_rank == 12 else "King") # More specific type

        print(f"Action: Encounter {card_type} ({card})")

        if card_rank == 1: # Aces
             print("   - Action: Use Ace ability (Reveal adjacent?) (Not Implemented Yet)")
             # Future: Implement Ace ability (e.g., reveal adjacent cards)
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN
             button.config(state=tk.DISABLED)

        elif card_rank in [12, 13]: # Queens and Kings (NPCs)
            if is_player_suit:
                print(f"   - Friendly NPC ({card_type}). Action: Add to hand.")
                card_state_grid[row][col] = config.STATE_ACTION_TAKEN
                if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
                     button.grid_forget()
                     button_grid[row][col] = None
                     card_data_grid[row][col] = None
                     print(f"     - Successfully moved {card} to hand.")
                else:
                     print(f"     - Could not add {card} to hand (Hand full?).")
                     button.config(state=tk.DISABLED)
            else: # Hostile NPC
                print(f"   - Hostile NPC ({card_type}). Action: Initiate Combat.")
                card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as 'busy'
                button.config(state=tk.DISABLED) # Disable during combat setup
                combat_manager.initiate_combat(root, player, card, row, col, game_state_for_combat)
                # Combat manager handles further state/button changes

    # Unknown Card Type
    else:
        print(f"Action: Unknown card type - {card} (Rank: {card_rank}, Color: {card_color})")
        card_state_grid[row][col] = config.STATE_ACTION_TAKEN
        button.config(state=tk.DISABLED)


    # --- Final Check Removed ---
    # Button state is now handled within each action branch or by combat manager.
    # print("-------------------------------------------------") # Keep log separator

# --- END OF FILE card_actions.py ---