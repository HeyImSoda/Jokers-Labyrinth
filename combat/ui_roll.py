# --- START OF FILE combat/ui_roll.py ---

import tkinter as tk
from tkinter import ttk, messagebox
import random
from PIL import ImageTk, Image # <-- Import Image just in case needed for type checks etc.
import config
import utils

class CombatRollWindow(tk.Toplevel):
    """Modal window for interactively rolling combat dice with shuffle animation."""
    def __init__(self, parent, player, target_card, target_row, target_col,
                 selected_value_card_info, game_state, combat_params, finalize_callback):
        # (Initialization checks and setup remain the same...)
        super().__init__(parent)
        if not parent or not parent.winfo_exists():
             raise RuntimeError("Cannot create CombatRollWindow without a valid parent.")
        self.parent = parent
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.title("Combat Roll")
        self.configure(padx=20, pady=20)

        self.player = player
        self.target_card = target_card
        # ... (rest of attribute assignments) ...
        self.selected_value_card_info = selected_value_card_info
        self.game_state = game_state
        self.pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
        self.tk_dice_images = {}
        self.attacker_total = combat_params["attacker_total"]
        self.defender_total = combat_params["defender_total"]
        self.difference = combat_params["difference"]
        self.num_diff_dice = combat_params["num_diff_dice"]
        self.finalize_callback = finalize_callback

        # --- State for rolling ---
        self.diff_dice_rolls = []
        self.diff_dice_labels = []
        self.danger_die_roll = None
        self.is_shuffling = False
        self.animation_frame_count = 0
        self.die_total_shuffle_steps = []
        self.max_shuffle_steps = 0

        # --- DEBUG: Print available PIL dice keys ---
        print(f"[CombatRollWindow Init] PIL Dice Images available: {list(self.pil_dice_images.keys())}")
        # ---

        # --- UI Elements ---
        info_frame = ttk.LabelFrame(self, text="Combat Details")
        info_frame.pack(fill='x', pady=(0, 10))
        # (Info labels remain the same...)
        used_card = selected_value_card_info[0] if selected_value_card_info else "None"
        ttk.Label(info_frame, text=f"Attacker: {self.attacker_total} (Card: {used_card})").pack(anchor='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Defender: {self.target_card} (Value: {self.defender_total})").pack(anchor='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Difference: {self.difference} -> Roll {self.num_diff_dice} dice").pack(anchor='w', padx=5, pady=2)


        # --- Frames for Dice (Consistent Sizing) ---
        estimated_dice_h = 60
        estimated_dice_w = 60
        if self.pil_dice_images:
             first_pil_img = next(iter(self.pil_dice_images.values()), None)
             if first_pil_img and isinstance(first_pil_img, Image.Image): # Check type
                 estimated_dice_w = int(first_pil_img.width * 1.15) # Slightly more padding
                 estimated_dice_h = int(first_pil_img.height * 1.15)

        self.diff_dice_display_frame = ttk.LabelFrame(self, text="Difference Dice")
        self.diff_dice_display_frame.pack(fill='x', pady=5)
        # Calculate width based on number of dice + padding
        frame_width = max(estimated_dice_w, (estimated_dice_w + 10) * self.num_diff_dice) if self.num_diff_dice > 0 else estimated_dice_w
        self.diff_dice_display_frame.config(height=estimated_dice_h, width=frame_width)
        self.diff_dice_display_frame.pack_propagate(False)

        self.danger_die_display_frame = ttk.LabelFrame(self, text="Danger Die")
        self.danger_die_display_frame.pack(fill='x', pady=5)
        self.danger_die_display_frame.config(height=estimated_dice_h, width=estimated_dice_w)
        self.danger_die_display_frame.pack_propagate(False)
        # Use image for placeholder if possible, else text
        placeholder_img = self._get_tk_dice_image('?') # Try loading a dummy key or known key? Or just text.
        self.danger_die_label = ttk.Label(self.danger_die_display_frame)
        if placeholder_img: self.danger_die_label.config(image=placeholder_img)
        else: self.danger_die_label.config(text="?", font=("Arial", 18, "bold"))
        self.danger_die_label.pack(expand=True)


        # --- Buttons Frame ---
        # (Button setup remains the same...)
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=(15, 0))
        self.roll_diff_button = ttk.Button(button_frame, text=f"Roll {self.num_diff_dice} Dice", command=self._start_diff_dice_roll)
        self.roll_diff_button.pack(side=tk.LEFT, padx=5, expand=True)
        if self.num_diff_dice <= 0:
            self.roll_diff_button.config(state=tk.DISABLED)
            if self.attacker_total > self.defender_total: reason = "N/A (Value > Defender)"
            else: reason = "N/A"
            ttk.Label(self.diff_dice_display_frame, text=reason).pack(expand=True)
        self.roll_danger_button = ttk.Button(button_frame, text="Roll Danger Die", command=self._start_danger_die_roll, state=tk.DISABLED)
        self.roll_danger_button.pack(side=tk.RIGHT, padx=5, expand=True)


        # Setup initial placeholder labels for difference dice
        if self.num_diff_dice > 0:
             self._setup_diff_dice_labels() # Ensure placeholders are set

        # (Centering logic remains the same...)
        self.update_idletasks()
        # ... geometry calculation ...
        parent_x=self.parent.winfo_rootx(); parent_y=self.parent.winfo_rooty()
        parent_w=self.parent.winfo_width(); parent_h=self.parent.winfo_height()
        win_w=self.winfo_width(); win_h=self.winfo_height()
        x=parent_x+(parent_w-win_w)//2; y=parent_y+(parent_h-win_h)//2
        self.geometry(f"+{x}+{y}")


    def _get_tk_dice_image(self, value):
        """Gets a Tk dice image, creating it from PIL if not cached. Includes enhanced debugging."""
        if not self.winfo_exists(): return None
        # Ensure value is an integer if it's meant to be a dice roll
        try: key = int(value)
        except (ValueError, TypeError): key = value # Allow non-int keys like '?' if needed

        print(f"Attempting to get Tk image for key: {key} (Original: {value})") # DEBUG

        # Check cache first
        if key in self.tk_dice_images:
            # print(f"  Found in cache for key: {key}") # DEBUG (Optional)
            return self.tk_dice_images[key]

        # Not in cache, try to create it
        pil_img = self.pil_dice_images.get(key) # Use the key (likely integer)
        print(f"  PIL image found for key {key}: {'Yes' if pil_img else 'No'}") # DEBUG

        if pil_img and isinstance(pil_img, Image.Image): # Check it's a valid PIL Image
            try:
                print(f"  Attempting ImageTk.PhotoImage creation for key {key}...") # DEBUG
                tk_image = ImageTk.PhotoImage(pil_img, master=self)
                self.tk_dice_images[key] = tk_image # Add to cache
                print(f"  Successfully created and cached Tk image for key {key}") # DEBUG
                return tk_image
            except Exception as e:
                print(f"  ERROR creating Tk image for key {key}: {e}") # DEBUG
                if self.winfo_exists():
                    messagebox.showerror("Image Error", f"Failed to load dice image {key}.\nPlease check asset files.\nError: {e}", parent=self)
                self.tk_dice_images[key] = None # Cache failure to avoid retrying
                return None
        else:
            # PIL image not found or not a valid Image object
             if key in self.pil_dice_images: # Check if key exists but value is wrong type
                 print(f"  Warning: Value for key {key} in pil_dice_images is not a PIL Image.") # DEBUG
             self.tk_dice_images[key] = None # Cache failure
             return None

    def _setup_diff_dice_labels(self):
        """Creates the label widgets for difference dice with placeholders."""
        for lbl in self.diff_dice_labels:
             if lbl.winfo_exists(): lbl.destroy()
        self.diff_dice_labels = []

        placeholder_img = self._get_tk_dice_image(1) # Try loading '1' as placeholder?
        for i in range(self.num_diff_dice):
             lbl = ttk.Label(self.diff_dice_display_frame)
             # --- Use image placeholder if possible, else text ---
             if placeholder_img:
                 lbl.config(image=placeholder_img)
                 lbl.image = placeholder_img # Keep ref even for placeholder
             else:
                 lbl.config(text="?", font=("Arial", 18, "bold"))
             # ----------------------------------------------------
             lbl.pack(side=tk.LEFT, padx=5, pady=5, expand=True)
             self.diff_dice_labels.append(lbl)

    # --- _start_diff_dice_roll (logic remains the same) ---
    def _start_diff_dice_roll(self):
        if not self.winfo_exists() or self.is_shuffling: return
        if self.num_diff_dice <= 0: return
        print(f"Starting roll for {self.num_diff_dice} difference dice...")
        self.is_shuffling = True
        self.roll_diff_button.config(state=tk.DISABLED)
        self.roll_danger_button.config(state=tk.DISABLED)
        self.diff_dice_rolls = utils.roll_dice(self.num_diff_dice)
        print(f"  Pre-rolled results: {self.diff_dice_rolls}")
        self.die_total_shuffle_steps = []
        self.max_shuffle_steps = 0
        for i in range(self.num_diff_dice):
            steps = config.DICE_BASE_SHUFFLE_STEPS + (i * config.DICE_INCREMENTAL_SHUFFLE_STEPS)
            self.die_total_shuffle_steps.append(steps)
            self.max_shuffle_steps = max(self.max_shuffle_steps, steps)
        print(f"  Animation steps per die: {self.die_total_shuffle_steps}")
        print(f"  Total animation frames: {self.max_shuffle_steps}")
        self.animation_frame_count = 0
        self._animate_diff_dice()

    # --- _animate_diff_dice (Ensure correct image setting) ---
    def _animate_diff_dice(self):
        if not self.winfo_exists():
             self.is_shuffling = False; return

        if self.animation_frame_count <= self.max_shuffle_steps: # Use <= to ensure final frame shown
            animation_in_progress = False # Flag to check if any die is still shuffling
            for i, lbl in enumerate(self.diff_dice_labels):
                if not lbl.winfo_exists(): continue
                required_steps = self.die_total_shuffle_steps[i]

                if self.animation_frame_count < required_steps:
                    # Still shuffling this die
                    animation_in_progress = True
                    temp_roll = random.randint(1, 6)
                    img = self._get_tk_dice_image(temp_roll)
                    if img:
                        lbl.config(image=img, text='') # SET IMAGE, CLEAR TEXT
                        lbl.image = img # KEEP REF
                    else:
                        lbl.config(text=f"[{temp_roll}]", image='') # Fallback text
                elif self.animation_frame_count == required_steps:
                     # This is the frame where the die should show its final result
                     final_roll = self.diff_dice_rolls[i]
                     print(f"  Displaying final roll {final_roll} for die {i+1}") # DEBUG
                     img = self._get_tk_dice_image(final_roll)
                     if img:
                        lbl.config(image=img, text='') # SET IMAGE, CLEAR TEXT
                        lbl.image = img # KEEP REF
                     else:
                        lbl.config(text=f"[{final_roll}]", image='') # Fallback text
                # Else: die has already stopped, do nothing to its label

            # Schedule next frame only if animation is still in progress
            if animation_in_progress or self.animation_frame_count < self.max_shuffle_steps:
                self.animation_frame_count += 1
                self.after(config.DICE_SHUFFLE_DELAY, self._animate_diff_dice)
            else:
                # Animation truly complete
                print("Difference dice rolling animation finished.")
                self.is_shuffling = False
                if self.winfo_exists():
                    self.roll_danger_button.config(state=tk.NORMAL)
                    self.roll_danger_button.focus_set()
        # (Removed the 'else' block that was here, handled by animation_in_progress check)


    # --- _start_danger_die_roll (logic remains the same) ---
    def _start_danger_die_roll(self):
        if not self.winfo_exists() or self.is_shuffling: return
        print("Rolling danger die (with shuffle)...")
        self.is_shuffling = True
        self.roll_danger_button.config(state=tk.DISABLED)
        self.roll_diff_button.config(state=tk.DISABLED)
        self.danger_die_roll = utils.roll_dice(1)[0]
        print(f"  Pre-rolled danger die: {self.danger_die_roll}")
        self.animation_frame_count = 0
        self.max_shuffle_steps = config.DICE_BASE_SHUFFLE_STEPS + config.DICE_INCREMENTAL_SHUFFLE_STEPS
        if not self.danger_die_label.winfo_exists():
             print("Error: Danger die label destroyed before shuffle.")
             self.is_shuffling = False
             self._finalize_error("Danger die label missing")
             return
        self._animate_danger_die()

    # --- _animate_danger_die (Ensure correct image setting) ---
    def _animate_danger_die(self):
        if not self.winfo_exists():
            self.is_shuffling = False; return

        # Check label exists at start of frame
        if not self.danger_die_label.winfo_exists():
             print("Error: Danger die label destroyed during animation.")
             self.is_shuffling = False
             self._finalize_error("Danger die label missing")
             return

        if self.animation_frame_count <= self.max_shuffle_steps: # Use <=
            if self.animation_frame_count < self.max_shuffle_steps:
                # Still shuffling
                temp_roll = random.randint(1, 6)
                img = self._get_tk_dice_image(temp_roll)
                if img:
                    self.danger_die_label.config(image=img, text='') # SET IMAGE, CLEAR TEXT
                    self.danger_die_label.image = img
                else:
                    self.danger_die_label.config(text=f"[{temp_roll}]", image='')
            else: # self.animation_frame_count == self.max_shuffle_steps
                # Show final result
                print(f"  Displaying final danger die: {self.danger_die_roll}") # DEBUG
                img = self._get_tk_dice_image(self.danger_die_roll)
                if img:
                    self.danger_die_label.config(image=img, text='') # SET IMAGE, CLEAR TEXT
                    self.danger_die_label.image = img
                else:
                    self.danger_die_label.config(text=f"[{self.danger_die_roll}]", image='')

            self.animation_frame_count += 1
            self.after(config.DICE_SHUFFLE_DELAY, self._animate_danger_die)
        else:
            # Danger die animation complete
            print("Danger die animation finished.")
            self.is_shuffling = False
            if self.winfo_exists():
                self.after(400, self._finalize) # Proceed to finalize

    # (_finalize and _finalize_error remain the same)
    def _finalize(self):
        if not self.winfo_exists():
            print("Roll window closed before finalizing.")
            return
        print("Closing roll window, calling finalize callback.")
        results = {"diff_rolls": self.diff_dice_rolls, "danger_roll": self.danger_die_roll}
        try:
            self.destroy()
            self.finalize_callback(results)
        except tk.TclError as e: print(f"TclError finalizing: {e}")
        except Exception as e: print(f"Error finalizing: {e}")

    def _finalize_error(self, message):
        print(f"Finalizing with error: {message}")
        if self.winfo_exists(): self.destroy()
        self.finalize_callback(None) # Indicate error


# --- END OF FILE combat/ui_roll.py ---