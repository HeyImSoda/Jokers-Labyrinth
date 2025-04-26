# --- START OF FILE combat_manager.py ---

import tkinter as tk
from tkinter import ttk, messagebox
import config
import utils # For roll_dice
from card_logic import Card
import hand_manager # For clearing hand on Queen loss

class CombatSetupWindow(tk.Toplevel):
    """Modal window for selecting a value card before combat."""
    def __init__(self, parent, target_card, value_cards_in_hand, callback):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.title("Initiate Combat")

        self.target_card = target_card
        self.value_cards = value_cards_in_hand # List of (Card, row, col) tuples
        self.callback = callback
        self.selected_card_info = None

        self.configure(padx=15, pady=15)

        # --- UI Elements ---
        # Determine target value (use 12 for Q, 13 for K, rank otherwise)
        target_rank = target_card.get_rank()
        target_value_display = target_rank if target_rank else "N/A" # Handle Jokers potentially having None rank

        ttk.Label(self, text=f"Fight {target_card} (Value: {target_value_display})?",
                  font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(self, text="Use Equipment or Friendly Face Card from hand (optional):").pack(pady=5) # Updated text

        self.selection_var = tk.StringVar(self)
        self.selection_var.set("None")

        rb_none = ttk.Radiobutton(self, text="Use No Card", variable=self.selection_var,
                                  value="None", command=self._update_selection)
        rb_none.pack(anchor='w', padx=10)

        self.radio_buttons = {}
        if not self.value_cards:
             ttk.Label(self, text="(No valid value cards in hand)").pack(anchor='w', padx=10)
        else:
            for card, r, c in self.value_cards:
                value_str = f"card_{r}_{c}"
                # Determine display value (12 for Q, 13 for K, rank otherwise)
                card_rank = card.get_rank()
                card_value_display = card_rank if card_rank else "N/A" # Handle potential None rank
                if card_rank == 12: card_value_display = 12
                elif card_rank == 13: card_value_display = 13

                rb = ttk.Radiobutton(self, text=f"{card} (Value: {card_value_display})",
                                     variable=self.selection_var,
                                     value=value_str, command=self._update_selection)
                rb.pack(anchor='w', padx=10)
                self.radio_buttons[value_str] = (card, r, c)

        ttk.Separator(self, orient='horizontal').pack(fill='x', pady=10)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=(10, 0))
        fight_button = ttk.Button(button_frame, text="Fight!", command=self._confirm_fight)
        fight_button.pack(side=tk.LEFT, expand=True, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel)
        cancel_button.pack(side=tk.RIGHT, expand=True, padx=5)

        self.wait_window()

    def _update_selection(self):
        selection = self.selection_var.get()
        self.selected_card_info = None if selection == "None" else self.radio_buttons.get(selection)

    def _confirm_fight(self):
        self._update_selection()
        self.destroy()
        self.callback(self.selected_card_info)

    def _cancel(self):
        self.destroy()
        self.callback(False)

