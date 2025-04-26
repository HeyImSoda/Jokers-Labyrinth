# --- START OF FILE combat/ui_setup.py ---

import tkinter as tk
from tkinter import ttk

# No other imports needed specifically for this window class itself

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
        if target_rank == 12: target_value_display = 12
        elif target_rank == 13: target_value_display = 13
        elif target_rank is not None and 2 <= target_rank <= 10: target_value_display = target_rank

        ttk.Label(self, text=f"Fight {target_card} (Value: {target_value_display})?",
                  font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(self, text="Use Equipment or Friendly Face Card from hand (optional):").pack(pady=5)

        self.selection_var = tk.StringVar(self)
        self.selection_var.set("None")

        rb_none = ttk.Radiobutton(self, text="Use No Card (Value: 0)", variable=self.selection_var,
                                  value="None", command=self._update_selection)
        rb_none.pack(anchor='w', padx=10)

        self.radio_buttons = {}
        if not self.value_cards:
             ttk.Label(self, text="(No valid value cards in hand)").pack(anchor='w', padx=10)
        else:
            for card, r, c in self.value_cards:
                value_str = f"card_{r}_{c}"
                card_rank = card.get_rank()
                card_value_display = "N/A" # Default
                if card_rank == 12: card_value_display = 12
                elif card_rank == 13: card_value_display = 13
                elif card_rank is not None and 2 <= card_rank <= 10: card_value_display = card_rank

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
        # --- ADDED Cancel Button ---
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel)
        cancel_button.pack(side=tk.RIGHT, expand=True, padx=5)
        # -------------------------

        self.wait_window()

    def _update_selection(self):
        selection = self.selection_var.get()
        self.selected_card_info = None if selection == "None" else self.radio_buttons.get(selection)

    def _confirm_fight(self):
        self._update_selection()
        self.destroy()
        self.callback(self.selected_card_info)

    # --- Ensure Cancel Callback ---
    def _cancel(self):
        self.destroy()
        self.callback(False) # Indicate cancellation
    # --------------------------

# --- END OF FILE combat/ui_setup.py ---