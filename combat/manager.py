# --- START OF FILE combat/manager.py ---

import tkinter as tk # For widget state checks? Maybe not needed here.
import config # For state constants maybe?
# Use relative imports for sibling modules within the 'combat' package
from . import setup as combat_setup
from . import logic as combat_logic
from . import effects as combat_effects
from .ui_setup import CombatSetupWindow
from .ui_roll import CombatRollWindow
from .ui_results import CombatResultsWindow

# Import hand_manager from the parent directory
import sys
import os
# Add parent directory to path to import hand_manager (adjust if needed)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hand_manager

# --- Main Entry Point ---
def initiate_combat(root, player, target_card, target_row, target_col, game_state):
    """Starts the combat setup phase by opening the CombatSetupWindow."""
    print(f"Initiating combat against {target_card} at ({target_row}, {target_col})")

    value_cards = combat_setup.get_value_cards_from_hand(game_state["hand_card_data"], player.suit)

    def combat_setup_callback(selected_value_card_info):
        if selected_value_card_info is False:
            print("Combat cancelled by player.")
            # Reset state/button if cancelled
            button = game_state["button_grid"][target_row][target_col]
            if button and button.winfo_exists():
                button.config(state=tk.NORMAL)
            game_state["card_state_grid"][target_row][target_col] = config.STATE_FACE_UP
            return

        # Proceed to resolution phase
        prepare_combat_resolution(root, player, target_card, target_row, target_col, selected_value_card_info, game_state)

    # Open the setup window (lives in ui_setup)
    CombatSetupWindow(root, target_card, value_cards, combat_setup_callback)


# --- Orchestration Logic ---
def prepare_combat_resolution(root, player, target_card, target_row, target_col, selected_value_card_info, game_state):
    """Calculates parameters, checks for auto-win, opens Roll Window or finalizes."""
    print("Preparing combat resolution...")
    used_card = selected_value_card_info[0] if selected_value_card_info else None

    # Calculate parameters using logic module
    combat_params = combat_logic.calculate_combat_parameters(used_card, target_card)
    attacker_total = combat_params["attacker_total"]
    defender_total = combat_params["defender_total"]
    difference = combat_params["difference"]
    num_diff_dice = combat_params["num_diff_dice"]

    print(f"  Attacker Value: {attacker_total} (Card: {used_card})")
    print(f"  Defender Value: {defender_total} (Card: {target_card})")

    # Check for Automatic Win (Attacker > Defender)
    if attacker_total > defender_total:
        print("  Outcome: AUTOMATIC WIN! (Attacker value > Defender value)")
        results_data = {
            "win": True, "automatic_win": True,
            "target": target_card, "defender_total": defender_total,
            "used_card": used_card, "attacker_total": attacker_total,
            "difference": difference,
            "num_diff_dice": 0, "diff_dice_rolls": [], "danger_die": None,
            "consequences": []
        }
        # Apply win effects (lives in effects module) - pass hand_manager module itself
        combat_effects.handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager)
        # Show results window (lives in ui_results)
        pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
        CombatResultsWindow(root, results_data, pil_dice_images)
        return # Combat finished

    # --- Proceed with Dice Rolling (Attacker <= Defender) ---
    print(f"  Difference={difference}, NumDice={num_diff_dice}. Proceeding to roll.")

    def finalize_combat_callback(roll_results):
        """Receives dice results from CombatRollWindow and finalizes."""
        if roll_results is None: # Handle potential error/early close from roll window
            print("Error: Received no results from roll window. Aborting finalize.")
            # Reset button/state?
            button = game_state["button_grid"][target_row][target_col]
            if button and button.winfo_exists(): button.config(state=tk.NORMAL)
            game_state["card_state_grid"][target_row][target_col] = config.STATE_FACE_UP
            return

        diff_dice_rolls = roll_results["diff_rolls"]
        danger_die_roll = roll_results["danger_roll"]
        # Call the finalization logic (kept in this manager file for now)
        finalize_combat(
            root, player, target_card, target_row, target_col,
            selected_value_card_info, game_state,
            combat_params, # Pass the whole dict
            diff_dice_rolls, danger_die_roll
        )

    # Open the roll window (lives in ui_roll)
    CombatRollWindow(root, player, target_card, target_row, target_col,
                     selected_value_card_info, game_state, combat_params,
                     finalize_combat_callback)


def finalize_combat(root, player, target_card, target_row, target_col,
                    selected_value_card_info, game_state,
                    combat_params, # Receive params dict
                    diff_dice_rolls, danger_die_roll):
    """Determines outcome based on rolls and calls effect handlers."""
    print("Finalizing Combat after dice rolls...")
    print(f"  Difference Rolls: {diff_dice_rolls}")
    print(f"  Danger Die: {danger_die_roll}")

    num_diff_dice = combat_params["num_diff_dice"]

    # Check win condition using logic module
    combat_won = combat_logic.check_combat_win_condition(diff_dice_rolls, danger_die_roll, num_diff_dice)

    used_card = selected_value_card_info[0] if selected_value_card_info else None
    results_data = {
        "win": combat_won, "automatic_win": False,
        "target": target_card, "defender_total": combat_params["defender_total"],
        "used_card": used_card, "attacker_total": combat_params["attacker_total"],
        "difference": combat_params["difference"],
        "num_diff_dice": num_diff_dice,
        "diff_dice_rolls": diff_dice_rolls,
        "danger_die": danger_die_roll,
        "consequences": []
    }

    # Call appropriate effect handler (lives in effects module)
    if combat_won:
        print("  Outcome: WIN!")
        combat_effects.handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager)
    else:
        print("  Outcome: LOSE!")
        combat_effects.handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager)

    # Show the results window (lives in ui_results)
    pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
    CombatResultsWindow(root, results_data, pil_dice_images)

# --- END OF FILE combat/manager.py ---