class CombatResultsWindow(tk.Toplevel):
    """Modal window to display combat results, now with dice images."""
    def __init__(self, parent, results_data, tk_dice_images): # Added tk_dice_images
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.title("Combat Results")
        self.configure(padx=20, pady=20)

        self.tk_dice_images = tk_dice_images # Store dice images

        outcome_text = "YOU WIN!" if results_data["win"] else "YOU LOSE..."
        outcome_color = "dark green" if results_data["win"] else "dark red"
        ttk.Label(self, text=outcome_text, font=("Arial", 16, "bold"), foreground=outcome_color).pack(pady=(0,15))

        details_frame = ttk.LabelFrame(self, text="Details")
        details_frame.pack(fill='x', pady=5)

        # --- Attacker/Defender Info ---
        ttk.Label(details_frame, text=f"Target: {results_data['target']} (Value: {results_data['defender_total']})").pack(anchor='w', padx=5, pady=2)
        used_card_text = f"Used: {results_data['used_card']} (Value: {results_data['attacker_total']})" if results_data['used_card'] else f"Used: None (Value: {results_data['attacker_total']})"
        ttk.Label(details_frame, text=used_card_text).pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Difference: {results_data['difference']}").pack(anchor='w', padx=5, pady=2)

        # --- Display Difference Dice Rolls ---
        diff_dice_frame = ttk.Frame(details_frame)
        diff_dice_frame.pack(anchor='w', padx=5, pady=2)
        ttk.Label(diff_dice_frame, text=f"Roll {results_data['num_diff_dice']} dice:").pack(side=tk.LEFT, padx=(0, 5))
        for roll in results_data['diff_dice_rolls']:
            img = self.tk_dice_images.get(roll)
            if img:
                lbl = ttk.Label(diff_dice_frame, image=img)
                lbl.image = img # Keep ref
                lbl.pack(side=tk.LEFT, padx=2)
            else: # Fallback to text if image missing
                ttk.Label(diff_dice_frame, text=f"[{roll}]").pack(side=tk.LEFT, padx=2)

        # --- Display Danger Die Roll ---
        danger_die_frame = ttk.Frame(details_frame)
        danger_die_frame.pack(anchor='w', padx=5, pady=2)
        ttk.Label(danger_die_frame, text="Danger Die:").pack(side=tk.LEFT, padx=(0, 5))
        danger_roll = results_data['danger_die']
        img = self.tk_dice_images.get(danger_roll)
        if img:
            lbl = ttk.Label(danger_die_frame, image=img)
            lbl.image = img # Keep ref
            lbl.pack(side=tk.LEFT, padx=2)
        else: # Fallback to text
            ttk.Label(danger_die_frame, text=f"[{danger_roll}]").pack(side=tk.LEFT, padx=2)


        # --- Consequences ---
        consequences_frame = ttk.LabelFrame(self, text="Consequences")
        consequences_frame.pack(fill='x', pady=10)
        if not results_data["consequences"]:
             ttk.Label(consequences_frame, text="- None").pack(anchor='w', padx=5, pady=2)
        else:
            for line in results_data["consequences"]:
                ttk.Label(consequences_frame, text=f"- {line}").pack(anchor='w', padx=5, pady=2)

        ok_button = ttk.Button(self, text="OK", command=self.destroy)
        ok_button.pack(pady=(15, 0))

        self.wait_window()

# --- UPDATED: get_value_cards_from_hand ---
def get_value_cards_from_hand(hand_card_data, player_suit):
    """Finds valid value cards (Red Numbers OR Friendly Q/K) in the hand."""
    value_cards = []
    for r in range(config.HAND_ROWS):
        for c in range(config.HAND_COLS):
            card = hand_card_data[r][c]
            if not card: continue # Skip empty slots

            card_color = card.get_color()
            card_rank = card.get_rank()
            card_suit = card.get_suit()

            is_equipment = (card_color == "red" and card_rank is not None and 2 <= card_rank <= 10)
            is_friendly_face = (card_rank in [12, 13] and card_suit == player_suit) # Queen=12, King=13

            if is_equipment or is_friendly_face:
                value_cards.append((card, r, c)) # Store card and its position

    return value_cards
# -----------------------------------------

def initiate_combat(root, player, target_card, target_row, target_col, game_state):
    """Starts the combat sequence."""
    print(f"Initiating combat against {target_card} at ({target_row}, {target_col})")

    # Pass player's suit to identify friendly face cards
    value_cards = get_value_cards_from_hand(game_state["hand_card_data"], player.suit)

    def combat_setup_callback(selected_value_card_info):
        if selected_value_card_info is False:
            print("Combat cancelled by player.")
            button = game_state["button_grid"][target_row][target_col]
            if button and button.winfo_exists():
                 button.config(state=tk.NORMAL)
                 game_state["card_state_grid"][target_row][target_col] = config.STATE_FACE_UP
            return
        resolve_combat(player, target_card, target_row, target_col, selected_value_card_info, game_state, root)

    CombatSetupWindow(root, target_card, value_cards, combat_setup_callback)


