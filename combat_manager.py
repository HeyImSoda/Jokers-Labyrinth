# --- START OF FILE combat_manager.py ---

import tkinter as tk
from tkinter import ttk # Keep ttk if needed for other things maybe?
import config
import utils # For roll_dice
from card_logic import Card
import hand_manager # For hand manipulation

# --- NEW: Import the UI windows from the separate file ---
from combat_ui import CombatSetupWindow, CombatRollWindow, CombatResultsWindow

def get_value_cards_from_hand(hand_card_data, player_suit):
    """Finds valid value cards (Red Numbers OR Friendly Q/K) in the hand."""
    value_cards = []
    for r in range(config.HAND_ROWS):
        for c in range(config.HAND_COLS):
            card = hand_card_data[r][c]
            if not card: continue

            card_color = card.get_color()
            card_rank = card.get_rank()
            card_suit = card.get_suit()

            # Equipment: Red numbers 2-10
            is_equipment = (card_color == "red" and card_rank is not None and 2 <= card_rank <= 10)
            # Friendly Face: Q/K matching player suit
            is_friendly_face = (card_rank in [12, 13] and card_suit == player_suit)

            if is_equipment or is_friendly_face:
                value_cards.append((card, r, c)) # Store card and original hand coords

    return value_cards

def _get_card_combat_value(card):
    """Helper to get the combat value (Q=12, K=13, Num=Value, else 0)."""
    if not card: return 0
    rank = card.get_rank()
    if rank == 12: return 12
    if rank == 13: return 13
    if rank is not None and 2 <= rank <= 10: return rank
    return 0 # Default for Aces, Jokers, etc. (and invalid cards)


def initiate_combat(root, player, target_card, target_row, target_col, game_state):
    """Starts the combat setup phase by opening the CombatSetupWindow."""
    print(f"Initiating combat against {target_card} at ({target_row}, {target_col})")

    # Find valid cards in hand the player *could* use
    value_cards = get_value_cards_from_hand(game_state["hand_card_data"], player.suit)

    # Define the callback function for when CombatSetupWindow closes
    def combat_setup_callback(selected_value_card_info):
        if selected_value_card_info is False:
            # Player cancelled the combat setup
            print("Combat cancelled by player.")
            # Re-enable the grid button and reset state
            button = game_state["button_grid"][target_row][target_col]
            if button and button.winfo_exists():
                button.config(state=tk.NORMAL)
            # Reset state to FACE_UP so it can be clicked again
            game_state["card_state_grid"][target_row][target_col] = config.STATE_FACE_UP
            return

        # Player confirmed, proceed to resolution phase
        prepare_combat_resolution(root, player, target_card, target_row, target_col, selected_value_card_info, game_state)

    # Open the setup window
    CombatSetupWindow(root, target_card, value_cards, combat_setup_callback)


