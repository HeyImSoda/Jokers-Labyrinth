# --- START OF FILE combat/manager.py ---

import tkinter as tk # For widget state checks
import config # For state constants
# Use relative imports for sibling modules within the 'combat' package
from . import setup as combat_setup
from . import logic as combat_logic
from . import effects as combat_effects
# --- Rename Window classes to View ---
from .ui_setup import CombatSetupView
from .ui_roll import CombatRollView
from .ui_results import CombatResultsView
# -----------------------------------

# Import hand_manager from the parent directory (keep existing import logic)
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path: sys.path.append(parent_dir)
try: import hand_manager
except ImportError: print("FATAL ERROR: Could not import hand_manager."); sys.exit(1)

# Import UI helpers from main - This is fragile, passing functions is better
# For now, assume they exist in the global scope where combat is initiated (main.py)
# We will call them via the game_state dict passed in.

# --- Global variable within the manager to track the current view instance ---
# This helps in cleaning up the previous view before showing the next one.
current_combat_view_instance = None
# ----------------------------------------------------------------------------

def cleanup_previous_combat_view():
    """Destroys the previous combat view frame if it exists."""
    global current_combat_view_instance
    if current_combat_view_instance:
        print(f"  Cleaning up previous combat view: {type(current_combat_view_instance).__name__}")
        current_combat_view_instance.destroy_view() # Use the new destroy method
        current_combat_view_instance = None

def end_combat_ui(game_state):
    """Cleans up combat UI and restores main game UI state."""
    print("--- Ending Combat UI ---")
    cleanup_previous_combat_view() # Ensure last view is gone

    # Access UI helper functions via game_state (passed from main)
    ui_helpers = game_state.get("ui_helpers", {})
    show_hand_func = ui_helpers.get("show_hand")
    enable_grid_func = ui_helpers.get("enable_grid")

    if show_hand_func and game_state.get("hand_frame"):
        show_hand_func(game_state["hand_frame"])
    else: print("Warning: Could not show hand frame.")

    if enable_grid_func and game_state.get("button_grid") and game_state.get("card_state_grid"):
        enable_grid_func(game_state["button_grid"], game_state["card_state_grid"])
    else: print("Warning: Could not enable grid.")


# --- Main Entry Point ---
def initiate_combat(player, target_card, target_row, target_col, game_state):
    """Starts the combat setup phase by showing the CombatSetupView."""
    global current_combat_view_instance
    print(f"\n=== Initiating Combat UI Sequence vs {target_card} at ({target_row}, {target_col}) ===")

    # Access UI elements and helpers from game_state
    info_frame = game_state.get("info_frame")
    hand_frame = game_state.get("hand_frame")
    button_grid = game_state.get("button_grid")
    card_state_grid = game_state.get("card_state_grid")
    root = game_state.get("root") # Get root for potential 'after' calls

    # --- Prepare UI Helpers ---
    # This assumes main.py defines these and makes them accessible, e.g., via a dict
    # If not passed explicitly, this part needs adjustment. For now, assume they are callable.
    # A cleaner way: pass the functions directly as args or in a dedicated ui_manager object.
    ui_helpers = {
        "hide_hand": game_state.get("hide_hand_func"),
        "show_hand": game_state.get("show_hand_func"),
        "disable_grid": game_state.get("disable_grid_func"),
        "enable_grid": game_state.get("enable_grid_func"),
    }
    game_state["ui_helpers"] = ui_helpers # Add helpers to game_state for easy passing

    # Check if essential UI elements are present
    if not info_frame: print("FATAL ERROR: info_frame missing in game_state for combat."); return
    if not hand_frame: print("Warning: hand_frame missing in game_state for combat."); # Continue cautiously
    if not button_grid: print("Warning: button_grid missing in game_state for combat."); # Continue cautiously

    # --- Setup Combat UI ---
    cleanup_previous_combat_view() # Clear any lingering views first

    if ui_helpers["hide_hand"]: ui_helpers["hide_hand"](hand_frame)
    if ui_helpers["disable_grid"]: ui_helpers["disable_grid"](button_grid)
    # Mark the specific combat card as busy/in-combat state? Optional.
    # card_state_grid[target_row][target_col] = config.STATE_COMBAT # Example state

    # Find valid cards player *could* use (from combat.setup)
    value_cards = combat_setup.get_value_cards_from_hand(game_state["hand_card_data"], player.suit)
    print(f"  Player hand value cards available: {[vc[0] for vc in value_cards]}")

    # --- Define callback for CombatSetupView ---
    def combat_setup_callback(selected_value_card_info):
        # This is called when a button in CombatSetupView is clicked
        global current_combat_view_instance
        print(f"  CombatSetupView Callback: Selection = {selected_value_card_info}")

        if selected_value_card_info is False: # Player cancelled
            print("  Combat cancelled by player during setup.")
            end_combat_ui(game_state) # Restore UI
            # Reset the grid card state back from potential 'BUSY' state if needed
            if card_state_grid: card_state_grid[target_row][target_col] = config.STATE_FACE_UP
            return

        # Player confirmed selection (or confirmed using no card)
        print(f"  Player selected combat card: {selected_value_card_info[0] if selected_value_card_info else 'None'}")
        # Proceed to the next step (resolution/rolling)
        prepare_combat_resolution(player, target_card, target_row, target_col, selected_value_card_info, game_state)

    # --- Create and Display CombatSetupView ---
    print("  Displaying Combat Setup View...")
    current_combat_view_instance = CombatSetupView(info_frame, target_card, value_cards, combat_setup_callback)
    current_combat_view_instance.display()


