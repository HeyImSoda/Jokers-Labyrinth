# --- START OF FILE card_actions.py ---

import tkinter as tk
import config
import hand_manager # Import hand management functions
from card_logic import Card # Keep Card import
# --- MODIFIED IMPORT ---
# Import the main entry point function from the combat package
from combat.manager import initiate_combat
# ---------------------
# Import helpers from main needed for combat UI management
# This is slightly awkward; ideally these helpers would be in a dedicated UI manager module.
try:
    # This assumes main.py is structured to allow these imports,
    # which might not be the case if main() runs directly.
    # A better approach is passing functions or a UI manager object.
    # For now, we rely on them being passed as arguments where needed.
    pass # from main import hide_hand, show_hand, disable_grid, enable_grid, clear_combat_view
except ImportError:
    print("Warning: Could not pre-import UI helpers from main in card_actions.py")


def handle_card_action(
    row, col,
    root, player, # Pass root and player
    card_data_grid, button_grid, card_state_grid, # Grids
    hand_card_data, hand_card_slots, # Hand components
    assets, # Asset components
    info_frame, hand_frame, # UI Frames passed from game_logic
    info_frame_bg # UI Style
    ):
    """
    Determines and executes the action for a revealed card.
    Initiates combat via combat.manager if appropriate, passing UI frames.
    """
    # Access button/card data (no change here)
    button = button_grid[row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS and button_grid[row][col]) else None
    card = card_data_grid[row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS) else None

    # --- Validate ---
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

    print(f"--- Action triggered for card {card} at ({row}, {col}) ---")

    card_suit = card.get_suit().lower()
    card_rank = card.rank
    card_color = card.get_color()
    tk_card_face_images = assets.get("tk_faces", {}) # For hand actions

    # Prepare game state dictionary for combat initiation
    # Note: We pass button_grid and card_state_grid for potential modification *after* combat.
    game_state_for_combat = {
        "card_data_grid": card_data_grid,
        "button_grid": button_grid,
        "card_state_grid": card_state_grid,
        "hand_card_data": hand_card_data,
        "hand_card_slots": hand_card_slots,
        "assets": assets,
        # Pass UI elements needed by combat manager
        "info_frame": info_frame,
        "hand_frame": hand_frame,
        "root": root # Pass root if needed for 'after' calls within combat (e.g. animation delays)
    }

    # --- Determine Action Logic ---

    action_taken = False # Flag to check if an action occurred

    # Jokers (Add to Hand)
    if card_color == "joker":
        print(f"Action: Found Joker ({card})! Attempting to add to hand.")
        if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
            button.grid_forget() # Remove button from grid layout
            button_grid[row][col] = None # Clear button reference
            card_data_grid[row][col] = None # Clear card data reference
            card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark grid slot as done
            print(f"   - Successfully moved {card} to hand. Grid slot cleared.")
            action_taken = True
        else:
            print(f"   - Could not add {card} to hand (Hand full?). Card remains on grid.")
            # Card remains, disable button as action failed/completed for now
            button.config(state=tk.DISABLED)
            card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Or keep FACE_UP? Rule dependent. Assume action done for now.

    # Black Number Cards (Hazards) -> Initiate Combat
    elif card_color == "black" and card_rank is not None and 2 <= card_rank <= 10:
        print(f"Action: Initiate Combat vs Hazard ({card})")
        # Don't disable the button here; combat manager will disable grid
        # card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as busy during combat
        initiate_combat(player, card, row, col, game_state_for_combat)
        action_taken = True # Combat initiation is the action

    # Red Number Cards (Equipment - Add to Hand)
    elif card_color == "red" and card_rank is not None and 2 <= card_rank <= 10:
        print(f"Action: Attempting Pickup Equipment ({card})")
        if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
            button.grid_forget()
            button_grid[row][col] = None
            card_data_grid[row][col] = None
            card_state_grid[row][col] = config.STATE_ACTION_TAKEN
            print(f"   - Successfully moved {card} to hand. Grid slot cleared.")
            action_taken = True
        else:
            print(f"   - Could not add {card} to hand (Hand full?). Card remains on grid.")
            button.config(state=tk.DISABLED)
            card_state_grid[row][col] = config.STATE_ACTION_TAKEN

    # Face Cards (J, Q, K) AND Aces
    elif card_rank is not None and (card_rank == 1 or 11 <= card_rank <= 13):
        is_player_suit = (card_suit == player.suit) if hasattr(player, 'suit') else False
        card_type = "Ace" if card_rank == 1 else ("Jack" if card_rank == 11 else ("Queen" if card_rank == 12 else "King"))
        print(f"Action: Encounter {card_type} ({card})")

        if card_rank == 1: # Aces (Ability - Placeholder)
             print("   - Action: Use Ace ability (Reveal adjacent) - (Not Implemented Yet)")
             # For now, just disable the card as its action is "done"
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN
             button.config(state=tk.DISABLED)
             action_taken = True

        elif card_rank == 11: # Jacks (Shouldn't be on grid based on rules)
             print(f"   - Warning: Encountered Jack ({card}) on grid. Disabling.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN
             button.config(state=tk.DISABLED)
             action_taken = True

        elif card_rank in [12, 13]: # Queens and Kings (NPCs)
            if is_player_suit: # Friendly NPC (Add to Hand)
                print(f"   - Friendly NPC ({card_type}). Action: Add to hand.")
                if hand_manager.add_card_to_hand_display(card, hand_card_data, hand_card_slots, tk_card_face_images, info_frame_bg):
                     button.grid_forget()
                     button_grid[row][col] = None
                     card_data_grid[row][col] = None
                     card_state_grid[row][col] = config.STATE_ACTION_TAKEN
                     print(f"     - Successfully moved {card} to hand. Grid slot cleared.")
                     action_taken = True
                else:
                     print(f"     - Could not add {card} to hand (Hand full?). Card remains.")
                     button.config(state=tk.DISABLED)
                     card_state_grid[row][col] = config.STATE_ACTION_TAKEN
            else: # Hostile NPC -> Initiate Combat
                print(f"   - Hostile NPC ({card_type}). Action: Initiate Combat.")
                # card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark busy
                initiate_combat(player, card, row, col, game_state_for_combat)
                action_taken = True # Combat initiation is the action

    # Unknown Card Type
    else:
        print(f"Action: Unknown card type - {card} (Rank: {card_rank}, Color: {card_color}). Disabling.")
        card_state_grid[row][col] = config.STATE_ACTION_TAKEN
        button.config(state=tk.DISABLED)
        action_taken = True

    # If no specific action resulted in combat or state change, ensure button is disabled
    if not action_taken and button.winfo_exists():
         print(f"Warning: No specific action handler triggered for {card}, but action considered complete. Disabling button.")
         card_state_grid[row][col] = config.STATE_ACTION_TAKEN
         button.config(state=tk.DISABLED)


    print("--- Action Handling Complete ---")

# --- END OF FILE card_actions.py ---