# --- MODIFIED: prepare_combat_resolution ---
def prepare_combat_resolution(root, player, target_card, target_row, target_col, selected_value_card_info, game_state):
    """Calculates combat parameters, checks for automatic win, and opens CombatRollWindow or finalizes."""
    print("Preparing combat resolution...")
    used_card = selected_value_card_info[0] if selected_value_card_info else None

    # Calculate attacker and defender values
    attacker_total = _get_card_combat_value(used_card)
    defender_total = _get_card_combat_value(target_card)

    print(f"  Attacker Value: {attacker_total} (Card: {used_card})")
    print(f"  Defender Value: {defender_total} (Card: {target_card})")

    # --- NEW: Check for Automatic Win ---
    if attacker_total > defender_total:
        print("  Outcome: AUTOMATIC WIN! (Attacker value > Defender value)")
        results_data = {
            "win": True, "automatic_win": True, # Flag for automatic win
            "target": target_card, "defender_total": defender_total,
            "used_card": used_card, "attacker_total": attacker_total,
            "difference": attacker_total - defender_total,
            "num_diff_dice": 0, "diff_dice_rolls": [], "danger_die": None, # No dice rolled
            "consequences": []
        }
        # Directly handle win consequences and show results
        handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data)
        # Show result window (needs PIL dice images from assets)
        pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
        CombatResultsWindow(root, results_data, pil_dice_images)
        return # Combat finished

    # --- Proceed with Dice Rolling (Attacker <= Defender) ---
    difference = abs(attacker_total - defender_total) # Use absolute difference for dice count

    # Determine number of dice based on *absolute* difference (as per rulebook)
    num_diff_dice = 0
    if difference <= 1: num_diff_dice = 2
    elif difference <= 3: num_diff_dice = 3
    elif difference <= 6: num_diff_dice = 4
    elif difference <= 8: num_diff_dice = 5
    else: num_diff_dice = 6 # 9+ difference

    combat_params = {
        "attacker_total": attacker_total, "defender_total": defender_total,
        "difference": difference, "num_diff_dice": num_diff_dice,
    }
    print(f"  Difference={difference}, NumDice={num_diff_dice}. Proceeding to roll.")

    # --- Define callback for when CombatRollWindow finishes ---
    def finalize_combat_callback(roll_results):
        """Receives dice results from CombatRollWindow and finalizes."""
        diff_dice_rolls = roll_results["diff_rolls"]
        danger_die_roll = roll_results["danger_roll"]
        finalize_combat(
            root, player, target_card, target_row, target_col,
            selected_value_card_info, game_state,
            attacker_total, defender_total, difference, num_diff_dice,
            diff_dice_rolls, danger_die_roll # Pass the received rolls
        )

    # --- Open the CombatRollWindow ---
    CombatRollWindow(root, player, target_card, target_row, target_col,
                     selected_value_card_info, game_state, combat_params,
                     finalize_combat_callback) # Pass the callback


# --- MODIFIED: finalize_combat ---
def finalize_combat(root, player, target_card, target_row, target_col,
                    selected_value_card_info, game_state,
                    attacker_total, defender_total, difference, num_diff_dice,
                    diff_dice_rolls, danger_die_roll): # Takes dice rolls as args
    """Determines outcome based on rolls (if any) and calls win/loss handlers."""
    # This function is now only called if dice were actually rolled (attacker <= defender)
    print("Finalizing Combat after dice rolls...")
    print(f"  Difference Rolls: {diff_dice_rolls}")
    print(f"  Danger Die: {danger_die_roll}")

    # Determine win/loss based on danger die vs difference dice
    # Combat is lost if the danger die matches *any* of the difference dice rolled.
    # Handles the case where num_diff_dice might be 0 (though prepare_combat_resolution should handle auto-win first)
    combat_won = True
    if danger_die_roll is None: # Should not happen if dice were rolled, but safety check
        print("  Warning: Danger die was not rolled. Assuming loss.")
        combat_won = False
    elif num_diff_dice > 0 and danger_die_roll in diff_dice_rolls:
        print(f"  Danger die ({danger_die_roll}) matches a difference roll. LOSS!")
        combat_won = False
    else:
        print(f"  Danger die ({danger_die_roll}) does not match difference rolls. WIN!")
        combat_won = True


    used_card = selected_value_card_info[0] if selected_value_card_info else None
    results_data = {
        "win": combat_won, "automatic_win": False, # Not an automatic win
        "target": target_card, "defender_total": defender_total,
        "used_card": used_card, "attacker_total": attacker_total, "difference": difference,
        "num_diff_dice": num_diff_dice, "diff_dice_rolls": diff_dice_rolls,
        "danger_die": danger_die_roll, "consequences": []
    }

    # Call appropriate handler based on win/loss outcome
    if combat_won:
        print("  Outcome: WIN!")
        handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data)
    else:
        print("  Outcome: LOSE!")
        handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data)

    # Show the results window
    pil_dice_images = game_state["assets"].get("pil_dice_scaled", {}) # Get PIL images
    CombatResultsWindow(root, results_data, pil_dice_images) # Pass PIL images


