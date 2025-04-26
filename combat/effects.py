# --- START OF FILE combat/effects.py ---

import tkinter as tk # Needed for state constants? Maybe move state consts to config
import config # For states, hand layout?
# Needs hand_manager for manipulating hand
# Needs Player type for setting skip turn?
# Best to pass needed objects (player, game_state, hand_manager) as arguments

def handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager_module):
    """Applies consequences of winning combat."""
    print(f"Handling Combat Win at ({target_row}, {target_col})")
    button_grid = game_state["button_grid"]
    card_data_grid = game_state["card_data_grid"]
    card_state_grid = game_state["card_state_grid"]
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]
    tk_card_face_images = game_state["assets"].get("tk_faces", {})

    # 1. Discard used value card (if any)
    if selected_value_card_info:
        used_card, _, _ = selected_value_card_info # Don't need r, c from hand here
        # Use the passed hand_manager module
        if hand_manager_module.remove_card_from_hand(used_card, hand_card_data, hand_card_slots, tk_card_face_images):
             results_data["consequences"].append(f"Discarded {used_card} from hand.")
        else:
             results_data["consequences"].append(f"Error removing {used_card} from hand.")
             print(f"Error: Could not find/remove {used_card} from hand data")

    # 2. Discard hazard/NPC from grid
    target_card = card_data_grid[target_row][target_col] # Get ref before clearing
    results_data["consequences"].append(f"Discarded {target_card} from the Dungeon.")
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists():
        button.grid_forget()
    button_grid[target_row][target_col] = None
    card_data_grid[target_row][target_col] = None
    card_state_grid[target_row][target_col] = config.STATE_ACTION_TAKEN

    # 3. Move player to the now empty space
    old_pos = player.position
    player.set_position(target_row, target_col)
    results_data["consequences"].append(f"Player moved from {old_pos} to ({target_row}, {target_col}).")


def handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data, hand_manager_module):
    """Applies consequences of losing combat."""
    print(f"Handling Combat Loss at ({target_row}, {target_col})")
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]
    button_grid = game_state["button_grid"]
    card_state_grid = game_state["card_state_grid"]
    tk_card_face_images = game_state["assets"].get("tk_faces", {})

    # 1. Discard used value card (if any)
    if selected_value_card_info:
        used_card, _, _ = selected_value_card_info
        if hand_manager_module.remove_card_from_hand(used_card, hand_card_data, hand_card_slots, tk_card_face_images):
             results_data["consequences"].append(f"Discarded {used_card} from hand.")
        else:
            results_data["consequences"].append(f"Error removing {used_card} from hand.")
            print(f"Error: Could not find/remove {used_card} from hand data")
    else:
        results_data["consequences"].append("No value card was used in the fight.")

    # 2. Cannot move past Hazard/NPC - Re-enable button, reset state
    results_data["consequences"].append(f"Player cannot move past {results_data['target']}.")
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists():
        button.config(state=tk.NORMAL)
    card_state_grid[target_row][target_col] = config.STATE_FACE_UP # Allow clicking again

    # 3. Resolve specific NPC loss effects (Queens, Kings)
    target_card = results_data['target']
    target_rank = target_card.get_rank()
    # Need player suit to know if Q/K was hostile - check card color/rank only?
    # Rulebook implies combat is only initiated vs *hostile* NPCs or hazards.
    is_hostile_npc = target_rank in [12, 13] # Assume hostility if we fought it

    if is_hostile_npc:
        if target_rank == 12: # Lost to hostile Queen
            results_data["consequences"].append("Lost to hostile Queen: Discard all cards from hand!")
            hand_manager_module.clear_hand_display(hand_card_data, hand_card_slots)
        elif target_rank == 13: # Lost to hostile King
             results_data["consequences"].append("Lost to hostile King: Skip next turn!")
             if hasattr(player, 'set_skip_turn'):
                 player.set_skip_turn(True)
             else:
                 print("Warning: Player object doesn't have 'set_skip_turn' method.")
    else: # Lost to a Hazard (Black Number Card)
         results_data["consequences"].append("Lost to Hazard. Blocked movement.")

# --- END OF FILE combat/effects.py ---