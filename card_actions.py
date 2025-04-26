# --- START OF FILE card_actions.py ---

import tkinter as tk
import config
import hand_manager # Import hand management functions
from card_logic import Card # Keep Card import
import combat_manager # Import the refactored combat module

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
        if 0 <= row < config.ROWS and 0 <= col < config.COLUMNS:
            if card_state_grid[row][col] != config.STATE_ACTION_TAKEN: card_state_grid[row][col] = config.STATE_ACTION_TAKEN
        if button and button.winfo_exists(): button.config(state=tk.DISABLED)
        return
    if not button or not button.winfo_exists():
        print(f"Error in handle_card_action: Button missing or destroyed at ({row},{col}).")
        if 0 <= row < config.ROWS and 0 <= col < config.COLUMNS:
            if card_state_grid[row][col] != config.STATE_ACTION_TAKEN: card_state_grid[row][col] = config.STATE_ACTION_TAKEN
        return

    # --- State Change Logic ---
    # For most actions (pickup, joker, ace use), disable button immediately.
    # For combat, disable button TEMPORARILY, combat_manager will re-enable if cancelled/lost.
    print(f"--- Action triggered for card {card} at ({row}, {col}) ---") # Keep this log

    card_suit = card.get_suit().lower()
    card_rank = card.rank
    card_color = card.get_color()
    tk_card_face_images = assets.get("tk_faces", {}) # Safely get Tk faces dict

    # --- Prepare game_state dictionary for combat_manager ---
    # This bundles the necessary state components for easy passing
    # Pass PIL images for dice rendering in combat UI windows
    game_state_for_combat = {
        "card_data_grid": card_data_grid,
        "button_grid": button_grid,
        "card_state_grid": card_state_grid,
        "hand_card_data": hand_card_data,
        "hand_card_slots": hand_card_slots,
        "assets": assets # Pass the whole assets dict (includes tk_faces and pil_dice_scaled)
        # info_frame_bg might be needed later if combat updates it? Unlikely for now.
    }

    # --- Determine Action Logic ---

    # Jokers (Add to hand)
    if card_color == "joker":
        print(f"Action: Found Joker ({card})! Attempting to add to hand.")
        card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark taken before potential removal
        if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
            button.grid_forget()
            button_grid[row][col] = None
            card_data_grid[row][col] = None # Clear data grid slot as well
            print(f"   - Successfully moved {card} to hand.")
        else:
            print(f"   - Could not add {card} to hand (Hand full?).")
            button.config(state=tk.DISABLED) # Disable if not picked up

    # Black Number Cards (Hazards) -> Initiate Combat
    elif card_color == "black" and card_rank is not None and 2 <= card_rank <= 10:
        print(f"Action: Initiate Combat vs Hazard ({card})")
        # Temporarily disable button; combat manager handles final state
        button.config(state=tk.DISABLED)
        # Mark state as busy/action-pending; combat manager handles final state
        card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Or a new STATE_IN_COMBAT? For now, ACTION_TAKEN works.
        combat_manager.initiate_combat(root, player, card, row, col, game_state_for_combat)
        # Combat manager handles further state/button changes based on outcome/cancellation

    # Red Number Cards (Equipment) -> Add to Hand
    elif card_color == "red" and card_rank is not None and 2 <= card_rank <= 10:
        print(f"Action: Attempting Pickup Equipment ({card})")
        card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark taken before potential removal
        if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
            button.grid_forget()
            button_grid[row][col] = None
            card_data_grid[row][col] = None # Clear data grid slot as well
            print(f"   - Successfully moved {card} to hand.")
        else:
            print(f"   - Could not add {card} to hand (Hand full?).")
            button.config(state=tk.DISABLED) # Disable if not picked up

    # Face Cards (J, Q, K) AND Aces
    elif card_rank is not None and (card_rank == 1 or 11 <= card_rank <= 13):
        # Player's suit check (using player object now)
        is_player_suit = (card_suit == player.suit) if hasattr(player, 'suit') else False
        card_type = "Ace" if card_rank == 1 else ("Jack" if card_rank == 11 else ("Queen" if card_rank == 12 else "King"))

        print(f"Action: Encounter {card_type} ({card})")

        if card_rank == 1: # Aces (Reveal adjacent)
             print("   - Action: Use Ace ability (Reveal adjacent) - (Not Implemented Yet)")
             # TODO: Implement reveal adjacent logic
             # For now, just disable the card
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN
             button.config(state=tk.DISABLED)

        elif card_rank == 11: # Jacks (Should not be on grid per setup rules)
             print(f"   - Warning: Encountered Jack ({card}) on grid, this shouldn't happen per rules.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN
             button.config(state=tk.DISABLED) # Treat as error/disable

        elif card_rank in [12, 13]: # Queens and Kings (NPCs)
            if is_player_suit: # Friendly NPC -> Add to Hand
                print(f"   - Friendly NPC ({card_type}). Action: Add to hand.")
                card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark taken
                if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
                     button.grid_forget()
                     button_grid[row][col] = None
                     card_data_grid[row][col] = None # Clear data grid slot
                     print(f"     - Successfully moved {card} to hand.")
                else:
                     print(f"     - Could not add {card} to hand (Hand full?).")
                     button.config(state=tk.DISABLED) # Disable if not picked up
            else: # Hostile NPC -> Initiate Combat
                print(f"   - Hostile NPC ({card_type}). Action: Initiate Combat.")
                button.config(state=tk.DISABLED) # Temp disable
                card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as busy
                combat_manager.initiate_combat(root, player, card, row, col, game_state_for_combat)
                # Combat manager handles further state/button changes

    # Unknown Card Type
    else:
        print(f"Action: Unknown card type - {card} (Rank: {card_rank}, Color: {card_color})")
        card_state_grid[row][col] = config.STATE_ACTION_TAKEN
        button.config(state=tk.DISABLED)

    print("--- Action Handling Complete ---")


# --- END OF FILE card_actions.py ---