# --- handle_combat_win (logic remains the same, relies on correct state passed in) ---
def handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data):
    """Applies consequences of winning combat."""
    print(f"Handling Combat Win at ({target_row}, {target_col})")
    button_grid = game_state["button_grid"]
    card_data_grid = game_state["card_data_grid"]
    card_state_grid = game_state["card_state_grid"]
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]
    tk_card_face_images = game_state["assets"].get("tk_faces", {}) # For hand redraw

    # 1. Discard used value card (if any)
    if selected_value_card_info:
        used_card, hand_r, hand_c = selected_value_card_info # Get card and original hand slot
        if hand_manager.remove_card_from_hand(used_card, hand_card_data, hand_card_slots, tk_card_face_images):
             results_data["consequences"].append(f"Discarded {used_card} from hand.")
        else:
             results_data["consequences"].append(f"Error removing {used_card} from hand.")
             print(f"Error: Could not find/remove {used_card} from hand data {hand_card_data}")

    # 2. Discard hazard/NPC from grid
    target_card = card_data_grid[target_row][target_col]
    results_data["consequences"].append(f"Discarded {target_card} from the Dungeon.")
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists():
        button.grid_forget() # Remove button visually
    button_grid[target_row][target_col] = None # Clear button ref
    card_data_grid[target_row][target_col] = None # Clear card data ref
    card_state_grid[target_row][target_col] = config.STATE_ACTION_TAKEN # Mark grid slot as done

    # 3. Move player to the now empty space
    old_pos = player.position
    player.set_position(target_row, target_col)
    results_data["consequences"].append(f"Player moved from {old_pos} to ({target_row}, {target_col}).")


# --- handle_combat_loss (logic remains the same, relies on correct state passed in) ---
def handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data):
    """Applies consequences of losing combat."""
    print(f"Handling Combat Loss at ({target_row}, {target_col})")
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]
    button_grid = game_state["button_grid"]
    card_state_grid = game_state["card_state_grid"]
    tk_card_face_images = game_state["assets"].get("tk_faces", {}) # For hand redraw/clear

    # 1. Discard used value card (if any)
    if selected_value_card_info:
        used_card, hand_r, hand_c = selected_value_card_info
        if hand_manager.remove_card_from_hand(used_card, hand_card_data, hand_card_slots, tk_card_face_images):
             results_data["consequences"].append(f"Discarded {used_card} from hand.")
        else:
            results_data["consequences"].append(f"Error removing {used_card} from hand.")
            print(f"Error: Could not find/remove {used_card} from hand data {hand_card_data}")
    else:
        # No card was used, maybe add consequence?
        results_data["consequences"].append("No value card was used in the fight.")


    # 2. Cannot move past Hazard/NPC - Re-enable button, reset state
    results_data["consequences"].append(f"Player cannot move past {results_data['target']}.")
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists():
        button.config(state=tk.NORMAL) # Re-enable button so player can try again (or move away)
    # Reset state to FACE_UP so it can be clicked again for another action/fight
    card_state_grid[target_row][target_col] = config.STATE_FACE_UP

    # 3. Resolve specific NPC loss effects (Queens, Kings)
    target_card = results_data['target']
    target_rank = target_card.get_rank()
    is_hostile_npc = target_rank in [12, 13] # Assumes non-player suit if combat was initiated

    if is_hostile_npc:
        if target_rank == 12: # Lost to hostile Queen
            results_data["consequences"].append("Lost to hostile Queen: Discard all cards from hand!")
            hand_manager.clear_hand_display(hand_card_data, hand_card_slots) # Clear hand visually and data
        elif target_rank == 13: # Lost to hostile King
             results_data["consequences"].append("Lost to hostile King: Skip next turn!")
             if hasattr(player, 'set_skip_turn'):
                 player.set_skip_turn(True)
             else:
                 print("Warning: Player object doesn't have 'set_skip_turn' method.")
    else: # Lost to a Hazard (Black Number Card)
         results_data["consequences"].append("Lost to Hazard. Blocked movement.")


# --- END OF FILE combat_manager.py ---