def resolve_combat(player, target_card, target_row, target_col, selected_value_card_info, game_state, root):
    """Calculates combat outcome and displays results."""
    used_card = selected_value_card_info[0] if selected_value_card_info else None

    # --- Determine attacker's value (0, Equipment rank, or 12/13 for Q/K) ---
    attacker_total = 0
    if used_card:
        rank = used_card.get_rank()
        if rank == 12: attacker_total = 12 # Queen value
        elif rank == 13: attacker_total = 13 # King value
        elif rank is not None: attacker_total = rank # Equipment value
    # -----------------------------------------------------------------------

    # --- Determine defender's value (12/13 for NPC Q/K, rank otherwise) ---
    defender_total = 0
    target_rank = target_card.get_rank()
    if target_rank == 12: defender_total = 12
    elif target_rank == 13: defender_total = 13
    elif target_rank is not None: defender_total = target_rank
    # Handle Jokers or cards with no rank? Assume 0 or some default? For now, uses rank.
    # --------------------------------------------------------------------

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
    danger_die = utils.roll_dice(1)[0]

    print(f"  Difference: {difference} -> Rolling {num_diff_dice} dice: {diff_dice_rolls}")
    print(f"  Danger Die: {danger_die}")

    combat_won = danger_die not in diff_dice_rolls

    results_data = {
        "win": combat_won, "target": target_card, "defender_total": defender_total,
        "used_card": used_card, "attacker_total": attacker_total, "difference": difference,
        "num_diff_dice": num_diff_dice, "diff_dice_rolls": diff_dice_rolls,
        "danger_die": danger_die, "consequences": []
    }

    if combat_won:
        print("  Outcome: WIN!")
        handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data)
    else:
        print("  Outcome: LOSE!")
        handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data)

    # Display results (pass Tk dice images from assets)
    tk_dice_images = game_state["assets"].get("tk_dice", {})
    CombatResultsWindow(root, results_data, tk_dice_images)


def handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data):
    """Applies consequences of winning combat."""
    button_grid = game_state["button_grid"]
    card_data_grid = game_state["card_data_grid"]
    # State grid updated by caller (handle_card_action sets to ACTION_TAKEN)
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]

    # 1. Discard used value card (if any) from hand data + display
    if selected_value_card_info:
        used_card, hand_r, hand_c = selected_value_card_info
        # Use hand_manager function for removal
        if hand_manager.remove_card_from_hand(used_card, hand_card_data, hand_card_slots):
             results_data["consequences"].append(f"Discarded {used_card} from hand.")
        else: # Should not happen if selection was valid
             results_data["consequences"].append(f"Error removing {used_card} from hand.")


    # 2. Discard hazard/NPC from grid
    target_card = card_data_grid[target_row][target_col] # Get card before clearing
    results_data["consequences"].append(f"Discarded {target_card} from the Dungeon.") # Log first
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists():
        button.grid_forget()
    button_grid[target_row][target_col] = None
    card_data_grid[target_row][target_col] = None
    # State grid remains ACTION_TAKEN, representing the now empty space

    # 3. Move player to the empty space
    old_pos = player.position
    player.set_position(target_row, target_col)
    results_data["consequences"].append(f"Player moved from {old_pos} to ({target_row}, {target_col}).")
    # TODO: Update player visual on grid


# --- UPDATED: handle_combat_loss ---
def handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data):
    """Applies consequences of losing combat."""
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]
    button_grid = game_state["button_grid"]
    card_state_grid = game_state["card_state_grid"] # Needed? Button disable handles interaction block

    # 1. Discard used value card (if any) from hand
    if selected_value_card_info:
        used_card, hand_r, hand_c = selected_value_card_info
        # Use hand_manager function for removal
        if hand_manager.remove_card_from_hand(used_card, hand_card_data, hand_card_slots):
             results_data["consequences"].append(f"Discarded {used_card} from hand.")
        else:
             results_data["consequences"].append(f"Error removing {used_card} from hand.")
    else:
        results_data["consequences"].append("No value card was used.")

    # 2. Cannot move past Hazard/NPC - Player position doesn't change
    results_data["consequences"].append(f"Player cannot move past {results_data['target']}.")
    # Ensure the button for the target remains disabled to prevent immediate re-click
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists():
        button.config(state=tk.DISABLED)
    # State remains ACTION_TAKEN

    # 3. Resolve NPC effects
    target_card = results_data['target']
    target_rank = target_card.get_rank()
    is_hostile_npc = target_rank in [12, 13] # Assuming non-friendly Q/K triggered combat

    if is_hostile_npc:
        if target_rank == 12: # Lost to hostile Queen
            results_data["consequences"].append("Lost to hostile Queen: Discard all cards from hand!")
            hand_manager.clear_hand_display(hand_card_data, hand_card_slots) # Clear data and visuals
        elif target_rank == 13: # Lost to hostile King
             results_data["consequences"].append("Lost to hostile King: Skip next turn! (Effect TBD)")
             # Future: Set a flag on the player object or game state to handle turn skipping
             if hasattr(player, 'set_skip_turn'): player.set_skip_turn(True) # Example if method exists
    else: # Hazard (Black Number)
        results_data["consequences"].append("Lost to Hazard.")
# ------------------------------------

# --- END OF FILE combat_manager.py ---