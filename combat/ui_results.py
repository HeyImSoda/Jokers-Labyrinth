# --- START OF FILE combat/ui_results.py ---

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk, Image # Ensure Image is imported

# No longer a Toplevel window

class CombatResultsView: # Renamed from CombatResultsWindow
    """View to display combat results, displayed within a parent frame."""
    def __init__(self, parent_frame, results_data, pil_dice_images, ok_callback):
        # self.parent = parent # No longer need Toplevel parent
        self.parent_frame = parent_frame # The frame to build UI into (info_frame)
        self.results_data = results_data
        self.pil_dice_images = pil_dice_images if pil_dice_images else {} # Ensure dict
        self.tk_dice_images = {} # Cache Tk images locally
        self.ok_callback = ok_callback # Called when OK is clicked

        # Create the main frame for this view's content
        self.frame = ttk.Frame(self.parent_frame, padding=(15, 15))

        # --- UI Elements packed into self.frame ---

        # --- 1. Outcome Header ---
        outcome_text = "YOU WIN!" if results_data["win"] else "YOU LOSE..."
        outcome_color = "dark green" if results_data["win"] else "dark red"
        ttk.Label(self.frame, text=outcome_text, font=("Arial", 16, "bold"), foreground=outcome_color).pack(pady=(0,15))

        # --- 2. Details Frame ---
        details_frame = ttk.LabelFrame(self.frame, text="Details", padding=(10, 5))
        details_frame.pack(fill='x', pady=5)

        # (Attacker/Defender/Dice info packing remains the same as before)
        ttk.Label(details_frame, text=f"Target: {results_data['target']} (Value: {results_data['defender_total']})").pack(anchor='w', padx=5, pady=2)
        used_card_text = f"Used: {results_data['used_card']} (Value: {results_data['attacker_total']})" if results_data['used_card'] else f"Used: None (Value: {results_data['attacker_total']})"
        ttk.Label(details_frame, text=used_card_text).pack(anchor='w', padx=5, pady=2)

        if results_data.get("automatic_win", False):
             ttk.Label(details_frame, text="Result: Automatic Win (Attacker Value > Defender Value)", foreground="blue").pack(anchor='w', padx=5, pady=2)
        elif results_data['num_diff_dice'] is not None and results_data['danger_die'] is not None :
            ttk.Label(details_frame, text=f"Difference: {results_data['difference']}").pack(anchor='w', padx=5, pady=2)
            # Display Difference Dice Rolls
            diff_dice_frame = ttk.Frame(details_frame)
            diff_dice_frame.pack(anchor='w', padx=5, pady=2)
            ttk.Label(diff_dice_frame, text=f"Difference Dice ({results_data['num_diff_dice']}):").pack(side=tk.LEFT, padx=(0, 5))
            if not results_data['diff_dice_rolls']:
                 ttk.Label(diff_dice_frame, text="N/A").pack(side=tk.LEFT, padx=2)
            else:
                for roll in results_data['diff_dice_rolls']:
                    img = self._get_tk_dice_image(roll)
                    if img:
                        lbl = ttk.Label(diff_dice_frame, image=img); lbl.image = img
                        lbl.pack(side=tk.LEFT, padx=2)
                    else:
                        ttk.Label(diff_dice_frame, text=f"[{roll}]", font=("Arial", 12)).pack(side=tk.LEFT, padx=2)
            # Display Danger Die Roll
            danger_die_frame = ttk.Frame(details_frame)
            danger_die_frame.pack(anchor='w', padx=5, pady=2)
            ttk.Label(danger_die_frame, text="Danger Die:").pack(side=tk.LEFT, padx=(0, 5))
            danger_roll = results_data['danger_die']
            img = self._get_tk_dice_image(danger_roll)
            if img:
                lbl = ttk.Label(danger_die_frame, image=img); lbl.image = img
                lbl.pack(side=tk.LEFT, padx=2)
            else:
                 roll_text = f"[{danger_roll}]" if danger_roll is not None else "N/A"
                 ttk.Label(danger_die_frame, text=roll_text, font=("Arial", 12)).pack(side=tk.LEFT, padx=2)
        else:
             ttk.Label(details_frame, text="Result determined without dice roll.").pack(anchor='w', padx=5, pady=2)


        # --- 3. Consequences Frame ---
        consequences_frame = ttk.LabelFrame(self.frame, text="Consequences", padding=(10, 5))
        consequences_frame.pack(fill='x', pady=10)
        if not results_data.get("consequences"):
             ttk.Label(consequences_frame, text="- None").pack(anchor='w', padx=5, pady=2)
        else:
            for line in results_data["consequences"]:
                ttk.Label(consequences_frame, text=f"- {line}", wraplength=350).pack(anchor='w', padx=5, pady=1)


        # --- 4. OK Button ---
        # Command now calls the ok_callback provided by the manager
        ok_button = ttk.Button(self.frame, text="OK", command=self.ok_callback)
        ok_button.pack(pady=(15, 0))
        ok_button.focus_set() # Set focus

        # --- Removed centering logic and wait_window ---

    def display(self):
        """Packs the view's frame into the parent frame."""
        self.frame.pack(fill='x', pady=20) # Example packing

    def destroy_view(self):
        """Destroys the view's main frame."""
        if self.frame and self.frame.winfo_exists():
            self.frame.destroy()

    # --- _get_tk_dice_image (remains the same, uses self.frame as master) ---
    def _get_tk_dice_image(self, value):
        if not self.frame or not self.frame.winfo_exists(): return None
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
                print(f"Error creating Tk image for {key} in ResultsView: {e}")
                if key not in self.tk_dice_images:
                     if self.frame.winfo_exists():
                        messagebox.showerror("Image Error", f"Failed to load dice image {key}.\nError: {e}", parent=self.frame)
                self.tk_dice_images[key] = None; return None
        else:
             self.tk_dice_images[key] = None; return None

# --- END OF FILE combat/ui_results.py ---