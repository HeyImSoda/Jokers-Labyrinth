# --- START OF FILE combat_ui.py ---

import assets_manager
import tkinter as tk
from tkinter import ttk, messagebox
import random # Needed for dice shuffle
# --- ADDED MISSING IMPORT ---
from PIL import ImageTk
# ---------------------------
import config
import utils # For roll_dice
# No direct Card logic needed here, but maybe config/utils

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
        target_value_display = "N/A" # Default
        # --- Corrected Value Display for Q/K/Nums ---
        if target_rank == 12: target_value_display = 12
        elif target_rank == 13: target_value_display = 13
        elif target_rank is not None and 2 <= target_rank <= 10: target_value_display = target_rank
        # --- End Correction ---

        ttk.Label(self, text=f"Fight {target_card} (Value: {target_value_display})?",
                  font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(self, text="Use Equipment or Friendly Face Card from hand (optional):").pack(pady=5)

        self.selection_var = tk.StringVar(self)
        self.selection_var.set("None")

        rb_none = ttk.Radiobutton(self, text="Use No Card (Value: 0)", variable=self.selection_var,
                                  value="None", command=self._update_selection) # Clarified value
        rb_none.pack(anchor='w', padx=10)

        self.radio_buttons = {}
        if not self.value_cards:
             ttk.Label(self, text="(No valid value cards in hand)").pack(anchor='w', padx=10)
        else:
            for card, r, c in self.value_cards:
                value_str = f"card_{r}_{c}"
                card_rank = card.get_rank()
                card_value_display = "N/A" # Default
                # --- Corrected Value Display for Q/K/Nums ---
                if card_rank == 12: card_value_display = 12
                elif card_rank == 13: card_value_display = 13
                elif card_rank is not None and 2 <= card_rank <= 10: card_value_display = card_rank
                # --- End Correction ---

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
        # print(f"Debug: Selected card info: {self.selected_card_info}") # Optional debug

    def _confirm_fight(self):
        self._update_selection() # Ensure latest selection is captured
        self.destroy()
        self.callback(self.selected_card_info) # Pass selection (or None) back

    def _cancel(self):
        self.destroy()
        self.callback(False) # Indicate cancellation

# --- MODIFIED: CombatRollWindow ---
class CombatRollWindow(tk.Toplevel):
    """Modal window for interactively rolling combat dice with shuffle animation."""
    def __init__(self, parent, player, target_card, target_row, target_col,
                 selected_value_card_info, game_state, combat_params, finalize_callback): # Added finalize_callback
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
        # --- MODIFIED: Access PIL images, create Tk images on demand if needed ---
        self.pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
        self.tk_dice_images = {} # Cache Tk images as they are created
        # ------------------------------------------------------------------------
        self.attacker_total = combat_params["attacker_total"]
        self.defender_total = combat_params["defender_total"]
        self.difference = combat_params["difference"]
        self.num_diff_dice = combat_params["num_diff_dice"]
        self.finalize_callback = finalize_callback # Store callback

        # State for rolling
        self.diff_dice_rolls = []
        self.diff_dice_labels = [] # To hold the image labels
        self.danger_die_roll = None
        self.shuffle_count = 0

        # --- UI Elements ---
        info_frame = ttk.LabelFrame(self, text="Combat Details")
        info_frame.pack(fill='x', pady=(0, 10))
        used_card = selected_value_card_info[0] if selected_value_card_info else "None"
        ttk.Label(info_frame, text=f"Attacker: {self.attacker_total} (Card: {used_card})").pack(anchor='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Defender: {self.target_card} (Value: {self.defender_total})").pack(anchor='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Difference: {self.difference} -> Roll {self.num_diff_dice} dice").pack(anchor='w', padx=5, pady=2)

        # Frame for Difference Dice
        self.diff_dice_display_frame = ttk.LabelFrame(self, text="Difference Dice")
        self.diff_dice_display_frame.pack(fill='x', pady=5)
        # Set a minimum height to prevent collapsing when empty/loading
        self.diff_dice_display_frame.config(height=max(1, int(assets_manager.load_pil_assets().get('height', 50) * config.DICE_SCALE_FACTOR * 1.2)))


        # Frame for Danger Die
        self.danger_die_display_frame = ttk.LabelFrame(self, text="Danger Die")
        self.danger_die_display_frame.pack(fill='x', pady=5)
        # Set a minimum height
        self.danger_die_display_frame.config(height=max(1, int(assets_manager.load_pil_assets().get('height', 50) * config.DICE_SCALE_FACTOR * 1.2)))
        self.danger_die_label = ttk.Label(self.danger_die_display_frame)
        self.danger_die_label.pack(pady=5)


        # Buttons Frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=(15, 0))

        self.roll_diff_button = ttk.Button(button_frame, text=f"Roll {self.num_diff_dice} Dice", command=self._start_diff_dice_roll)
        self.roll_diff_button.pack(side=tk.LEFT, padx=5, expand=True)

        self.roll_danger_button = ttk.Button(button_frame, text="Roll Danger Die", command=self._start_danger_die_roll, state=tk.DISABLED)
        self.roll_danger_button.pack(side=tk.RIGHT, padx=5, expand=True)

        # --- Start the difference dice roll immediately if needed ---
        if self.num_diff_dice > 0:
             self._setup_diff_dice_labels() # Create labels first
             self._start_diff_dice_roll()   # Start the shuffle
        else:
             # If 0 difference dice, can proceed directly to danger die
             self.roll_diff_button.config(state=tk.DISABLED)
             self.roll_danger_button.config(state=tk.NORMAL)
             ttk.Label(self.diff_dice_display_frame, text="N/A (Difference <= 1)").pack(padx=5, pady=5)

    # --- Helper to get/create Tkinter PhotoImage ---
    def _get_tk_dice_image(self, value):
        """Gets a Tk dice image, creating it from PIL if not cached."""
        if value not in self.tk_dice_images:
            pil_img = self.pil_dice_images.get(value)
            if pil_img:
                try:
                    # Create with self (the Toplevel window) as master
                    self.tk_dice_images[value] = ImageTk.PhotoImage(pil_img, master=self)
                except Exception as e:
                    print(f"Error creating Tk dice image for {value}: {e}")
                    # Check if window still exists before trying to log more errors
                    if self.winfo_exists():
                        messagebox.showerror("Image Error", f"Failed to load dice image {value}.\nPlease check asset files.", parent=self)
                    self.tk_dice_images[value] = None # Avoid retrying
            else:
                 print(f"Warning: PIL dice image not found for value {value}")
                 self.tk_dice_images[value] = None
        return self.tk_dice_images.get(value)

    # --- Setup difference dice labels ---
    def _setup_diff_dice_labels(self):
        """Creates the label widgets for difference dice before shuffling."""
        # Clear any existing labels first
        for lbl in self.diff_dice_labels:
             if lbl.winfo_exists(): lbl.destroy()
        self.diff_dice_labels = []

        for i in range(self.num_diff_dice):
            # Create label, but don't set image yet (or set placeholder)
            lbl = ttk.Label(self.diff_dice_display_frame, text="?") # Placeholder text
            lbl.pack(side=tk.LEFT, padx=3, pady=5)
            self.diff_dice_labels.append(lbl)

    # --- Start difference dice roll (now starts shuffle) ---
    def _start_diff_dice_roll(self):
        """Disables button and starts the difference dice shuffle animation."""
        if not self.winfo_exists(): return # Stop if window closed
        self.roll_diff_button.config(state=tk.DISABLED)
        self.diff_dice_rolls = [] # Clear previous rolls if any

        # Ensure labels are created if not already (e.g., if called manually after setup)
        if not self.diff_dice_labels and self.num_diff_dice > 0:
            self._setup_diff_dice_labels()

        if not self.diff_dice_labels: # Still no labels? Nothing to roll.
             print("Warning: No difference dice labels to animate.")
             if self.winfo_exists(): self.roll_danger_button.config(state=tk.NORMAL) # Allow proceeding
             return

        self.shuffle_count = config.DICE_SHUFFLE_STEPS
        print(f"Shuffling {self.num_diff_dice} difference dice...")
        self._shuffle_diff_dice() # Start the shuffle sequence

    # --- Shuffle difference dice animation ---
    def _shuffle_diff_dice(self):
        """Displays random die faces for shuffle effect across all diff dice labels."""
        if not self.winfo_exists(): return # Stop if window closed

        if self.shuffle_count > 0:
            for lbl in self.diff_dice_labels:
                if not lbl.winfo_exists(): continue # Skip destroyed labels
                temp_roll = random.randint(1, 6)
                img = self._get_tk_dice_image(temp_roll)
                if img:
                    lbl.config(image=img, text='') # Set image, clear text
                    lbl.image = img # Keep ref
                else: # Fallback text if image fails
                    lbl.config(text=f"[{temp_roll}]", image='')

            self.shuffle_count -= 1
            # Use 'after' on self (the Toplevel window)
            self.after(config.DICE_SHUFFLE_DELAY, self._shuffle_diff_dice)
        else:
            # Shuffle complete, roll the actual difference dice
            self.diff_dice_rolls = utils.roll_dice(self.num_diff_dice)
            print(f"  Actual Difference Rolls: {self.diff_dice_rolls}")

            # Display the final rolls
            for i, lbl in enumerate(self.diff_dice_labels):
                if not lbl.winfo_exists(): continue # Skip destroyed labels
                if i < len(self.diff_dice_rolls): # Ensure index exists
                     final_roll = self.diff_dice_rolls[i]
                     img = self._get_tk_dice_image(final_roll)
                     if img:
                         lbl.config(image=img, text='')
                         lbl.image = img
                     else: # Fallback text
                         lbl.config(text=f"[{final_roll}]", image='')
                else: # Should not happen if lists match
                     lbl.config(text="ERR", image='')


            # Enable danger die button if window still exists
            print("Difference dice rolling complete.")
            if self.winfo_exists():
                self.roll_danger_button.config(state=tk.NORMAL)
                self.roll_danger_button.focus_set() # Set focus for convenience

    # --- Danger Die rolling ---
    def _start_danger_die_roll(self):
        """Disables button and starts the danger die shuffle animation."""
        if not self.winfo_exists(): return
        self.roll_danger_button.config(state=tk.DISABLED)
        self.shuffle_count = config.DICE_SHUFFLE_STEPS
        print("Rolling danger die (with shuffle)...")
        # Ensure label exists
        if not self.danger_die_label.winfo_exists():
             print("Error: Danger die label destroyed before shuffle.")
             return
        self._shuffle_danger_die()

    def _shuffle_danger_die(self):
        """Displays a random die face for shuffle effect."""
        if not self.winfo_exists(): return
        # Also check if the specific label exists
        if not self.danger_die_label.winfo_exists(): return

        if self.shuffle_count > 0:
            temp_roll = random.randint(1, 6)
            img = self._get_tk_dice_image(temp_roll) # Use helper
            if img:
                self.danger_die_label.config(image=img, text='')
                self.danger_die_label.image = img
            else:
                self.danger_die_label.config(text=f"[{temp_roll}]", image='') # Clear image if fallback

            self.shuffle_count -= 1
            self.after(config.DICE_SHUFFLE_DELAY, self._shuffle_danger_die)
        else:
            # Shuffle complete, roll the actual danger die
            self.danger_die_roll = utils.roll_dice(1)[0]
            print(f"  Final Danger Die: {self.danger_die_roll}")
            img = self._get_tk_dice_image(self.danger_die_roll) # Use helper
             # Check label exists before configuring
            if self.danger_die_label.winfo_exists():
                if img:
                    self.danger_die_label.config(image=img, text='')
                    self.danger_die_label.image = img
                else:
                    self.danger_die_label.config(text=f"[{self.danger_die_roll}]", image='')

            # Proceed to finalize combat after a short pause if window still exists
            if self.winfo_exists():
                self.after(400, self._finalize) # Wait briefly after final die shown

    def _finalize(self):
        """Gathers results and calls the main finalize_combat function via callback."""
        # Check if the window was closed prematurely
        if not self.winfo_exists():
            print("Roll window closed before finalizing.")
            # Optionally call callback with a specific value indicating premature close?
            # self.finalize_callback({"error": "Window closed prematurely"})
            return # Don't proceed if window is gone

        print("Closing roll window, calling finalize callback.")
        # Pass collected rolls back to the main combat logic
        results = {
            "diff_rolls": self.diff_dice_rolls,
            "danger_roll": self.danger_die_roll
        }
        # Try/except block around destroy/callback for extra safety
        try:
            self.destroy() # Close this rolling window first
            self.finalize_callback(results) # Then call the callback
        except tk.TclError as e:
             # This might happen if the parent window was destroyed
             print(f"TclError during finalize (likely window already destroyed): {e}")
        except Exception as e:
             print(f"Unexpected error during finalize: {e}")


# --- MODIFIED: CombatResultsWindow ---
class CombatResultsWindow(tk.Toplevel):
    """Modal window to display combat results, using PIL images."""
    def __init__(self, parent, results_data, pil_dice_images): # Takes PIL images
        super().__init__(parent)
        # Ensure parent exists before proceeding
        if not parent or not parent.winfo_exists():
             print("Error: Parent window for CombatResultsWindow does not exist.")
             # Cannot create the window, maybe raise an error or return early
             # For now, just print and don't finish init
             return
        self.parent = parent # Keep reference if needed

        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.title("Combat Results")
        self.configure(padx=20, pady=20)

        self.pil_dice_images = pil_dice_images # Store PIL dice images
        self.tk_dice_images = {} # Cache Tk images locally

        outcome_text = "YOU WIN!" if results_data["win"] else "YOU LOSE..."
        outcome_color = "dark green" if results_data["win"] else "dark red"
        ttk.Label(self, text=outcome_text, font=("Arial", 16, "bold"), foreground=outcome_color).pack(pady=(0,15))

        details_frame = ttk.LabelFrame(self, text="Details")
        details_frame.pack(fill='x', pady=5)

        # --- Attacker/Defender Info ---
        ttk.Label(details_frame, text=f"Target: {results_data['target']} (Value: {results_data['defender_total']})").pack(anchor='w', padx=5, pady=2)
        used_card_text = f"Used: {results_data['used_card']} (Value: {results_data['attacker_total']})" if results_data['used_card'] else f"Used: None (Value: {results_data['attacker_total']})"
        ttk.Label(details_frame, text=used_card_text).pack(anchor='w', padx=5, pady=2)

        # --- Display Automatic Win/Loss or Dice Info ---
        if results_data.get("automatic_win", False):
             ttk.Label(details_frame, text="Result: Automatic Win (Attacker Value > Defender Value)", foreground="blue").pack(anchor='w', padx=5, pady=2)
        # Add check for automatic loss if you implement that rule
        # elif results_data.get("automatic_loss", False):
        #      ttk.Label(details_frame, text="Result: Automatic Loss (Attacker Value < Defender Value)", foreground="orange red").pack(anchor='w', padx=5, pady=2)
        elif results_data['num_diff_dice'] is not None and results_data['danger_die'] is not None : # Check if dice were involved
            ttk.Label(details_frame, text=f"Difference: {results_data['difference']}").pack(anchor='w', padx=5, pady=2)
            # --- Display Difference Dice Rolls ---
            diff_dice_frame = ttk.Frame(details_frame)
            diff_dice_frame.pack(anchor='w', padx=5, pady=2)
            ttk.Label(diff_dice_frame, text=f"Roll {results_data['num_diff_dice']} dice:").pack(side=tk.LEFT, padx=(0, 5))
            if not results_data['diff_dice_rolls']: # Handle case if 0 dice were rolled (should be covered by auto-win, but safe)
                 ttk.Label(diff_dice_frame, text="N/A").pack(side=tk.LEFT, padx=2)
            else:
                for roll in results_data['diff_dice_rolls']:
                    img = self._get_tk_dice_image(roll) # Use helper
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
            if danger_roll is None: # Handle case if danger die wasn't rolled (shouldn't happen here)
                 ttk.Label(danger_die_frame, text="N/A").pack(side=tk.LEFT, padx=2)
            else:
                img = self._get_tk_dice_image(danger_roll) # Use helper
                if img:
                    lbl = ttk.Label(danger_die_frame, image=img)
                    lbl.image = img # Keep ref
                    lbl.pack(side=tk.LEFT, padx=2)
                else: # Fallback to text
                    ttk.Label(danger_die_frame, text=f"[{danger_roll}]").pack(side=tk.LEFT, padx=2)
        else:
             # Case where combat might have ended abnormally? Or auto-win displayed above.
             ttk.Label(details_frame, text="Result determined without dice roll.").pack(anchor='w', padx=5, pady=2)


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

        # Center the window relative to the parent
        self.update_idletasks() # Ensure window size is calculated
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        win_w = self.winfo_width()
        win_h = self.winfo_height()
        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2
        self.geometry(f"+{x}+{y}") # Position the window

        self.wait_window()

    # --- Helper to get/create Tkinter PhotoImage (similar to CombatRollWindow) ---
    def _get_tk_dice_image(self, value):
        """Gets a Tk dice image, creating it from PIL if not cached."""
        if not self.winfo_exists(): return None # Check if window still exists

        if value not in self.tk_dice_images:
            pil_img = self.pil_dice_images.get(value)
            if pil_img:
                try:
                    # Create with self (the Toplevel window) as master
                    self.tk_dice_images[value] = ImageTk.PhotoImage(pil_img, master=self)
                except Exception as e:
                    print(f"Error creating Tk dice image for {value} in ResultsWindow: {e}")
                    if self.winfo_exists():
                         messagebox.showerror("Image Error", f"Failed to load dice image {value}.\nPlease check asset files.", parent=self)
                    self.tk_dice_images[value] = None # Avoid retrying
            else:
                 print(f"Warning: PIL dice image not found for value {value}")
                 self.tk_dice_images[value] = None
        return self.tk_dice_images.get(value)


# --- END OF FILE combat_ui.py ---