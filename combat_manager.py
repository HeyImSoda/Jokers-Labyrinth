# --- START OF FILE combat_manager.py ---

import tkinter as tk
from tkinter import ttk, messagebox
import random # Needed for danger die shuffle
import config
import utils # For roll_dice
from card_logic import Card
import hand_manager # For clearing hand on Queen loss

# (CombatSetupWindow remains the same as before)
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

        target_rank = target_card.get_rank()
        target_value_display = target_rank if target_rank is not None else "N/A"
        if target_rank == 12: target_value_display = 12
        elif target_rank == 13: target_value_display = 13


        ttk.Label(self, text=f"Fight {target_card} (Value: {target_value_display})?",
                  font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(self, text="Use Equipment or Friendly Face Card from hand (optional):").pack(pady=5)

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
                card_rank = card.get_rank()
                card_value_display = card_rank if card_rank is not None else "N/A"
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

# --- CombatRollWindow Class ---
class CombatRollWindow(tk.Toplevel):
    """Modal window for interactively rolling combat dice."""
    def __init__(self, parent, player, target_card, target_row, target_col,
                 selected_value_card_info, game_state, combat_params):
        super().__init__(parent)
        self.parent = parent
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.title("Combat Roll")
        self.configure(padx=20, pady=20)

        # Store necessary data
        self.player = player
        self.target_card = target_card
        self.target_row = target_row
        self.target_col = target_col
        self.selected_value_card_info = selected_value_card_info
        self.game_state = game_state
        self.tk_dice_images = game_state["assets"].get("tk_dice", {})
        self.attacker_total = combat_params["attacker_total"]
        self.defender_total = combat_params["defender_total"]
        self.difference = combat_params["difference"]
        self.num_diff_dice = combat_params["num_diff_dice"]

        # State for rolling
        self.diff_dice_rolls = []
        self.diff_dice_labels = [] # To hold the image labels
        self.current_diff_die_index = 0
        self.danger_die_roll = None
        self.shuffle_count = 0

        # --- UI Elements ---
        info_frame = ttk.LabelFrame(self, text="Combat Details")
        info_frame.pack(fill='x', pady=(0, 10))
        used_card = selected_value_card_info[0] if selected_value_card_info else None
        ttk.Label(info_frame, text=f"Attacker: {self.attacker_total} (Card: {used_card})").pack(anchor='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Defender: {self.target_card} (Value: {self.defender_total})").pack(anchor='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Difference: {self.difference} -> Roll {self.num_diff_dice} dice").pack(anchor='w', padx=5, pady=2)

        # Frame for Difference Dice
        self.diff_dice_display_frame = ttk.LabelFrame(self, text="Difference Dice")
        # --- CORRECTED: Removed minheight ---
        self.diff_dice_display_frame.pack(fill='x', pady=5)
        # -----------------------------------

        # Frame for Danger Die
        self.danger_die_display_frame = ttk.LabelFrame(self, text="Danger Die")
        # --- CORRECTED: Removed minheight ---
        self.danger_die_display_frame.pack(fill='x', pady=5)
        # -----------------------------------
        # Placeholder label for danger die image
        self.danger_die_label = ttk.Label(self.danger_die_display_frame)
        self.danger_die_label.pack(pady=5)


        # Buttons Frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=(15, 0))

        self.roll_diff_button = ttk.Button(button_frame, text=f"Roll {self.num_diff_dice} Dice", command=self._start_diff_dice_roll)
        self.roll_diff_button.pack(side=tk.LEFT, padx=5, expand=True)

        self.roll_danger_button = ttk.Button(button_frame, text="Roll Danger Die", command=self._start_danger_die_roll, state=tk.DISABLED)
        self.roll_danger_button.pack(side=tk.RIGHT, padx=5, expand=True)


    def _start_diff_dice_roll(self):
        """Disables button and starts the sequential difference dice roll."""
        self.roll_diff_button.config(state=tk.DISABLED)
        self.diff_dice_rolls = [] # Clear previous rolls if any
        for lbl in self.diff_dice_labels: lbl.destroy() # Clear old labels
        self.diff_dice_labels = []
        self.current_diff_die_index = 0
        print("Rolling difference dice...")
        self._roll_next_diff_die() # Start the sequence

    def _roll_next_diff_die(self):
        """Rolls one difference die, displays it, and schedules the next."""
        if self.current_diff_die_index < self.num_diff_dice:
            roll = utils.roll_dice(1)[0]
            self.diff_dice_rolls.append(roll)
            print(f"  Rolled: {roll}")

            # Display the die image
            img = self.tk_dice_images.get(roll)
            if img:
                lbl = ttk.Label(self.diff_dice_display_frame, image=img)
                lbl.image = img # Keep ref
                lbl.pack(side=tk.LEFT, padx=3, pady=5)
                self.diff_dice_labels.append(lbl)
            else: # Fallback
                lbl = ttk.Label(self.diff_dice_display_frame, text=f"[{roll}]")
                lbl.pack(side=tk.LEFT, padx=3, pady=5)
                self.diff_dice_labels.append(lbl)

            self.current_diff_die_index += 1
            # Schedule the next roll after a delay
            self.after(config.DICE_ROLL_DELAY, self._roll_next_diff_die)
        else:
            # All difference dice rolled, enable danger die button
            print("Difference dice rolling complete.")
            self.roll_danger_button.config(state=tk.NORMAL)
            self.roll_danger_button.focus_set() # Set focus for convenience

    def _start_danger_die_roll(self):
        """Disables button and starts the danger die shuffle animation."""
        self.roll_danger_button.config(state=tk.DISABLED)
        self.shuffle_count = config.DICE_SHUFFLE_STEPS
        print("Rolling danger die (with shuffle)...")
        self._shuffle_danger_die()

    def _shuffle_danger_die(self):
        """Displays a random die face for shuffle effect."""
        if self.shuffle_count > 0:
            temp_roll = random.randint(1, 6)
            img = self.tk_dice_images.get(temp_roll)
            if img:
                self.danger_die_label.config(image=img)
                self.danger_die_label.image = img
            else:
                self.danger_die_label.config(text=f"[{temp_roll}]", image='') # Clear image if fallback

            self.shuffle_count -= 1
            self.after(config.DICE_SHUFFLE_DELAY, self._shuffle_danger_die)
        else:
            # Shuffle complete, roll the actual danger die
            self.danger_die_roll = utils.roll_dice(1)[0]
            print(f"  Final Danger Die: {self.danger_die_roll}")
            img = self.tk_dice_images.get(self.danger_die_roll)
            if img:
                self.danger_die_label.config(image=img)
                self.danger_die_label.image = img
            else:
                self.danger_die_label.config(text=f"[{self.danger_die_roll}]", image='')

            # Proceed to finalize combat after a short pause
            self.after(400, self._finalize) # Wait briefly after final die shown

    def _finalize(self):
        """Gathers results and calls the main finalize_combat function."""
        print("Finalizing combat resolution.")
        self.destroy() # Close this rolling window
        finalize_combat(
            self.parent, # Pass the root window
            self.player,
            self.target_card,
            self.target_row,
            self.target_col,
            self.selected_value_card_info,
            self.game_state,
            self.attacker_total,
            self.defender_total,
            self.difference,
            self.num_diff_dice,
            self.diff_dice_rolls, # Pass the collected rolls
            self.danger_die_roll  # Pass the final danger roll
        )


# (CombatResultsWindow remains the same as before)
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
        if not results_data['diff_dice_rolls']: # Handle case if 0 dice were rolled
             ttk.Label(diff_dice_frame, text="N/A").pack(side=tk.LEFT, padx=2)
        else:
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
        if danger_roll is None: # Handle case if danger die wasn't rolled (e.g., 0 diff dice?)
             ttk.Label(danger_die_frame, text="N/A").pack(side=tk.LEFT, padx=2)
        else:
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


# (get_value_cards_from_hand remains the same)
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

            is_equipment = (card_color == "red" and card_rank is not None and 2 <= card_rank <= 10)
            is_friendly_face = (card_rank in [12, 13] and card_suit == player_suit)

            if is_equipment or is_friendly_face:
                value_cards.append((card, r, c))

    return value_cards

# (initiate_combat remains the same)
def initiate_combat(root, player, target_card, target_row, target_col, game_state):
    """Starts the combat setup phase."""
    print(f"Initiating combat against {target_card} at ({target_row}, {target_col})")
    value_cards = get_value_cards_from_hand(game_state["hand_card_data"], player.suit)
    def combat_setup_callback(selected_value_card_info):
        if selected_value_card_info is False:
            print("Combat cancelled by player.")
            button = game_state["button_grid"][target_row][target_col]
            if button and button.winfo_exists(): button.config(state=tk.NORMAL)
            game_state["card_state_grid"][target_row][target_col] = config.STATE_FACE_UP
            return
        prepare_combat_resolution(root, player, target_card, target_row, target_col, selected_value_card_info, game_state)
    CombatSetupWindow(root, target_card, value_cards, combat_setup_callback)

# (prepare_combat_resolution remains the same)
def prepare_combat_resolution(root, player, target_card, target_row, target_col, selected_value_card_info, game_state):
    """Calculates combat parameters and opens the CombatRollWindow."""
    print("Preparing combat resolution...")
    used_card = selected_value_card_info[0] if selected_value_card_info else None
    attacker_total = 0
    if used_card:
        rank = used_card.get_rank()
        if rank == 12: attacker_total = 12
        elif rank == 13: attacker_total = 13
        elif rank is not None: attacker_total = rank
    defender_total = 0
    target_rank = target_card.get_rank()
    if target_rank == 12: defender_total = 12
    elif target_rank == 13: defender_total = 13
    elif target_rank is not None: defender_total = target_rank
    difference = abs(attacker_total - defender_total)
    num_diff_dice = 0
    if difference <= 1: num_diff_dice = 2
    elif difference <= 3: num_diff_dice = 3
    elif difference <= 6: num_diff_dice = 4
    elif difference <= 8: num_diff_dice = 5
    else: num_diff_dice = 6
    combat_params = {
        "attacker_total": attacker_total, "defender_total": defender_total,
        "difference": difference, "num_diff_dice": num_diff_dice,
    }
    print(f"  Attacker={attacker_total}, Defender={defender_total}, Diff={difference}, NumDice={num_diff_dice}")
    CombatRollWindow(root, player, target_card, target_row, target_col,
                     selected_value_card_info, game_state, combat_params)

# (finalize_combat remains the same)
def finalize_combat(root, player, target_card, target_row, target_col,
                    selected_value_card_info, game_state,
                    attacker_total, defender_total, difference, num_diff_dice,
                    diff_dice_rolls, danger_die_roll):
    """Determines outcome based on rolls and calls win/loss handlers."""
    print("Finalizing Combat...")
    print(f"  Difference Rolls: {diff_dice_rolls}")
    print(f"  Danger Die: {danger_die_roll}")
    combat_won = (danger_die_roll is not None) and (danger_die_roll not in diff_dice_rolls)
    used_card = selected_value_card_info[0] if selected_value_card_info else None
    results_data = {
        "win": combat_won, "target": target_card, "defender_total": defender_total,
        "used_card": used_card, "attacker_total": attacker_total, "difference": difference,
        "num_diff_dice": num_diff_dice, "diff_dice_rolls": diff_dice_rolls,
        "danger_die": danger_die_roll, "consequences": []
    }
    if combat_won:
        print("  Outcome: WIN!")
        handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data)
    else:
        print("  Outcome: LOSE!")
        handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data)
    tk_dice_images = game_state["assets"].get("tk_dice", {})
    CombatResultsWindow(root, results_data, tk_dice_images)


