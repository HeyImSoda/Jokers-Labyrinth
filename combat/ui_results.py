# --- START OF FILE combat/ui_results.py ---

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk

# Needs access to config? Maybe not directly.

class CombatResultsWindow(tk.Toplevel):
    """Modal window to display combat results, using PIL images."""
    def __init__(self, parent, results_data, pil_dice_images):
        # Ensure parent exists before proceeding
        if not parent or not parent.winfo_exists():
             print("Error: Parent window for CombatResultsWindow does not exist.")
             # Best effort: create without transient/grab, but might behave oddly
             super().__init__()
             # return # Or raise error? For now, proceed but without guarantees
        else:
             super().__init__(parent)
             self.parent = parent
             self.transient(parent)
             self.grab_set()

        self.resizable(False, False)
        self.title("Combat Results")
        self.configure(padx=20, pady=20)

        self.pil_dice_images = pil_dice_images
        self.tk_dice_images = {}

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
        elif results_data['num_diff_dice'] is not None and results_data['danger_die'] is not None :
            ttk.Label(details_frame, text=f"Difference: {results_data['difference']}").pack(anchor='w', padx=5, pady=2)
            # --- Display Difference Dice Rolls ---
            diff_dice_frame = ttk.Frame(details_frame)
            diff_dice_frame.pack(anchor='w', padx=5, pady=2)
            ttk.Label(diff_dice_frame, text=f"Roll {results_data['num_diff_dice']} dice:").pack(side=tk.LEFT, padx=(0, 5))
            if not results_data['diff_dice_rolls']:
                 ttk.Label(diff_dice_frame, text="N/A").pack(side=tk.LEFT, padx=2)
            else:
                for roll in results_data['diff_dice_rolls']:
                    img = self._get_tk_dice_image(roll)
                    if img:
                        lbl = ttk.Label(diff_dice_frame, image=img)
                        lbl.image = img
                        lbl.pack(side=tk.LEFT, padx=2)
                    else:
                        ttk.Label(diff_dice_frame, text=f"[{roll}]").pack(side=tk.LEFT, padx=2)

            # --- Display Danger Die Roll ---
            danger_die_frame = ttk.Frame(details_frame)
            danger_die_frame.pack(anchor='w', padx=5, pady=2)
            ttk.Label(danger_die_frame, text="Danger Die:").pack(side=tk.LEFT, padx=(0, 5))
            danger_roll = results_data['danger_die']
            if danger_roll is None:
                 ttk.Label(danger_die_frame, text="N/A").pack(side=tk.LEFT, padx=2)
            else:
                img = self._get_tk_dice_image(danger_roll)
                if img:
                    lbl = ttk.Label(danger_die_frame, image=img)
                    lbl.image = img
                    lbl.pack(side=tk.LEFT, padx=2)
                else:
                    ttk.Label(danger_die_frame, text=f"[{danger_roll}]").pack(side=tk.LEFT, padx=2)
        else:
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

        # Center the window relative to the parent (if parent exists)
        if hasattr(self, 'parent') and self.parent and self.parent.winfo_exists():
            self.update_idletasks()
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_w = self.parent.winfo_width()
            parent_h = self.parent.winfo_height()
            win_w = self.winfo_width()
            win_h = self.winfo_height()
            x = parent_x + (parent_w - win_w) // 2
            y = parent_y + (parent_h - win_h) // 2
            self.geometry(f"+{x}+{y}")

        self.wait_window()

    def _get_tk_dice_image(self, value):
        """Gets a Tk dice image, creating it from PIL if not cached."""
        # (Code is the same as before)
        if not self.winfo_exists(): return None
        if value not in self.tk_dice_images:
            pil_img = self.pil_dice_images.get(value)
            if pil_img:
                try:
                    self.tk_dice_images[value] = ImageTk.PhotoImage(pil_img, master=self)
                except Exception as e:
                    print(f"Error creating Tk dice image for {value} in ResultsWindow: {e}")
                    if self.winfo_exists():
                         messagebox.showerror("Image Error", f"Failed to load dice image {value}.\nPlease check asset files.", parent=self)
                    self.tk_dice_images[value] = None
            else:
                 print(f"Warning: PIL dice image not found for value {value}")
                 self.tk_dice_images[value] = None
        return self.tk_dice_images.get(value)

# --- END OF FILE combat/ui_results.py ---