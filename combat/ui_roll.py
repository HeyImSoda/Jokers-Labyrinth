# --- START OF FILE combat/ui_roll.py ---

import tkinter as tk
from tkinter import ttk, messagebox
import random
from PIL import ImageTk, Image # Ensure Image is imported
import config
import utils # For roll_dice
import sys # For exit

# No longer a Toplevel window

class CombatRollView: # Renamed from CombatRollWindow
    """View for interactively rolling combat dice, displayed within a parent frame."""
    def __init__(self, parent_frame, player, target_card,
                 selected_value_card_info, game_state, combat_params, finalize_callback):
        # self.parent = parent # No longer need Toplevel parent
        self.parent_frame = parent_frame # The frame to build UI into (info_frame)

        # Store necessary data (remains the same)
        self.player = player
        self.target_card = target_card
        self.selected_value_card_info = selected_value_card_info
        self.game_state = game_state
        self.pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
        self.tk_dice_images = {} # Cache Tk images for this view instance
        self.attacker_total = combat_params["attacker_total"]
        self.defender_total = combat_params["defender_total"]
        self.difference = combat_params["difference"]
        self.num_diff_dice = combat_params["num_diff_dice"]
        self.finalize_callback = finalize_callback # Called with roll results or None

        # State for rolling / animation (remains the same)
        self.diff_dice_rolls = []
        self.diff_dice_labels = []
        self.danger_die_roll = None
        self.danger_die_label = None
        self.is_shuffling = False
        self.animation_frame_count = 0
        self.die_total_shuffle_steps = []
        self.max_shuffle_steps = 0
        self._after_id_diff = None # Store after ID for cancellation
        self._after_id_danger = None # Store after ID for cancellation

        print(f"[CombatRollView Init] PIL Dice Images available: {list(self.pil_dice_images.keys())}")
        # (Warnings about missing images remain the same)
        if not self.pil_dice_images: print("  WARNING: No PIL dice images loaded.")
        elif 'icon' not in self.pil_dice_images: print("  WARNING: Placeholder icon not loaded.")


        # Create the main frame for this view's content
        self.frame = ttk.Frame(self.parent_frame, padding=(15,15))

        # --- UI Elements packed into self.frame ---

        # --- 1. Info Frame ---
        info_frame_ui = ttk.LabelFrame(self.frame, text="Combat Details", padding=(10, 5))
        info_frame_ui.pack(fill='x', pady=(0, 10))
        used_card = selected_value_card_info[0] if selected_value_card_info else "None"
        ttk.Label(info_frame_ui, text=f"Attacker: {self.attacker_total} (Card: {used_card})").pack(anchor='w', padx=5, pady=1)
        ttk.Label(info_frame_ui, text=f"Defender: {self.target_card} (Value: {self.defender_total})").pack(anchor='w', padx=5, pady=1)
        if self.num_diff_dice > 0:
            ttk.Label(info_frame_ui, text=f"Difference: {self.difference} -> Roll {self.num_diff_dice} Difference Dice vs Danger Die").pack(anchor='w', padx=5, pady=1)
        else:
             ttk.Label(info_frame_ui, text=f"Difference: {self.difference} -> No dice roll needed.").pack(anchor='w', padx=5, pady=1)


        # --- 2. Determine Dice Size for Layout --- (remains the same)
        ref_pil_img = self.pil_dice_images.get('icon') or self.pil_dice_images.get(1)
        estimated_dice_h, estimated_dice_w = 60, 60
        if ref_pil_img and isinstance(ref_pil_img, Image.Image):
             estimated_dice_w = int(ref_pil_img.width * 1.15)
             estimated_dice_h = int(ref_pil_img.height * 1.2)
             print(f"  Estimated dice display size: {estimated_dice_w}x{estimated_dice_h}")


        # --- 3. Difference Dice Display Area --- (Layout remains the same)
        diff_outer_frame = ttk.LabelFrame(self.frame, text="Difference Dice", padding=(10, 5))
        diff_outer_frame.config(height=estimated_dice_h + 35)
        diff_outer_frame.pack(fill='x', pady=5)
        diff_outer_frame.pack_propagate(False)
        self.diff_dice_display_frame = ttk.Frame(diff_outer_frame)
        self.diff_dice_display_frame.pack(fill='none', expand=True)


        # --- 4. Danger Die Display Area --- (Layout remains the same)
        danger_outer_frame = ttk.LabelFrame(self.frame, text="Danger Die", padding=(10, 5))
        danger_outer_frame.config(height=estimated_dice_h + 35)
        danger_outer_frame.pack(fill='x', pady=5)
        danger_outer_frame.pack_propagate(False)
        self.danger_die_display_frame = ttk.Frame(danger_outer_frame)
        self.danger_die_display_frame.pack(fill='none', expand=True)
        self.danger_die_label = ttk.Label(self.danger_die_display_frame)
        icon_img = self._get_tk_dice_image('icon')
        if icon_img:
            self.danger_die_label.config(image=icon_img); self.danger_die_label.image = icon_img
        else:
            self.danger_die_label.config(text="?", font=("Arial", 24, "bold"), anchor='center')
        self.danger_die_label.pack(expand=True)


        # --- 5. Buttons Frame ---
        button_frame = ttk.Frame(self.frame, padding=(0, 10, 0, 0))
        button_frame.pack(fill='x')

        # --- Roll Difference Dice Button ---
        # Now enabled by default if dice > 0, command triggers roll
        self.roll_diff_button = None
        if self.num_diff_dice > 0:
            self.roll_diff_button = ttk.Button(button_frame, text=f"Roll {self.num_diff_dice} Dice",
                                               command=self._start_diff_dice_roll, state=tk.NORMAL) # Start NORMAL
            self.roll_diff_button.pack(side=tk.LEFT, padx=5, expand=True, fill='x')
        else:
            ttk.Label(self.diff_dice_display_frame, text="N/A").pack(expand=True)

        # --- Roll Danger Die Button ---
        # Starts disabled, enabled after diff dice finish
        self.roll_danger_button = ttk.Button(button_frame, text="Roll Danger Die",
                                             command=self._start_danger_die_roll, state=tk.DISABLED)
        self.roll_danger_button.pack(side=tk.RIGHT, padx=5, expand=True, fill='x')


        # --- 6. Initial Setup ---
        if self.num_diff_dice > 0:
             self._setup_diff_dice_labels() # Setup placeholders

        # --- Removed centering logic (handled by parent frame) ---
        # --- Removed automatic roll trigger ---

    # --- Methods ---

    def display(self):
        """Packs the view's frame into the parent frame."""
        self.frame.pack(fill='x', pady=20) # Example packing

    def destroy_view(self):
        """Destroys the view's main frame and cancels pending animations."""
        print("Destroying CombatRollView")
        # Cancel any pending 'after' calls
        if self._after_id_diff:
            self.frame.after_cancel(self._after_id_diff)
            self._after_id_diff = None
        if self._after_id_danger:
            self.frame.after_cancel(self._after_id_danger)
            self._after_id_danger = None

        if self.frame and self.frame.winfo_exists():
            self.frame.destroy()
        self.is_shuffling = False # Ensure shuffling stops

    # --- _get_tk_dice_image (remains the same, uses self.frame as master) ---
    def _get_tk_dice_image(self, value):
        if not self.frame or not self.frame.winfo_exists(): return None # Check frame existence
        try: key = int(value)
        except (ValueError, TypeError): key = str(value).lower()
        if key in self.tk_dice_images: return self.tk_dice_images[key]
        pil_img = self.pil_dice_images.get(key)
        if pil_img and isinstance(pil_img, Image.Image):
            try:
                tk_image = ImageTk.PhotoImage(pil_img, master=self.frame) # MASTER is self.frame
                self.tk_dice_images[key] = tk_image
                return tk_image
            except Exception as e:
                print(f"  ERROR creating Tk image for key {key}: {e}")
                if key not in self.tk_dice_images:
                     if self.frame.winfo_exists(): # Check frame before showing error
                        messagebox.showerror("Image Error", f"Failed to load dice image '{key}'.\nError: {e}", parent=self.frame) # Parent is frame
                self.tk_dice_images[key] = None; return None
        else:
             self.tk_dice_images[key] = None; return None


    # --- _setup_diff_dice_labels (remains the same) ---
    def _setup_diff_dice_labels(self):
        for lbl in self.diff_dice_labels:
             if lbl.winfo_exists(): lbl.destroy()
        self.diff_dice_labels = []
        icon_img = self._get_tk_dice_image('icon')
        for i in range(self.num_diff_dice):
             lbl = ttk.Label(self.diff_dice_display_frame)
             if icon_img:
                 lbl.config(image=icon_img); lbl.image = icon_img
             else:
                 lbl.config(text="?", font=("Arial", 24, "bold"), anchor='center')
             lbl.pack(side=tk.LEFT, padx=5, pady=0, anchor='center')
             self.diff_dice_labels.append(lbl)

    # --- Animation Logic (remains mostly the same, but uses self.frame.after) ---

    def _start_diff_dice_roll(self):
        """ Triggered by button press. Starts difference dice shuffle."""
        # Added check for is_shuffling
        if not self.frame.winfo_exists() or self.is_shuffling: return
        if self.num_diff_dice <= 0: return

        print(f"Starting roll animation for {self.num_diff_dice} difference dice...")
        self.is_shuffling = True
        # --- Disable BOTH buttons during animation ---
        if self.roll_diff_button: self.roll_diff_button.config(state=tk.DISABLED)
        if self.roll_danger_button: self.roll_danger_button.config(state=tk.DISABLED)
        # ---------------------------------------------

        self.diff_dice_rolls = utils.roll_dice(self.num_diff_dice)
        print(f"  Pre-rolled results: {self.diff_dice_rolls}")

        self.die_total_shuffle_steps = []
        self.max_shuffle_steps = 0
        for i in range(self.num_diff_dice):
            steps = config.DICE_BASE_SHUFFLE_STEPS + (i * config.DICE_INCREMENTAL_SHUFFLE_STEPS)
            self.die_total_shuffle_steps.append(steps)
            self.max_shuffle_steps = max(self.max_shuffle_steps, steps)

        print(f"  Animation steps per die: {self.die_total_shuffle_steps}")
        print(f"  Total animation frames needed: {self.max_shuffle_steps}")

        self.animation_frame_count = 0
        self._animate_diff_dice() # Start the animation loop

    def _animate_diff_dice(self):
        """Animates difference dice, stopping them sequentially."""
        if not self.frame.winfo_exists():
            print("  Animation stopped: View destroyed.")
            self.is_shuffling = False; self._after_id_diff = None; return

        # (Animation update logic remains the same as before)
        if self.animation_frame_count <= self.max_shuffle_steps:
            animation_still_running = False
            for i, lbl in enumerate(self.diff_dice_labels):
                if not lbl.winfo_exists(): continue
                required_steps = self.die_total_shuffle_steps[i]
                if self.animation_frame_count < required_steps:
                    animation_still_running = True
                    temp_roll = random.randint(1, 6); img = self._get_tk_dice_image(temp_roll)
                    if img: lbl.config(image=img, text=''); lbl.image = img
                    else: lbl.config(text=f"[{temp_roll}]", image='', font=("Arial", 24, "bold"))
                elif self.animation_frame_count == required_steps:
                     final_roll = self.diff_dice_rolls[i]; print(f"  Die {i+1} stopping: {final_roll}")
                     img = self._get_tk_dice_image(final_roll)
                     if img: lbl.config(image=img, text=''); lbl.image = img
                     else: lbl.config(text=f"[{final_roll}]", image='', font=("Arial", 24, "bold"))
                     if self.animation_frame_count == self.max_shuffle_steps: animation_still_running = False
            # Schedule next frame using self.frame.after
            if animation_still_running or self.animation_frame_count < self.max_shuffle_steps:
                 self.animation_frame_count += 1
                 self._after_id_diff = self.frame.after(config.DICE_SHUFFLE_DELAY, self._animate_diff_dice) # Use self.frame
            else: # Animation finished
                self._after_id_diff = None
                print("Difference dice rolling animation finished.")
                self.is_shuffling = False # Mark shuffling as done *before* enabling button
                # Enable danger die button
                if self.frame.winfo_exists() and self.roll_danger_button:
                    self.roll_danger_button.config(state=tk.NORMAL)
                    self.roll_danger_button.focus_set()
        else: # Should not happen if logic above is correct, but safety catch
             self._after_id_diff = None
             print("Difference dice animation finished (final check).")
             self.is_shuffling = False
             if self.frame.winfo_exists() and self.roll_danger_button:
                 self.roll_danger_button.config(state=tk.NORMAL); self.roll_danger_button.focus_set()


    def _start_danger_die_roll(self):
        """ Triggered by button press. Starts the danger die shuffle animation."""
        # Added check for is_shuffling
        if not self.frame.winfo_exists() or self.is_shuffling: return
        if not self.danger_die_label or not self.danger_die_label.winfo_exists():
             print("Error: Danger die label missing."); self._finalize_error("Danger die label missing"); return

        print("Rolling danger die (with shuffle)...")
        self.is_shuffling = True
        # --- Disable Danger button during animation ---
        if self.roll_danger_button: self.roll_danger_button.config(state=tk.DISABLED)
        # Keep diff button disabled if it exists
        if self.roll_diff_button: self.roll_diff_button.config(state=tk.DISABLED)
        # ---------------------------------------------

        self.danger_die_roll = utils.roll_dice(1)[0]
        print(f"  Pre-rolled danger die: {self.danger_die_roll}")

        self.animation_frame_count = 0
        self.max_shuffle_steps = config.DICE_BASE_SHUFFLE_STEPS + config.DICE_INCREMENTAL_SHUFFLE_STEPS
        print(f"  Danger die animation frames: {self.max_shuffle_steps}")

        self._animate_danger_die() # Start the animation loop

    def _animate_danger_die(self):
        """Animates the danger die."""
        if not self.frame.winfo_exists():
            print("  Animation stopped: View destroyed.")
            self.is_shuffling = False; self._after_id_danger = None; return
        if not self.danger_die_label or not self.danger_die_label.winfo_exists():
             print("Error: Danger die label destroyed."); self.is_shuffling = False; self._after_id_danger = None; self._finalize_error("Danger die label missing"); return

        # (Animation update logic remains the same)
        if self.animation_frame_count <= self.max_shuffle_steps:
            if self.animation_frame_count < self.max_shuffle_steps:
                temp_roll = random.randint(1, 6); img = self._get_tk_dice_image(temp_roll)
                if img: self.danger_die_label.config(image=img, text=''); self.danger_die_label.image = img
                else: self.danger_die_label.config(text=f"[{temp_roll}]", image='', font=("Arial", 24, "bold"))
            else: # Last frame, show result
                print(f"  Danger die stopping: {self.danger_die_roll}")
                img = self._get_tk_dice_image(self.danger_die_roll)
                if img: self.danger_die_label.config(image=img, text=''); self.danger_die_label.image = img
                else: self.danger_die_label.config(text=f"[{self.danger_die_roll}]", image='', font=("Arial", 24, "bold"))

            # Schedule next frame using self.frame.after
            self.animation_frame_count += 1
            self._after_id_danger = self.frame.after(config.DICE_SHUFFLE_DELAY, self._animate_danger_die) # Use self.frame
        else: # Animation finished
             self._after_id_danger = None
             print("Danger die animation finished.")
             self.is_shuffling = False
             # Proceed to finalize combat after a short pause
             if self.frame.winfo_exists():
                 # Use self.frame.after to schedule the finalize call
                 self.frame.after(400, self._finalize)

    # --- Finalization ---

    def _finalize(self):
        """Gathers results and calls the finalize_callback passed during init."""
        if not self.frame.winfo_exists():
            print("Roll view destroyed before finalizing.")
            # Don't call callback again if already destroyed
            return

        if self.danger_die_roll is None:
            print("Error: Finalizing but danger die was not rolled.")
            self._finalize_error("Danger die result missing")
            return

        print("Finalizing CombatRollView, calling finalize callback.")
        results = { "diff_rolls": self.diff_dice_rolls, "danger_roll": self.danger_die_roll }

        # Call the callback provided by the manager
        if self.finalize_callback:
            try:
                self.finalize_callback(results)
            except Exception as e:
                 print(f"Error executing finalize_callback: {e}")
        # No need to destroy self here, the manager will handle it


    def _finalize_error(self, message):
        """Calls finalize callback with None to indicate failure."""
        print(f"Finalizing CombatRollView with error: {message}")
        if self.finalize_callback:
            try:
                self.finalize_callback(None) # Signal error to manager
            except Exception as e:
                 print(f"Error executing finalize_callback during error handling: {e}")
        # Let the manager handle destroying the view


# --- END OF FILE combat/ui_roll.py ---