# --- Orchestration Logic ---
def prepare_combat_resolution(player, target_card, target_row, target_col, selected_value_card_info, game_state):
    """Calculates parameters, checks for auto-win, displays Roll View or Results View."""
    global current_combat_view_instance
    print("\n--- Preparing Combat Resolution ---")
    # We are already in combat UI mode here (hand hidden, grid disabled)
    info_frame = game_state.get("info_frame")
    if not info_frame: print("FATAL ERROR: info_frame missing in prepare_combat_resolution."); return

    cleanup_previous_combat_view() # Clear the setup view

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

    # --- Define callback for CombatResultsView ---
    def results_view_callback():
        # Called when the 'OK' button on the results view is clicked
        print("  CombatResultsView Callback: OK clicked.")
        end_combat_ui(game_state) # Restore main UI

    # --- Check for Automatic Win ---
    if attacker_total > defender_total:
        print("  Result: AUTOMATIC WIN! (Attacker value > Defender value)")
        results_data = { # Prepare data for results view
            "win": True, "automatic_win": True, "target": target_card,
            "defender_total": defender_total, "used_card": used_card,
            "attacker_total": attacker_total, "difference": difference,
            "num_diff_dice": 0, "diff_dice_rolls": [], "danger_die": None,
            "consequences": []
        }
        # Apply win effects (from combat.effects) - populates consequences
        combat_effects.handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager)

        # --- Display Results View ---
        print("  Displaying Combat Results View (Auto-Win)...")
        pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
        current_combat_view_instance = CombatResultsView(info_frame, results_data, pil_dice_images, results_view_callback)
        current_combat_view_instance.display()
        print("=== Combat Sequence Finished (Automatic Win) ===")
        return # Combat sequence finished

    # --- Proceed with Dice Rolling (Attacker <= Defender) ---
    print(f"  Requires Dice Roll: {num_diff_dice} difference dice vs 1 danger die.")

    # --- Define callback for CombatRollView ---
    def finalize_combat_callback(roll_results):
        # Called by CombatRollView after danger die animation finishes
        # roll_results = {"diff_rolls": [...], "danger_roll": int} or None
        global current_combat_view_instance
        print(f"  CombatRollView Callback: Rolls = {roll_results}")

        if roll_results is None:
            print("  Error: CombatRollView closed prematurely or failed. Resetting combat state.")
            # Maybe show an error message?
            end_combat_ui(game_state) # Restore UI
             # Reset the grid card state back from potential 'BUSY' state if needed
            if game_state.get("card_state_grid"): game_state["card_state_grid"][target_row][target_col] = config.STATE_FACE_UP
            return

        diff_dice_rolls = roll_results["diff_rolls"]
        danger_die_roll = roll_results["danger_roll"]
        # Call the finalization logic (calculates win/loss, applies effects)
        finalize_combat(
            player, target_card, target_row, target_col,
            selected_value_card_info, game_state,
            combat_params, # Pass the whole dict
            diff_dice_rolls, danger_die_roll,
            results_view_callback # Pass the *final* callback for the results view
        )

    # --- Create and Display CombatRollView ---
    print("  Displaying Combat Roll View...")
    current_combat_view_instance = CombatRollView(
        info_frame, player, target_card,
        selected_value_card_info, game_state, combat_params,
        finalize_combat_callback # Pass the callback defined above
    )
    current_combat_view_instance.display()


def finalize_combat(player, target_card, target_row, target_col,
                    selected_value_card_info, game_state,
                    combat_params, # Receive params dict
                    diff_dice_rolls, danger_die_roll,
                    results_callback): # Callback for the results view
    """Determines outcome based on rolls, calls effect handlers, shows Results View."""
    global current_combat_view_instance
    print("\n--- Finalizing Combat After Dice Rolls ---")
    info_frame = game_state.get("info_frame")
    if not info_frame: print("FATAL ERROR: info_frame missing in finalize_combat."); return

    cleanup_previous_combat_view() # Clear the roll view

    print(f"  Attacker Value: {combat_params['attacker_total']}")
    print(f"  Defender Value: {combat_params['defender_total']}")
    print(f"  Difference Dice ({combat_params['num_diff_dice']}): {diff_dice_rolls}")
    print(f"  Danger Die Roll: {danger_die_roll}")

    num_diff_dice = combat_params["num_diff_dice"]

    # Check win condition using combat.logic module
    combat_won = combat_logic.check_combat_win_condition(diff_dice_rolls, danger_die_roll, num_diff_dice)

    used_card = selected_value_card_info[0] if selected_value_card_info else None
    results_data = { # Prepare data for results view
        "win": combat_won, "automatic_win": False, "target": target_card,
        "defender_total": combat_params["defender_total"], "used_card": used_card,
        "attacker_total": combat_params["attacker_total"], "difference": combat_params["difference"],
        "num_diff_dice": num_diff_dice, "diff_dice_rolls": diff_dice_rolls,
        "danger_die": danger_die_roll, "consequences": []
    }

    # Call appropriate effect handler (from combat.effects) - populates consequences
    if combat_won:
        print("  Outcome: WIN!")
        combat_effects.handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager)
    else:
        print("  Outcome: LOSE!")
        combat_effects.handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager)

    # --- Display Results View ---
    print("  Displaying Combat Results View (Dice Roll)...")
    pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
    current_combat_view_instance = CombatResultsView(info_frame, results_data, pil_dice_images, results_callback)
    current_combat_view_instance.display()
    print("=== Combat Sequence Finished (Dice Roll) ===")


# --- END OF FILE combat/manager.py ---