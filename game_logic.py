# --- START OF FILE game_logic.py ---

import tkinter as tk
import config
import animation # Import animation functions
import card_actions # Import the new actions module

# --- Callback function after flip animation ---
def on_card_revealed(
    row, col,
    button_grid, card_data_grid, card_state_grid, # Grids
    assets # Asset components
    ):
    """
    Finalizes reveal after animation, sets final image, RE-ENABLES button for second click.
    Called by root.after() scheduled in animate_flip.

    Args:
        row, col: Coordinates of the card revealed.
        button_grid: 2D list holding Tkinter Button widgets or None.
        card_data_grid: 2D list holding Card objects or None.
        card_state_grid: 2D list holding card state constants.
        assets: Dictionary containing all loaded image assets (PIL and Tk).
    """
    # Access data using arguments
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
        else:
            print(f"Error: Could not find Tk image for key: {image_key} in on_card_revealed")
            # Use Tk back image from assets as fallback
            tk_back_image = assets.get("tk_photo_back")
            if tk_back_image:
                 button.config(image=tk_back_image, state=tk.DISABLED) # Fallback, disable
                 button.image = tk_back_image
            else:
                 # Absolute fallback if back image somehow missing
                 button.config(text="Error", state=tk.DISABLED)
            card_state_grid[row][col] = config.STATE_ACTION_TAKEN # State: Disabled (Error)

    elif card and not button:
         # This case means the button was likely removed (e.g. card sent to hand)
         # but the callback still fired. Ensure state is correct.
         if card_state_grid[row][col] != config.STATE_ACTION_TAKEN:
             # print(f"Note: Button missing in on_card_revealed for ({row},{col}), syncing state.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN


# --- Main Click Handler ---
def handle_card_click(
    row, col,
    root, player, # Core components
    card_data_grid, button_grid, card_state_grid, # Grids
    hand_card_data, hand_card_slots, # Hand components
    assets, info_frame_bg # UI/Asset components
    ):
    """
    Called when a button on the grid is clicked.
    Routes to flip animation OR calls card_actions.handle_card_action.
    Includes basic player adjacency check.

    Args:
        row, col: Coordinates of the clicked button.
        root: The main Tkinter window.
        player: The Player object instance.
        card_data_grid, button_grid, card_state_grid: Game state grids.
        hand_card_data, hand_card_slots: Hand display state.
        assets: Dictionary of all assets.
        info_frame_bg: Background color of the info frame.
    """
    # Bounds check
    if not (0 <= row < config.ROWS and 0 <= col < config.COLUMNS):
         print(f"Error: Click coordinates ({row},{col}) out of bounds.")
         return

    # --- Player Interaction Rule ---
    # Check if the player can interact with this card based on position
    # Uncomment this block when player movement is implemented and interaction should be restricted
    # if not player.can_interact(row, col):
    #     print(f"Player at {player.position} cannot interact with non-adjacent card at ({row}, {col}).")
    #     # Optional: Provide feedback to the user (e.g., flash the card?)
    #     return
    # --- End Player Interaction Rule ---


    button = button_grid[row][col] # Might be None if card was taken
    card = card_data_grid[row][col] # Might be None
    # Safely access state grid element
    try:
        current_state = card_state_grid[row][col]
    except IndexError:
        print(f"Error: State grid index out of bounds for ({row},{col})")
        return

    button_exists = button is not None and button.winfo_exists()
    button_state = button['state'] if button_exists else None

    # Ignore clicks on fully processed/removed slots or empty center
    if current_state == config.STATE_ACTION_TAKEN or card is None:
        # print(f"Ignoring click on ({row},{col}) - State: {current_state}, Card: {card}")
        return

    # Handle clicks based on state
    if current_state == config.STATE_FACE_DOWN: # Face Down -> Flip
        if button_exists and button_state == tk.NORMAL:
            print(f"First click on ({row},{col}). Flipping card...")
            button.config(state=tk.DISABLED) # Disable during animation

            # Prepare the callback with necessary arguments
            # We need a way to pass the required args to on_card_revealed when root.after calls it.
            # A lambda function is a good way to do this.
            reveal_callback_with_args = lambda r=row, c=col: on_card_revealed(
                r, c, button_grid, card_data_grid, card_state_grid, assets
            )

            animation.animate_flip(root, button, card, assets, reveal_callback_with_args, row, col)
        elif button_exists:
             print(f"Ignoring click on ({row},{col}) - Button not normal (State: {button_state})")
        else:
             print(f"Error: Clicked face-down slot ({row},{col}) but button is missing.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as error/disabled

    elif current_state == config.STATE_FACE_UP: # Face Up -> Action
        if button_exists and button_state == tk.NORMAL:
            print(f"Second click on ({row},{col}). Performing action...")
            # Call the action handler from the dedicated module, passing all required state
            card_actions.handle_card_action(
                row, col,
                card_data_grid, button_grid, card_state_grid,
                hand_card_data, hand_card_slots,
                assets, info_frame_bg
                # Pass player here if handle_card_action needs it: player=player
            )
        elif button_exists:
             print(f"Ignoring click on face-up card ({row},{col}) - Button not normal (State: {button_state})")
        else:
             # Button gone after reveal? Should not happen unless reveal failed badly.
             print(f"Error: Clicked face-up slot ({row},{col}) but button is missing.")
             card_state_grid[row][col] = config.STATE_ACTION_TAKEN # Mark as error/disabled

    else: # Should not happen if state checks are correct
        print(f"Warning: Unhandled click state for ({row},{col}) - GridState: {current_state}, Button Exists: {button_exists}, ButtonState: {button_state}")

# --- END OF FILE game_logic.py ---