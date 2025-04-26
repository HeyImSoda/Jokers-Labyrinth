# --- START OF FILE combat/ui_results.py ---

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk, Image # Ensure Image is imported

# Needs access to config? Maybe not directly.

class CombatResultsWindow(tk.Toplevel):
    """Modal window to display combat results, using PIL images."""
    def __init__(self, parent, results_data, pil_dice_images):
        # Ensure parent exists before proceeding
        if not parent or not parent.winfo_exists():
             print("Error: Parent window for CombatResultsWindow does not exist.")
             # Best effort: create without transient/grab, but might behave oddly
             super().__init__()
             self.parent = None # Explicitly set parent to None
             # return # Or raise error? For now, proceed but without guarantees
        else:
             super().__init__(parent)
             self.parent = parent
             self.transient(parent)
             self.grab_set()

        self.resizable(False, False)
        self.title("Combat Results")
        self.configure(padx=20, pady=20)

        self.pil_dice_images = pil_dice_images if pil_dice_images else {} # Ensure it's a dict
        self.tk_dice_images = {} # Cache Tk images locally

        # --- 1. Outcome Header ---
        outcome_text = "YOU WIN!" if results_data["win"] else "YOU LOSE..."
        outcome_color = "dark green" if results_data["win"] else "dark red"
        ttk.Label(self, text=outcome_text, font=("Arial", 16, "bold"), foreground=outcome_color).pack(pady=(0,15))

        # --- 2. Details Frame ---
        details_frame = ttk.LabelFrame(self, text="Details", padding=(10, 5))
        details_frame.pack(fill='x', pady=5)

        # Attacker/Defender Info
        ttk.Label(details_frame, text=f"Target: {results_data['target']} (Value: {results_data['defender_total']})").pack(anchor='w', padx=5, pady=2)
        used_card_text = f"Used: {results_data['used_card']} (Value: {results_data['attacker_total']})" if results_data['used_card'] else f"Used: None (Value: {results_data['attacker_total']})"
        ttk.Label(details_frame, text=used_card_text).pack(anchor='w', padx=5, pady=2)

        # Display Automatic Win/Loss or Dice Info
        if results_data.get("automatic_win", False):
             ttk.Label(details_frame, text="Result: Automatic Win (Attacker Value > Defender Value)", foreground="blue").pack(anchor='w', padx=5, pady=2)
        # Check if dice were involved (num_diff_dice might be 0 but danger die rolled if attacker <= defender)
        elif results_data['num_diff_dice'] is not None and results_data['danger_die'] is not None :
            ttk.Label(details_frame, text=f"Difference: {results_data['difference']}").pack(anchor='w', padx=5, pady=2)

            # Display Difference Dice Rolls
            diff_dice_frame = ttk.Frame(details_frame)
            diff_dice_frame.pack(anchor='w', padx=5, pady=2)
            ttk.Label(diff_dice_frame, text=f"Difference Dice ({results_data['num_diff_dice']}):").pack(side=tk.LEFT, padx=(0, 5))
            if not results_data['diff_dice_rolls']:
                 # Handle case if 0 dice were rolled (e.g., diff 0 or 1 needs 2 dice, but maybe future rule changes)
                 ttk.Label(diff_dice_frame, text="N/A").pack(side=tk.LEFT, padx=2)
            else:
                for roll in results_data['diff_dice_rolls']:
                    img = self._get_tk_dice_image(roll) # Use helper
                    if img:
                        lbl = ttk.Label(diff_dice_frame, image=img)
                        lbl.image = img # Keep ref
                        lbl.pack(side=tk.LEFT, padx=2)
                    else: # Fallback to text if image missing
                        ttk.Label(diff_dice_frame, text=f"[{roll}]", font=("Arial", 12)).pack(side=tk.LEFT, padx=2)

            # Display Danger Die Roll
            danger_die_frame = ttk.Frame(details_frame)
            danger_die_frame.pack(anchor='w', padx=5, pady=2)
            ttk.Label(danger_die_frame, text="Danger Die:").pack(side=tk.LEFT, padx=(0, 5))
            danger_roll = results_data['danger_die']
            img = self._get_tk_dice_image(danger_roll) # Use helper
            if img:
                lbl = ttk.Label(danger_die_frame, image=img)
                lbl.image = img # Keep ref
                lbl.pack(side=tk.LEFT, padx=2)
            else: # Fallback to text
                 # Danger roll should always exist if we reached this point, but check anyway
                 roll_text = f"[{danger_roll}]" if danger_roll is not None else "N/A"
                 ttk.Label(danger_die_frame, text=roll_text, font=("Arial", 12)).pack(side=tk.LEFT, padx=2)
        else:
             # Case where combat ended abnormally or without dice (e.g., player cancelled?)
             # Auto-win case is handled above.
             ttk.Label(details_frame, text="Result determined without dice roll.").pack(anchor='w', padx=5, pady=2)


        # --- 3. Consequences Frame ---
        consequences_frame = ttk.LabelFrame(self, text="Consequences", padding=(10, 5))
        consequences_frame.pack(fill='x', pady=10)
        if not results_data.get("consequences"): # Use .get for safety
             ttk.Label(consequences_frame, text="- None").pack(anchor='w', padx=5, pady=2)
        else:
            # Use a Text widget for potentially long consequences? Or just labels. Labels are simpler.
            for line in results_data["consequences"]:
                ttk.Label(consequences_frame, text=f"- {line}", wraplength=350).pack(anchor='w', padx=5, pady=1) # Add wraplength


        # --- 4. OK Button ---
        ok_button = ttk.Button(self, text="OK", command=self.destroy)
        ok_button.pack(pady=(15, 0))
        ok_button.focus_set() # Set focus to OK button

        # Center the window relative to the parent (if parent exists)
        self.center_window()

        # Make window modal
        self.wait_window()

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
        x = max(0, parent_x + (parent_w - win_w) // 2)
        y = max(0, parent_y + (parent_h - win_h) // 2)
        self.geometry(f"+{x}+{y}")

    def _get_tk_dice_image(self, value):
        """Gets a Tk dice image, creating it from PIL if not cached."""
        # Check if window still exists (important in callbacks)
        if not self.winfo_exists(): return None

        # Normalize key
        try: key = int(value)
        except (ValueError, TypeError): key = str(value).lower()

        if key in self.tk_dice_images:
            return self.tk_dice_images[key]

        pil_img = self.pil_dice_images.get(key)

        if pil_img and isinstance(pil_img, Image.Image):
            try:
                # Set master=self
                tk_image = ImageTk.PhotoImage(pil_img, master=self)
                self.tk_dice_images[key] = tk_image
                return tk_image
            except Exception as e:
                print(f"Error creating Tk dice image for {key} in ResultsWindow: {e}")
                # Show error only once per key
                if key not in self.tk_dice_images:
                    if self.winfo_exists():
                         messagebox.showerror("Image Error", f"Failed to load dice image {key}.\nError: {e}", parent=self)
                self.tk_dice_images[key] = None
                return None
        else:
             self.tk_dice_images[key] = None
             return None

# --- END OF FILE combat/ui_results.py ---