# --- START OF FILE combat_manager.py ---

import tkinter as tk
from tkinter import ttk, messagebox
import config
import utils # For roll_dice
from card_logic import Card # For type checking/accessing card info

class CombatSetupWindow(tk.Toplevel):
    """Modal window for selecting a value card before combat."""
    def __init__(self, parent, target_card, value_cards_in_hand, callback):
        super().__init__(parent)
        self.transient(parent) # Stay on top of parent
        self.grab_set()       # Make modal
        self.resizable(False, False)
        self.title("Initiate Combat")

        self.target_card = target_card
        self.value_cards = value_cards_in_hand # List of (Card, row, col) tuples
        self.callback = callback # Function to call with result
        self.selected_card_info = None # Will store (Card, row, col) or None

        self.configure(padx=15, pady=15)

        # --- UI Elements ---
        ttk.Label(self, text=f"Fight {target_card} (Value: {target_card.get_rank()})?",
                  font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(self, text="Use a value card from your hand (optional):").pack(pady=5)

        self.selection_var = tk.StringVar(self)
        self.selection_var.set("None") # Default to no card

        # Option for NO card
        rb_none = ttk.Radiobutton(self, text="Use No Card", variable=self.selection_var,
                                  value="None", command=self._update_selection)
        rb_none.pack(anchor='w', padx=10)

        # Options for each value card
        self.radio_buttons = {}
        if not self.value_cards:
             ttk.Label(self, text="(No valid value cards in hand)").pack(anchor='w', padx=10)
        else:
            for card, r, c in self.value_cards:
                value_str = f"card_{r}_{c}" # Unique value for radio button
                rb = ttk.Radiobutton(self, text=f"{card} (Value: {card.get_rank()})",
                                     variable=self.selection_var,
                                     value=value_str, command=self._update_selection)
                rb.pack(anchor='w', padx=10)
                self.radio_buttons[value_str] = (card, r, c) # Map value string back to card info

        ttk.Separator(self, orient='horizontal').pack(fill='x', pady=10)

        # Action Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=(10, 0))

        fight_button = ttk.Button(button_frame, text="Fight!", command=self._confirm_fight)
        fight_button.pack(side=tk.LEFT, expand=True, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel)
        cancel_button.pack(side=tk.RIGHT, expand=True, padx=5)

        self.wait_window() # Pause execution until this window is closed

    def _update_selection(self):
        """Updates the internal selected card based on radio button."""
        selection = self.selection_var.get()
        if selection == "None":
            self.selected_card_info = None
        else:
            self.selected_card_info = self.radio_buttons.get(selection)
        # print(f"Selection updated: {self.selected_card_info}") # Debug print

    def _confirm_fight(self):
        """Calls the callback with the selected card info and closes."""
        self._update_selection() # Ensure selection is current
        self.destroy()
        self.callback(self.selected_card_info) # Pass selection back

    def _cancel(self):
        """Calls the callback with False (indicating cancellation) and closes."""
        self.destroy()
        self.callback(False) # Indicate cancellation

class CombatResultsWindow(tk.Toplevel):
    """Modal window to display combat results."""
    def __init__(self, parent, results_data):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.title("Combat Results")
        self.configure(padx=20, pady=20)

        outcome_text = "YOU WIN!" if results_data["win"] else "YOU LOSE..."
        outcome_color = "dark green" if results_data["win"] else "dark red"

        ttk.Label(self, text=outcome_text, font=("Arial", 16, "bold"), foreground=outcome_color).pack(pady=(0,15))

        details_frame = ttk.LabelFrame(self, text="Details")
        details_frame.pack(fill='x', pady=5)

        ttk.Label(details_frame, text=f"Target: {results_data['target']} (Value: {results_data['defender_total']})").pack(anchor='w', padx=5, pady=2)
        used_card_text = f"Used: {results_data['used_card']} (Value: {results_data['attacker_total']})" if results_data['used_card'] else f"Used: None (Value: {results_data['attacker_total']})"
        ttk.Label(details_frame, text=used_card_text).pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Difference: {results_data['difference']}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Roll {results_data['num_diff_dice']} dice: {results_data['diff_dice_rolls']}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Danger Die: {results_data['danger_die']}").pack(anchor='w', padx=5, pady=2)

        consequences_frame = ttk.LabelFrame(self, text="Consequences")
        consequences_frame.pack(fill='x', pady=10)
        for line in results_data["consequences"]:
            ttk.Label(consequences_frame, text=f"- {line}").pack(anchor='w', padx=5, pady=2)

        ok_button = ttk.Button(self, text="OK", command=self.destroy)
        ok_button.pack(pady=(15, 0))

        self.wait_window()


def get_value_cards_from_hand(hand_card_data):
    """Finds Red Number cards in the hand."""
    value_cards = []
    for r in range(config.HAND_ROWS):
        for c in range(config.HAND_COLS):
            card = hand_card_data[r][c]
            if card and card.get_color() == "red" and card.rank is not None and 2 <= card.rank <= 10:
                value_cards.append((card, r, c)) # Store card and its position in hand grid
    return value_cards


def initiate_combat(root, player, target_card, target_row, target_col, game_state):
    """
    Starts the combat sequence: gets value cards, shows selection window.

    Args:
        root: The main Tkinter window.
        player: The Player object.
        target_card: The Card object being fought.
        target_row, target_col: Grid coordinates of the target card.
        game_state: Dictionary containing references to grids, hand, assets etc.
                    Expected keys: 'card_data_grid', 'button_grid', 'card_state_grid',
                                   'hand_card_data', 'hand_card_slots', 'assets'
    """
    print(f"Initiating combat against {target_card} at ({target_row}, {target_col})")

    value_cards = get_value_cards_from_hand(game_state["hand_card_data"])

    # Define the callback function that CombatSetupWindow will call
    def combat_setup_callback(selected_value_card_info):
        if selected_value_card_info is False:
            print("Combat cancelled by player.")
            # Re-enable the target button if combat is cancelled before resolution
            button = game_state["button_grid"][target_row][target_col]
            if button and button.winfo_exists():
                 button.config(state=tk.NORMAL)
                 game_state["card_state_grid"][target_row][target_col] = config.STATE_FACE_UP # Revert state
            return

        # Proceed to resolve combat
        resolve_combat(player, target_card, target_row, target_col, selected_value_card_info, game_state, root)

    # Show the modal setup window
    CombatSetupWindow(root, target_card, value_cards, combat_setup_callback)


def resolve_combat(player, target_card, target_row, target_col, selected_value_card_info, game_state, root):
    """
    Calculates combat outcome based on selection and rules.

    Args:
        player: The Player object.
        target_card: The Card being fought.
        target_row, target_col: Coordinates of the target.
        selected_value_card_info: (Card, r, c) tuple for the used value card, or None.
        game_state: Dictionary with game state components.
        root: The main Tk window (for the results pop-up).
    """
    used_card = selected_value_card_info[0] if selected_value_card_info else None
    attacker_total = used_card.get_rank() if used_card else 0
    defender_total = target_card.get_rank()

    print(f"Resolving Combat: Attacker={attacker_total} (Card: {used_card}) vs Defender={defender_total} (Card: {target_card})")

    difference = abs(attacker_total - defender_total)

    # Determine number of dice based on difference
    num_diff_dice = 0
    if difference <= 1: num_diff_dice = 2
    elif difference <= 3: num_diff_dice = 3
    elif difference <= 6: num_diff_dice = 4
    elif difference <= 8: num_diff_dice = 5
    else: num_diff_dice = 6 # 9+

    # Roll dice
    diff_dice_rolls = utils.roll_dice(num_diff_dice)
    danger_die = utils.roll_dice(1)[0] # Roll the single danger die

    print(f"  Difference: {difference} -> Rolling {num_diff_dice} dice: {diff_dice_rolls}")
    print(f"  Danger Die: {danger_die}")

    # Determine outcome
    combat_won = danger_die not in diff_dice_rolls

    results_data = {
        "win": combat_won,
        "target": target_card,
        "defender_total": defender_total,
        "used_card": used_card,
        "attacker_total": attacker_total,
        "difference": difference,
        "num_diff_dice": num_diff_dice,
        "diff_dice_rolls": diff_dice_rolls,
        "danger_die": danger_die,
        "consequences": []
    }

    if combat_won:
        print("  Outcome: WIN!")
        handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data)
    else:
        print("  Outcome: LOSE!")
        handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data)

    # Display results in a pop-up
    CombatResultsWindow(root, results_data)


def handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data):
    """Applies consequences of winning combat."""
    button_grid = game_state["button_grid"]
    card_data_grid = game_state["card_data_grid"]
    card_state_grid = game_state["card_state_grid"]
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"] # Needed to clear visual if card used

    # 1. Discard used value card (if any) from hand
    if selected_value_card_info:
        used_card, hand_r, hand_c = selected_value_card_info
        hand_card_data[hand_r][hand_c] = None
        # Clear the visual slot in the hand
        slot_label = hand_card_slots[hand_r][hand_c]
        if slot_label and slot_label.winfo_exists():
            slot_label.config(image='', bg=slot_label.master.cget('bg')) # Reset to background
            slot_label.image = None # Clear reference
        results_data["consequences"].append(f"Discarded {used_card} from hand.")

    # 2. Discard hazard/NPC from grid
    target_card = card_data_grid[target_row][target_col]
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists():
        button.grid_forget()
        button_grid[target_row][target_col] = None
    card_data_grid[target_row][target_col] = None
    # State is already ACTION_TAKEN from card_actions, which is correct for an empty space
    results_data["consequences"].append(f"Discarded {target_card} from the Dungeon.")

    # 3. Move player to the empty space
    old_pos = player.position
    player.set_position(target_row, target_col)
    # TODO: Update player visual on grid when implemented
    results_data["consequences"].append(f"Player moved from {old_pos} to ({target_row}, {target_col}).")


def handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data):
    """Applies consequences of losing combat."""
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]
    button_grid = game_state["button_grid"]
    card_state_grid = game_state["card_state_grid"]

    # 1. Discard used value card (if any) from hand
    if selected_value_card_info:
        used_card, hand_r, hand_c = selected_value_card_info
        hand_card_data[hand_r][hand_c] = None
        # Clear the visual slot
        slot_label = hand_card_slots[hand_r][hand_c]
        if slot_label and slot_label.winfo_exists():
            slot_label.config(image='', bg=slot_label.master.cget('bg'))
            slot_label.image = None
        results_data["consequences"].append(f"Discarded {used_card} from hand.")
    else:
        results_data["consequences"].append("No value card was used.")

    # 2. Cannot move past Hazard/NPC
    results_data["consequences"].append(f"Player cannot move past {results_data['target']}.")
    # Button should remain disabled, state remains ACTION_TAKEN until player moves away or tries again?
    # For now, keep it disabled. Player needs to move away.
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists():
        button.config(state=tk.DISABLED) # Ensure it's disabled

    # 3. Resolve NPC effects (Placeholder)
    target_card = results_data['target']
    if target_card.get_rank() in [12, 13]: # Queen or King (NPCs)
        results_data["consequences"].append(f"Lost to NPC: Resolve {target_card}'s effect (Not Implemented Yet).")
        # Future: Add specific effects here based on target_card type
    else: # Hazard (Black Number)
        results_data["consequences"].append("Lost to Hazard.")

# --- END OF FILE combat_manager.py ---