# --- START OF FILE combat/ui_roll.py ---

import tkinter as tk
from tkinter import ttk, messagebox
import random
from PIL import ImageTk, Image # Ensure Image is imported
import config
import utils # For roll_dice
import sys # For exit

class CombatRollWindow(tk.Toplevel):
    """Modal window for interactively rolling combat dice with shuffle animation."""
    def __init__(self, parent, player, target_card, target_row, target_col,
                 selected_value_card_info, game_state, combat_params, finalize_callback):
        # Ensure parent is valid
        if not parent or not parent.winfo_exists():
             # This is a critical error, cannot proceed reasonably
             print("FATAL ERROR: CombatRollWindow created without a valid parent window.")
             messagebox.showerror("Internal Error", "Cannot open combat roll window: Parent window missing.", icon='error')
             # Don't call super().__init__ if parent is invalid
             # Try to call finalize_callback with an error state if possible
             if finalize_callback: finalize_callback(None)
             # Exit or raise might be too drastic, but the window won't work.
             # Returning here prevents further initialization.
             return

        super().__init__(parent)
        self.parent = parent
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.title("Combat Roll")
        self.configure(padx=15, pady=15) # Main window padding

        # Store necessary data
        self.player = player
        self.target_card = target_card
        # self.target_row = target_row # Not strictly needed in UI itself
        # self.target_col = target_col # Not strictly needed in UI itself
        self.selected_value_card_info = selected_value_card_info
        self.game_state = game_state
        self.pil_dice_images = game_state["assets"].get("pil_dice_scaled", {})
        self.tk_dice_images = {} # Cache Tk images for this window instance
        self.attacker_total = combat_params["attacker_total"]
        self.defender_total = combat_params["defender_total"]
        self.difference = combat_params["difference"]
        self.num_diff_dice = combat_params["num_diff_dice"]
        self.finalize_callback = finalize_callback

        # State for rolling / animation
        self.diff_dice_rolls = []   # Stores final results [int]
        self.diff_dice_labels = []  # Stores ttk.Label widgets for difference dice
        self.danger_die_roll = None # Stores final result (int)
        self.danger_die_label = None # Stores ttk.Label widget for danger die
        self.is_shuffling = False   # Flag to prevent multiple animations
        self.animation_frame_count = 0 # Counter for animation steps
        self.die_total_shuffle_steps = [] # Stores how many frames each die shuffles [int]
        self.max_shuffle_steps = 0  # Max frames needed overall for sequential stop

        print(f"[CombatRollWindow Init] PIL Dice Images available: {list(self.pil_dice_images.keys())}")
        if not self.pil_dice_images:
            print("  WARNING: No PIL dice images loaded. UI will use text fallbacks.")
        elif 'icon' not in self.pil_dice_images:
             print("  WARNING: Placeholder icon 'die_icometric_small.png' not loaded. UI will use text fallbacks.")


        # --- UI Elements ---

        # --- 1. Info Frame ---
        info_frame = ttk.LabelFrame(self, text="Combat Details", padding=(10, 5))
        info_frame.pack(fill='x', pady=(0, 10))
        used_card = selected_value_card_info[0] if selected_value_card_info else "None"
        ttk.Label(info_frame, text=f"Attacker: {self.attacker_total} (Card: {used_card})").pack(anchor='w', padx=5, pady=1)
        ttk.Label(info_frame, text=f"Defender: {self.target_card} (Value: {self.defender_total})").pack(anchor='w', padx=5, pady=1)
        # Only show dice roll info if dice are actually needed
        if self.num_diff_dice > 0:
            ttk.Label(info_frame, text=f"Difference: {self.difference} -> Roll {self.num_diff_dice} Difference Dice vs Danger Die").pack(anchor='w', padx=5, pady=1)
        else:
            # This case should only be hit if attacker > defender (auto-win handled before window opens)
            # but adding text for robustness.
             ttk.Label(info_frame, text=f"Difference: {self.difference} -> No dice roll needed.").pack(anchor='w', padx=5, pady=1)


        # --- 2. Determine Dice Size for Layout ---
        # Try to get size from icon or first die image for consistent spacing
        ref_pil_img = self.pil_dice_images.get('icon') or self.pil_dice_images.get(1)
        estimated_dice_h = 60 # Default height
        estimated_dice_w = 60 # Default width
        if ref_pil_img and isinstance(ref_pil_img, Image.Image):
             # Add some padding to the raw image size
             estimated_dice_w = int(ref_pil_img.width * 1.15)
             estimated_dice_h = int(ref_pil_img.height * 1.2)
             print(f"  Estimated dice display size: {estimated_dice_w}x{estimated_dice_h}")
        else:
            print(f"  Using default estimated dice display size: {estimated_dice_w}x{estimated_dice_h}")


        # --- 3. Difference Dice Display Area ---
        diff_outer_frame = ttk.LabelFrame(self, text="Difference Dice", padding=(10, 5))
        # Set height based on estimated size + padding to prevent collapse
        diff_outer_frame.config(height=estimated_dice_h + 10)
        diff_outer_frame.pack(fill='x', pady=5)
        # *** Crucial: Prevent the LabelFrame from shrinking to fit its contents ***
        diff_outer_frame.pack_propagate(False)

        # --- Create an *inner* Frame for packing the actual dice labels ---
        # This inner frame will be centered within the outer LabelFrame
        self.diff_dice_display_frame = ttk.Frame(diff_outer_frame)
        self.diff_dice_display_frame.pack(fill='none', expand=True) # Center the inner frame


        # --- 4. Danger Die Display Area ---
        danger_outer_frame = ttk.LabelFrame(self, text="Danger Die", padding=(10, 5))
        danger_outer_frame.config(height=estimated_dice_h + 10)
        danger_outer_frame.pack(fill='x', pady=5)
        danger_outer_frame.pack_propagate(False)

        # --- Inner Frame for the danger die ---
        self.danger_die_display_frame = ttk.Frame(danger_outer_frame)
        self.danger_die_display_frame.pack(fill='none', expand=True) # Center the inner frame

        # Create the danger die label itself inside the inner frame
        self.danger_die_label = ttk.Label(self.danger_die_display_frame) # Parent is inner frame
        # Set initial image to placeholder icon if available
        icon_img = self._get_tk_dice_image('icon')
        if icon_img:
            self.danger_die_label.config(image=icon_img)
            self.danger_die_label.image = icon_img # Keep reference
        else:
            # Fallback text if icon is missing
            self.danger_die_label.config(text="?", font=("Arial", 24, "bold"), anchor='center')
        self.danger_die_label.pack(expand=True) # Center label within inner frame


        # --- 5. Buttons Frame ---
        button_frame = ttk.Frame(self, padding=(0, 10, 0, 0)) # Add top padding
        button_frame.pack(fill='x')

        # --- Roll Difference Dice Button ---
        # Only create/enable if needed
        self.roll_diff_button = None
        if self.num_diff_dice > 0:
            self.roll_diff_button = ttk.Button(button_frame, text=f"Roll {self.num_diff_dice} Dice", command=self._start_diff_dice_roll)
            self.roll_diff_button.pack(side=tk.LEFT, padx=5, expand=True, fill='x')
        else:
            # If no diff dice needed, add placeholder label in their frame
            ttk.Label(self.diff_dice_display_frame, text="N/A").pack(expand=True)


        # --- Roll Danger Die Button ---
        self.roll_danger_button = ttk.Button(button_frame, text="Roll Danger Die", command=self._start_danger_die_roll, state=tk.DISABLED)
        self.roll_danger_button.pack(side=tk.RIGHT, padx=5, expand=True, fill='x')

        # If no diff dice needed, enable danger die roll immediately
        if self.num_diff_dice <= 0 and self.roll_danger_button:
             self.roll_danger_button.config(state=tk.NORMAL)


        # --- 6. Initial Setup ---
        # Setup placeholder labels for difference dice (if any)
        if self.num_diff_dice > 0:
             self._setup_diff_dice_labels()

        # Center the window
        self.center_window()

        # Automatically start difference dice roll if applicable
        if self.num_diff_dice > 0 and self.roll_diff_button:
             self.after(100, self._start_diff_dice_roll) # Short delay before auto-roll

    # --- Helper Methods ---

    def center_window(self):
        """Centers the window on the parent."""
        if not self.winfo_exists(): return
        self.update_idletasks() # Ensure window size is calculated
        if not self.parent or not self.parent.winfo_exists(): return # No parent to center on

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_w = self.parent.winfo_width()
        parent_h = self.parent.winfo_height()
        win_w = self.winfo_width()
        win_h = self.winfo_height()

        # Calculate position, ensuring it's not off-screen if parent is near edge
        x = max(0, parent_x + (parent_w - win_w) // 2)
        y = max(0, parent_y + (parent_h - win_h) // 2)

        self.geometry(f"+{x}+{y}") # Position the window

    def _get_tk_dice_image(self, value):
        """Gets a Tk dice image, creating it from PIL if not cached."""
        # Check if window still exists (important in callbacks)
        if not self.winfo_exists(): return None

        # Normalize key (e.g., handle integer 1 vs string '1' if needed)
        try: key = int(value)
        except (ValueError, TypeError): key = str(value).lower() # Use lower string for icon etc.

        # print(f"Attempting to get Tk image for key: {key} (Original: {value})") # Debug
        if key in self.tk_dice_images:
            # print(f"  Found cached Tk image for key {key}") # Debug
            return self.tk_dice_images[key]

        # Retrieve PIL image from assets
        pil_img = self.pil_dice_images.get(key)
        # print(f"  PIL image found for key {key}: {'Yes' if pil_img else 'No'}") # Debug

        if pil_img and isinstance(pil_img, Image.Image):
            try:
                # print(f"  Attempting ImageTk.PhotoImage creation for key {key}...") # Debug
                # *** Crucial: Set master=self to prevent garbage collection ***
                tk_image = ImageTk.PhotoImage(pil_img, master=self)
                self.tk_dice_images[key] = tk_image # Cache it
                # print(f"  Successfully created and cached Tk image for key {key}") # Debug
                return tk_image
            except Exception as e:
                print(f"  ERROR creating Tk image for key {key}: {e}")
                # Show error only once per key to avoid spamming
                if key not in self.tk_dice_images: # Check cache before showing error
                    if self.winfo_exists(): # Check window exists before showing messagebox
                        messagebox.showerror("Image Error", f"Failed to load dice image '{key}'.\nError: {e}", parent=self)
                self.tk_dice_images[key] = None # Mark as failed to prevent retry
                return None
        else:
             # PIL image wasn't found or wasn't a valid Image object
             if key in self.pil_dice_images: print(f"  Warning: Asset for key {key} is not a valid PIL Image.")
             # else: print(f"  Warning: PIL image asset not found for key {key}") # Already printed during loading
             self.tk_dice_images[key] = None # Mark as failed
             return None

    def _setup_diff_dice_labels(self):
        """Creates the label widgets for difference dice with placeholder icons."""
        # Clear any existing labels first
        for lbl in self.diff_dice_labels:
             if lbl.winfo_exists(): lbl.destroy()
        self.diff_dice_labels = []

        icon_img = self._get_tk_dice_image('icon') # Get placeholder icon

        for i in range(self.num_diff_dice):
             # Parent is the *inner* frame
             lbl = ttk.Label(self.diff_dice_display_frame)
             if icon_img:
                 lbl.config(image=icon_img)
                 lbl.image = icon_img # Keep reference
             else:
                 # Fallback text if icon missing
                 lbl.config(text="?", font=("Arial", 24, "bold"), anchor='center')
             # Pack labels horizontally within the inner frame
             lbl.pack(side=tk.LEFT, padx=5, pady=0, anchor='center')
             self.diff_dice_labels.append(lbl)

    # --- Animation Logic (Using Sequential Stop) ---

    def _start_diff_dice_roll(self):
        """Disables button and starts the difference dice shuffle animation."""
        if not self.winfo_exists() or self.is_shuffling: return
        if self.num_diff_dice <= 0: return # Should not happen if button exists

        print(f"Starting roll animation for {self.num_diff_dice} difference dice...")
        self.is_shuffling = True
        if self.roll_diff_button: self.roll_diff_button.config(state=tk.DISABLED)
        if self.roll_danger_button: self.roll_danger_button.config(state=tk.DISABLED)

        # Pre-roll the actual results
        self.diff_dice_rolls = utils.roll_dice(self.num_diff_dice)
        print(f"  Pre-rolled results: {self.diff_dice_rolls}")

        # Calculate total shuffle steps for each die (sequential stop)
        self.die_total_shuffle_steps = []
        self.max_shuffle_steps = 0
        for i in range(self.num_diff_dice):
            # Each die shuffles a base amount + an increment for each previous die
            steps = config.DICE_BASE_SHUFFLE_STEPS + (i * config.DICE_INCREMENTAL_SHUFFLE_STEPS)
            self.die_total_shuffle_steps.append(steps)
            self.max_shuffle_steps = max(self.max_shuffle_steps, steps)

        print(f"  Animation steps per die: {self.die_total_shuffle_steps}")
        print(f"  Total animation frames needed: {self.max_shuffle_steps}")

        self.animation_frame_count = 0 # Reset frame counter
        self._animate_diff_dice() # Start the animation loop

    def _animate_diff_dice(self):
        """Animates difference dice, stopping them sequentially."""
        if not self.winfo_exists():
            print("  Animation stopped: Window closed.")
            self.is_shuffling = False
            return

        # Check if animation is complete
        if self.animation_frame_count > self.max_shuffle_steps:
            print("Difference dice rolling animation finished.")
            self.is_shuffling = False
            # Enable danger die button if window still exists
            if self.winfo_exists() and self.roll_danger_button:
                self.roll_danger_button.config(state=tk.NORMAL)
                self.roll_danger_button.focus_set() # Set focus for convenience
            return

        # Update dice that are still shuffling
        animation_still_running = False
        for i, lbl in enumerate(self.diff_dice_labels):
            if not lbl.winfo_exists(): continue # Skip if label was somehow destroyed

            required_steps_for_this_die = self.die_total_shuffle_steps[i]

            if self.animation_frame_count < required_steps_for_this_die:
                # This die is still shuffling
                animation_still_running = True
                temp_roll = random.randint(1, 6)
                img = self._get_tk_dice_image(temp_roll)
                if img:
                    lbl.config(image=img, text='') # Set image, clear text
                    lbl.image = img # Keep ref
                else: # Fallback text if image fails
                    lbl.config(text=f"[{temp_roll}]", image='', font=("Arial", 24, "bold"))

            elif self.animation_frame_count == required_steps_for_this_die:
                # This die stops on this frame - show final result
                final_roll = self.diff_dice_rolls[i]
                print(f"  Die {i+1} stopping at frame {self.animation_frame_count} with result: {final_roll}")
                img = self._get_tk_dice_image(final_roll)
                if img:
                    lbl.config(image=img, text='')
                    lbl.image = img
                else: # Fallback text
                    lbl.config(text=f"[{final_roll}]", image='', font=("Arial", 24, "bold"))
                # Check if this is the last die to stop
                if self.animation_frame_count == self.max_shuffle_steps:
                    animation_still_running = False # Ensure loop terminates

            # Else (self.animation_frame_count > required_steps_for_this_die):
            # This die has already stopped, do nothing.

        # Schedule next frame only if animation is ongoing or hasn't reached max frames yet
        # This handles the case where the last die stops before max_shuffle_steps
        # (e.g., if only one die is rolled)
        if animation_still_running or self.animation_frame_count < self.max_shuffle_steps:
             self.animation_frame_count += 1
             self.after(config.DICE_SHUFFLE_DELAY, self._animate_diff_dice)
        else:
             # This else block might be redundant due to the check at the start, but safe.
             print("Difference dice rolling animation finished (final check).")
             self.is_shuffling = False
             if self.winfo_exists() and self.roll_danger_button:
                 self.roll_danger_button.config(state=tk.NORMAL)
                 self.roll_danger_button.focus_set()


    def _start_danger_die_roll(self):
        """Disables button and starts the danger die shuffle animation."""
        if not self.winfo_exists() or self.is_shuffling: return
        if not self.danger_die_label or not self.danger_die_label.winfo_exists():
             print("Error: Danger die label is missing. Cannot start roll.")
             self._finalize_error("Danger die label missing")
             return

        print("Rolling danger die (with shuffle)...")
        self.is_shuffling = True
        if self.roll_danger_button: self.roll_danger_button.config(state=tk.DISABLED)
        if self.roll_diff_button: self.roll_diff_button.config(state=tk.DISABLED) # Keep disabled

        # Pre-roll the actual result
        self.danger_die_roll = utils.roll_dice(1)[0]
        print(f"  Pre-rolled danger die: {self.danger_die_roll}")

        # Calculate total shuffle steps (use consistent formula)
        self.animation_frame_count = 0 # Reset frame counter
        # Make it shuffle for a decent amount of time, maybe related to last diff die
        self.max_shuffle_steps = config.DICE_BASE_SHUFFLE_STEPS + config.DICE_INCREMENTAL_SHUFFLE_STEPS
        print(f"  Danger die animation frames: {self.max_shuffle_steps}")

        self._animate_danger_die() # Start the animation loop

    def _animate_danger_die(self):
        """Animates the danger die."""
        if not self.winfo_exists():
            print("  Animation stopped: Window closed.")
            self.is_shuffling = False
            return
        if not self.danger_die_label or not self.danger_die_label.winfo_exists():
             print("Error: Danger die label destroyed during animation.")
             self.is_shuffling = False
             self._finalize_error("Danger die label missing")
             return

        # Check if animation is complete
        if self.animation_frame_count > self.max_shuffle_steps:
            print("Danger die animation finished.")
            self.is_shuffling = False
            # Proceed to finalize combat after a short pause if window still exists
            if self.winfo_exists():
                self.after(400, self._finalize) # Wait briefly after final die shown
            return

        # Update shuffling die or show final result
        if self.animation_frame_count < self.max_shuffle_steps:
            # Still shuffling
            temp_roll = random.randint(1, 6)
            img = self._get_tk_dice_image(temp_roll)
            if img:
                self.danger_die_label.config(image=img, text='')
                self.danger_die_label.image = img
            else: # Fallback text
                self.danger_die_label.config(text=f"[{temp_roll}]", image='', font=("Arial", 24, "bold"))
        else:
            # Show final result on the last frame
            print(f"  Danger die stopping at frame {self.animation_frame_count} with result: {self.danger_die_roll}")
            img = self._get_tk_dice_image(self.danger_die_roll)
            if img:
                self.danger_die_label.config(image=img, text='')
                self.danger_die_label.image = img
            else: # Fallback text
                self.danger_die_label.config(text=f"[{self.danger_die_roll}]", image='', font=("Arial", 24, "bold"))

        # Schedule next frame
        self.animation_frame_count += 1
        self.after(config.DICE_SHUFFLE_DELAY, self._animate_danger_die)


    # --- Finalization ---

    def _finalize(self):
        """Gathers results and calls the main finalize_combat function via callback."""
        # Check if the window was closed prematurely
        if not self.winfo_exists():
            print("Roll window closed before finalizing.")
            # Finalize callback should have already been called with None if closed early
            return

        # Ensure results are valid (danger die should have a value now)
        if self.danger_die_roll is None:
            print("Error: Finalizing combat but danger die was not rolled. Aborting.")
            self._finalize_error("Danger die result missing")
            return

        print("Closing roll window, calling finalize callback.")
        results = {
            "diff_rolls": self.diff_dice_rolls,
            "danger_roll": self.danger_die_roll
        }
        # Try/except block around destroy/callback for extra safety
        try:
            # Destroy window *before* calling callback to prevent re-entrancy issues
            self.destroy()
            self.finalize_callback(results) # Then call the callback
        except tk.TclError as e:
             # This might happen if the parent window was destroyed between
             # the winfo_exists check and the destroy/callback calls.
             print(f"TclError during finalize (likely parent window destroyed): {e}")
             # If callback hasn't been called, try calling it with error?
             # self.finalize_callback(None) # Or assume it failed
        except Exception as e:
             print(f"Unexpected error during finalize: {e}")
             # If callback hasn't been called, try calling it with error?
             # self.finalize_callback(None)

    def _finalize_error(self, message):
        """Closes window and calls finalize callback with None to indicate failure."""
        print(f"Finalizing with error: {message}")
        # Ensure callback is called even on error exit
        callback = self.finalize_callback
        try:
            if self.winfo_exists(): self.destroy()
        except tk.TclError as e:
            print(f"TclError during error finalization: {e}")
        except Exception as e:
            print(f"Error during error finalization: {e}")
        # Call callback *after* trying to destroy
        if callback: callback(None)

    # Override destroy to ensure finalize_callback(None) is called if closed early
    # def destroy(self):
    #     print("CombatRollWindow destroy called.")
    #     # If destroyed externally (e.g., closing window) before finalize, signal error
    #     if self.is_shuffling or self.danger_die_roll is None : # Check if combat was unresolved
    #          if self.finalize_callback:
    #              print("  Window destroyed prematurely, calling finalize_callback(None)")
    #              # This logic can be tricky. Avoid calling callback twice.
    #              # Maybe set a flag?
    #              # self.finalize_callback(None)
    #              # self.finalize_callback = None # Prevent double call in _finalize
    #              pass # Let _finalize handle it via winfo_exists checks maybe safer
    #     super().destroy()


# --- END OF FILE combat/ui_roll.py ---