# --- START OF FILE game_logic.py ---

import tkinter as tk
import config
import animation # Import animation functions
import card_actions # Import the actions module
# No combat_manager needed here directly if card_actions handles initiation

# --- Callback function after flip animation ---
# (This function remains the same - it only affects the grid button)
def on_card_revealed(
    row, col,
    button_grid, card_data_grid, card_state_grid, # Grids
    assets # Asset components
    ):
    """
    Finalizes reveal after animation, sets final image, RE-ENABLES button for second click.
    Called by root.after() scheduled in animate_flip.
    """
    button = button_grid[row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS and button_grid[row][col]) else None
    card = card_data_grid[row][col] if (0 <= row < config.ROWS and 0 <= col < config.COLUMNS) else None

    if button and card and button.winfo_exists():
        suit_key = str(card.get_suit()).lower()
        rank_key = str(card.get_rank_string()).lower()
        image_key = f"{suit_key}_{rank_key}"
        tk_faces_dict = assets.get("tk_faces", {}) # Safely get Tk faces dict
        tk_photo_final = tk_faces_dict.get(image_key) # Look in the Tk faces dict

        if tk_photo_final:
            button.config(image=tk_photo_final, state=tk.NORMAL) # Set image and re-enable
            button.image = tk_photo_final
            card_state_grid[row][col] = config.STATE_FACE_UP # State: Face Up
            print(f"Card at ({row},{col}) revealed as {card}. State set to FACE_UP.")
        else:
            print(f"Error: Could not find Tk image for key: {image_key} in on_card_revealed")
            tk_back_image = assets.get("tk_photo_back")
            fallback_text = "Error"
            if tk_back_image:
                 button.config(image=tk_back_image, state=tk.DISABLED) # Fallback, disable
                 button.image = tk_back_image
                 fallback_text = f"!\n{image_key[:5]}" # Show partial key on back
            button.config(text=fallback_text, compound=tk.CENTER, fg="red") # Show text over image
            card_state_grid[row][col] = config.STATE_ACTION_TAKEN # State: Disabled (Error)
            print(f"State for ({row},{col}) set to ACTION_TAKEN due to missing image.")

    elif card and not button:
         if card_state_grid[row][col] != config.STATE_ACTION_TAKEN:
             # print(f"Note: Button missing in on_card_revealed for ({row},{col}), syncing state.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN


# --- Main Click Handler ---
def handle_card_click(
    row, col,
    root, player, # Core components
    card_data_grid, button_grid, card_state_grid, # Grids
    hand_card_data, hand_card_slots, # Hand components
    assets, # Asset components
    info_frame, hand_frame, # UI Frames passed from main
    info_frame_bg # UI Style
    ):
    """
    Called when a button on the grid is clicked.
    Routes to flip animation OR calls card_actions.handle_card_action.
    Includes basic player adjacency check (still commented out).
    Passes UI frames needed for embedded combat display.
    """
    # Bounds check
    if not (0 <= row < config.ROWS and 0 <= col < config.COLUMNS):
         print(f"Error: Click coordinates ({row},{col}) out of bounds.")
         return

    # --- Player Interaction Rule (Optional) ---
    # if not player.can_interact(row, col):
    #     print(f"Player at {player.position} cannot interact with non-adjacent card at ({row}, {col}).")
    #     return
    # --- End Player Interaction Rule ---

    button = button_grid[row][col] # Might be None if card was taken
    card = card_data_grid[row][col] # Might be None
    try:
        current_state = card_state_grid[row][col]
    except IndexError:
        print(f"Error: State grid index out of bounds for ({row},{col})")
        return

    button_exists = button is not None and isinstance(button, tk.Button) and button.winfo_exists()
    button_state = button['state'] if button_exists else None

    print(f"Click on ({row},{col}). Card: {card}. Current State: {current_state}. Button Exists: {button_exists}. Button State: {button_state}")

    # Ignore clicks on fully processed/removed slots or empty center
    if current_state == config.STATE_ACTION_TAKEN or card is None:
        print(f"Ignoring click on ({row},{col}) - State is ACTION_TAKEN or no card.")
        return

    # Ignore clicks if button is disabled (e.g., during animation or combat)
    if button_exists and button_state == tk.DISABLED:
        print(f"Ignoring click on ({row},{col}) - Button is DISABLED.")
        return

    # Handle clicks based on state
    if current_state == config.STATE_FACE_DOWN: # Face Down -> Flip
        if button_exists: # Should always exist if state is FACE_DOWN unless error
            print(f"First click on ({row},{col}). Flipping card...")
            button.config(state=tk.DISABLED) # Disable during animation

            # --- Lambda for callback needs all args required by on_card_revealed ---
            reveal_callback_with_args = lambda r=row, c=col: on_card_revealed(
                r, c,
                button_grid, card_data_grid, card_state_grid, # Pass grids
                assets # Pass assets
            )

            # Pass the lambda function to animate_flip
            animation.animate_flip(root, button, card, assets, reveal_callback_with_args, row, col)
        else:
             print(f"Error: Clicked face-down slot ({row},{col}) but button is missing.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as error/disabled

    elif current_state == config.STATE_FACE_UP: # Face Up -> Action
        if button_exists:
            print(f"Second click on ({row},{col}). Performing action...")
            # Call the action handler, passing all required state *and UI frames*
            card_actions.handle_card_action(
                row, col,
                root, player, # Core components
                card_data_grid, button_grid, card_state_grid, # Game state grids
                hand_card_data, hand_card_slots, # Hand state
                assets, # Assets
                info_frame, hand_frame, # UI Frames for combat display
                info_frame_bg # Styling
            )
        else:
             print(f"Error: Clicked face-up slot ({row},{col}) but button is missing.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as error/disabled

    else: # Should not happen
        print(f"Warning: Unhandled click state for ({row},{col}) - GridState: {current_state}")

# --- END OF FILE game_logic.py ---