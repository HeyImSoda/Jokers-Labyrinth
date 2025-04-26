# --- START OF FILE combat/manager.py ---

import tkinter as tk # For widget state checks
import config # For state constants
# Use relative imports for sibling modules within the 'combat' package
from . import setup as combat_setup
from . import logic as combat_logic
from . import effects as combat_effects
from .ui_setup import CombatSetupWindow
from .ui_roll import CombatRollWindow
from .ui_results import CombatResultsWindow

# Import hand_manager from the parent directory
# This approach is generally okay for simpler projects, but can become fragile.
# Consider passing hand_manager functions/object if structure gets more complex.
import sys
import os
# Add parent directory to path to import hand_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
try:
    import hand_manager
except ImportError:
    print("FATAL ERROR: Could not import hand_manager. Check project structure and sys.path.")
    sys.exit(1) # Exit if critical module is missing

# --- Main Entry Point ---
def initiate_combat(root, player, target_card, target_row, target_col, game_state):
    """Starts the combat setup phase by opening the CombatSetupWindow."""
    print(f"\n=== Initiating Combat vs {target_card} at ({target_row}, {target_col}) ===")

    # Find valid cards player *could* use (from combat.setup)
    value_cards = combat_setup.get_value_cards_from_hand(game_state["hand_card_data"], player.suit)
    print(f"  Player hand value cards available: {[vc[0] for vc in value_cards]}")

    # Define callback for when CombatSetupWindow closes
    def combat_setup_callback(selected_value_card_info):
        # selected_value_card_info is either False (cancelled) or (Card, r, c) or None (no card used)
        if selected_value_card_info is False:
            print("  Combat cancelled by player during setup.")
            # Reset the grid card state and button state
            button = game_state["button_grid"][target_row][target_col]
            if button and button.winfo_exists():
                button.config(state=tk.NORMAL)
            # Reset state to FACE_UP so it can be clicked again
            game_state["card_state_grid"][target_row][target_col] = config.STATE_FACE_UP
            print(f"  Card state at ({target_row},{target_col}) reset to FACE_UP.")
            return

        # Player confirmed selection (or confirmed using no card)
        print(f"  Player selected combat card: {selected_value_card_info[0] if selected_value_card_info else 'None'}")
        prepare_combat_resolution(root, player, target_card, target_row, target_col, selected_value_card_info, game_state)

    # Open the setup window (from combat.ui_setup)
    CombatSetupWindow(root, target_card, value_cards, combat_setup_callback)


# --- Orchestration Logic ---
def prepare_combat_resolution(root, player, target_card, target_row, target_col, selected_value_card_info, game_state):
    """Calculates parameters, checks for auto-win, opens Roll Window or finalizes."""
    print("\n--- Preparing Combat Resolution ---")
    used_card = selected_value_card_info[0] if selected_value_card_info else None

    # Calculate parameters using combat.logic module
    combat_params = combat_logic.calculate_combat_parameters(used_card, target_card)
    attacker_total = combat_params["attacker_total"]
    defender_total = combat_params["defender_total"]
    difference = combat_params["difference"] # Absolute difference
    num_diff_dice = combat_params["num_diff_dice"]

    print(f"  Attacker Value: {attacker_total} (Card: {used_card})")
    print(f"  Defender Value: {defender_total} (Card: {target_card})")
    print(f"  Difference: {difference}")

    # Check for Automatic Win (Attacker Value > Defender Value)
    # Note: Rules PDF implies you only roll if Attacker <= Defender.
    if attacker_total > defender_total:
        print("  Result: AUTOMATIC WIN! (Attacker value > Defender value)")
        results_data = {
            "win": True, "automatic_win": True, # Flag for automatic win
            "target": target_card, "defender_total": defender_total,
            "used_card": used_card, "attacker_total": attacker_total,
            "difference": difference, # Store difference even for auto-win
            "num_diff_dice": 0, "diff_dice_rolls": [], "danger_die": None, # No dice rolled
            "consequences": []
        }
        # Apply win effects (from combat.effects) - pass hand_manager module
        combat_effects.handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager)
        # Show results window (from combat.ui_results)
        pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
        CombatResultsWindow(root, results_data, pil_dice_images)
        print("=== Combat Finished (Automatic Win) ===")
        return # Combat finished

    # --- Proceed with Dice Rolling (Attacker <= Defender) ---
    print(f"  Requires Dice Roll: {num_diff_dice} difference dice vs 1 danger die.")

    def finalize_combat_callback(roll_results):
        """Receives dice results from CombatRollWindow and finalizes."""
        # roll_results = {"diff_rolls": [...], "danger_roll": int} or None
        if roll_results is None:
            print("  Error: CombatRollWindow closed prematurely or failed. Resetting combat state.")
            # Reset state/button as if combat was cancelled before rolling
            button = game_state["button_grid"][target_row][target_col]
            if button and button.winfo_exists(): button.config(state=tk.NORMAL)
            game_state["card_state_grid"][target_row][target_col] = config.STATE_FACE_UP
            print(f"  Card state at ({target_row},{target_col}) reset to FACE_UP.")
            return

        diff_dice_rolls = roll_results["diff_rolls"]
        danger_die_roll = roll_results["danger_roll"]
        # Call the finalization logic (defined below in this manager file)
        finalize_combat(
            root, player, target_card, target_row, target_col,
            selected_value_card_info, game_state,
            combat_params, # Pass the whole dict
            diff_dice_rolls, danger_die_roll # Pass the received rolls
        )

    # Open the roll window (from combat.ui_roll)
    CombatRollWindow(root, player, target_card, target_row, target_col,
                     selected_value_card_info, game_state, combat_params,
                     finalize_combat_callback) # Pass the callback


def finalize_combat(root, player, target_card, target_row, target_col,
                    selected_value_card_info, game_state,
                    combat_params, # Receive params dict
                    diff_dice_rolls, danger_die_roll): # Takes dice rolls as args
    """Determines outcome based on rolls and calls effect handlers."""
    print("\n--- Finalizing Combat After Dice Rolls ---")
    print(f"  Attacker Value: {combat_params['attacker_total']}")
    print(f"  Defender Value: {combat_params['defender_total']}")
    print(f"  Difference Dice ({combat_params['num_diff_dice']}): {diff_dice_rolls}")
    print(f"  Danger Die Roll: {danger_die_roll}")

    num_diff_dice = combat_params["num_diff_dice"]

    # Check win condition using combat.logic module
    combat_won = combat_logic.check_combat_win_condition(diff_dice_rolls, danger_die_roll, num_diff_dice)

    used_card = selected_value_card_info[0] if selected_value_card_info else None
    results_data = {
        "win": combat_won, "automatic_win": False, # Not an automatic win
        "target": target_card, "defender_total": combat_params["defender_total"],
        "used_card": used_card, "attacker_total": combat_params["attacker_total"],
        "difference": combat_params["difference"],
        "num_diff_dice": num_diff_dice,
        "diff_dice_rolls": diff_dice_rolls,
        "danger_die": danger_die_roll,
        "consequences": [] # Effects handlers will populate this
    }

    # Call appropriate effect handler (from combat.effects) based on win/loss outcome
    if combat_won:
        print("  Outcome: WIN!")
        combat_effects.handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager)
    else:
        print("  Outcome: LOSE!")
        combat_effects.handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager)

    # Show the results window (from combat.ui_results)
    pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
    CombatResultsWindow(root, results_data, pil_dice_images)
    print("=== Combat Finished (Dice Roll) ===")

# --- END OF FILE combat/manager.py ---