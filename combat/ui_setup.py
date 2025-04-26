# --- START OF FILE combat/ui_setup.py ---

import tkinter as tk
from tkinter import ttk

# No longer a Toplevel window

class CombatSetupView: # Renamed from CombatSetupWindow
    """View for selecting a value card before combat, displayed within a parent frame."""
    def __init__(self, parent_frame, target_card, value_cards_in_hand, callback):
        # self.parent = parent # No longer need Toplevel parent
        self.parent_frame = parent_frame # The frame to build UI into (info_frame)
        self.target_card = target_card
        self.value_cards = value_cards_in_hand # List of (Card, row, col) tuples
        self.callback = callback # Called with selection or False on cancel
        self.selected_card_info = None

        # Create the main frame for this view's content
        self.frame = ttk.Frame(self.parent_frame, padding=(15, 15))
        # self.frame.pack(fill='x', expand=True) # Don't pack here, display() method will do it

        # --- UI Elements packed into self.frame ---
        target_rank = target_card.get_rank()
        target_value_display = "N/A" # Default
        if target_rank == 12: target_value_display = 12
        elif target_rank == 13: target_value_display = 13
        elif target_rank is not None and 2 <= target_rank <= 10: target_value_display = target_rank

        ttk.Label(self.frame, text=f"Fight {target_card} (Value: {target_value_display})?",
                  font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(self.frame, text="Use Equipment or Friendly Face Card from hand (optional):").pack(pady=5)

        self.selection_var = tk.StringVar(self.frame) # Master is the frame
        self.selection_var.set("None") # Default selection

        rb_none = ttk.Radiobutton(self.frame, text="Use No Card (Value: 0)", variable=self.selection_var,
                                  value="None", command=self._update_selection)
        rb_none.pack(anchor='w', padx=10)

        self.radio_buttons = {}
        if not self.value_cards:
             ttk.Label(self.frame, text="(No valid value cards in hand)").pack(anchor='w', padx=10)
        else:
            for card, r, c in self.value_cards:
                value_str = f"card_{r}_{c}" # Unique value for radio button
                card_rank = card.get_rank()
                card_value_display = "N/A" # Default
                if card_rank == 12: card_value_display = 12
                elif card_rank == 13: card_value_display = 13
                elif card_rank is not None and 2 <= card_rank <= 10: card_value_display = card_rank

                rb = ttk.Radiobutton(self.frame, text=f"{card} (Value: {card_value_display})",
                                     variable=self.selection_var,
                                     value=value_str, command=self._update_selection)
                rb.pack(anchor='w', padx=10)
                self.radio_buttons[value_str] = (card, r, c) # Map value_str to card info

        ttk.Separator(self.frame, orient='horizontal').pack(fill='x', pady=10)

        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill='x', pady=(10, 0))

        fight_button = ttk.Button(button_frame, text="Fight!", command=self._confirm_fight)
        fight_button.pack(side=tk.LEFT, expand=True, padx=5, fill='x')
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel)
        cancel_button.pack(side=tk.RIGHT, expand=True, padx=5, fill='x')
        # --- Removed wait_window ---

    def display(self):
        """Packs the view's frame into the parent frame."""
        # Pack the main frame into the parent (e.g., info_frame)
        # Use appropriate pack options depending on where in info_frame it should go
        self.frame.pack(fill='x', pady=20) # Example packing

    def destroy_view(self):
        """Destroys the view's main frame."""
        if self.frame and self.frame.winfo_exists():
            self.frame.destroy()

    def _update_selection(self):
        """Updates the internal selection based on the radio button."""
        selection = self.selection_var.get()
        self.selected_card_info = None if selection == "None" else self.radio_buttons.get(selection)

    def _confirm_fight(self):
        """Calls the callback with the selected card info."""
        self._update_selection() # Ensure latest selection is captured
        # No need to destroy here, the manager calling the callback will handle it
        self.callback(self.selected_card_info) # Pass selection (or None) back

    def _cancel(self):
        """Calls the callback with False to indicate cancellation."""
        # No need to destroy here, the manager calling the callback will handle it
        self.callback(False) # Indicate cancellation

# --- END OF FILE combat/ui_setup.py ---