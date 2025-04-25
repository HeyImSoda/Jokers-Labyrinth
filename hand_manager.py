# --- START OF FILE hand_manager.py ---

import tkinter as tk
import config # For hand layout settings

def add_card_to_hand_display(card_to_add, hand_card_data, hand_card_slots, tk_card_face_images, parent_bg_color):
    """
    Finds the first empty slot in the hand and displays the card.
    Raises the card label to the top of the stacking order.
    """
    if not card_to_add:
        print("Warning: Tried to add None card to hand.")
        return False

    for r in range(config.HAND_ROWS):
        for c in range(config.HAND_COLS):
            if hand_card_data[r][c] is None:
                # Found empty slot
                print(f"Adding {card_to_add} to hand slot ({r},{c})")
                hand_card_data[r][c] = card_to_add
                hand_label = hand_card_slots[r][c]

                suit_key = str(card_to_add.get_suit()).lower()
                rank_key = str(card_to_add.get_rank_string()).lower()
                image_key = f"{suit_key}_{rank_key}"

                tk_photo = tk_card_face_images.get(image_key)

                if tk_photo and hand_label and hand_label.winfo_exists():
                    # Make the slot visible with the card image
                    hand_label.config(image=tk_photo,
                                      bg=parent_bg_color, # Use parent background
                                      relief=tk.FLAT,
                                      borderwidth=0)
                    hand_label.image = tk_photo # Keep reference!

                    # --- MODIFICATION: Bring this label to the top ---
                    hand_label.lift()
                    # --------------------------------------------------

                    return True # Card added successfully
                else:
                    error_msg = f"Error displaying hand card at ({r},{c}): "
                    if not tk_photo: error_msg += f"Image '{image_key}' not found. "
                    if not hand_label: error_msg += "Label widget is None. "
                    elif not hand_label.winfo_exists(): error_msg += "Label widget destroyed."
                    print(error_msg)
                    hand_card_data[r][c] = None # Revert data change
                    return False # Failed to add

    print(f"Hand is full. Cannot add card {card_to_add}.")
    return False # Hand is full

# --- END OF FILE hand_manager.py ---