# (handle_combat_win remains the same)
def handle_combat_win(player, target_row, target_col, selected_value_card_info, game_state, results_data):
    """Applies consequences of winning combat."""
    button_grid = game_state["button_grid"]
    card_data_grid = game_state["card_data_grid"]
    card_state_grid = game_state["card_state_grid"]
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]
    if selected_value_card_info:
        used_card, hand_r, hand_c = selected_value_card_info
        if hand_manager.remove_card_from_hand(used_card, hand_card_data, hand_card_slots): results_data["consequences"].append(f"Discarded {used_card} from hand.")
        else: results_data["consequences"].append(f"Error removing {used_card} from hand.")
    target_card = card_data_grid[target_row][target_col]
    results_data["consequences"].append(f"Discarded {target_card} from the Dungeon.")
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists(): button.grid_forget()
    button_grid[target_row][target_col] = None
    card_data_grid[target_row][target_col] = None
    card_state_grid[target_row][target_col] = config.STATE_ACTION_TAKEN
    old_pos = player.position
    player.set_position(target_row, target_col)
    results_data["consequences"].append(f"Player moved from {old_pos} to ({target_row}, {target_col}).")


# (handle_combat_loss remains the same - already included re-enable logic)
def handle_combat_loss(player, target_row, target_col, selected_value_card_info, game_state, results_data):
    """Applies consequences of losing combat."""
    hand_card_data = game_state["hand_card_data"]
    hand_card_slots = game_state["hand_card_slots"]
    button_grid = game_state["button_grid"]
    card_state_grid = game_state["card_state_grid"]
    if selected_value_card_info:
        used_card, hand_r, hand_c = selected_value_card_info
        if hand_manager.remove_card_from_hand(used_card, hand_card_data, hand_card_slots): results_data["consequences"].append(f"Discarded {used_card} from hand.")
        else: results_data["consequences"].append(f"Error removing {used_card} from hand.")
    else: results_data["consequences"].append("No value card was used.")
    results_data["consequences"].append(f"Player cannot move past {results_data['target']}.")
    button = button_grid[target_row][target_col]
    if button and button.winfo_exists(): button.config(state=tk.NORMAL) # Re-enable button
    card_state_grid[target_row][target_col] = config.STATE_FACE_UP # Allow clicking again
    target_card = results_data['target']
    target_rank = target_card.get_rank()
    is_hostile_npc = target_rank in [12, 13]
    if is_hostile_npc:
        if target_rank == 12: # Lost to hostile Queen
            results_data["consequences"].append("Lost to hostile Queen: Discard all cards from hand!")
            hand_manager.clear_hand_display(hand_card_data, hand_card_slots)
        elif target_rank == 13: # Lost to hostile King
             results_data["consequences"].append("Lost to hostile King: Skip next turn! (Effect TBD)")
             if hasattr(player, 'set_skip_turn'): player.set_skip_turn(True)
    else: results_data["consequences"].append("Lost to Hazard.")

# --- END OF FILE combat_manager.py ---