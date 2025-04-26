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
                    # Configure the slot label
                    hand_label.config(image=tk_photo, bg=parent_bg_color, relief=tk.FLAT, borderwidth=0)
                    hand_label.image = tk_photo # Keep reference!
                    hand_label.lift() # Bring to top
                    return True
                else:
                    error_msg = f"Error displaying hand card at ({r},{c}): "
                    if not tk_photo: error_msg += f"Image '{image_key}' not found. "
                    if not hand_label: error_msg += "Label widget is None. "
                    elif not hand_label.winfo_exists(): error_msg += "Label widget destroyed."
                    print(error_msg)
                    hand_card_data[r][c] = None # Revert data change
                    return False

    print(f"Hand is full. Cannot add card {card_to_add}.")
    return False

def remove_card_from_hand(card_to_remove, hand_card_data, hand_card_slots):
    """Removes a specific card from the hand data and clears its visual slot."""
    if not card_to_remove: return False
    for r in range(config.HAND_ROWS):
        for c in range(config.HAND_COLS):
             if hand_card_data[r][c] == card_to_remove:
                 print(f"Removing {card_to_remove} from hand slot ({r},{c})")
                 hand_card_data[r][c] = None # Remove data
                 slot_label = hand_card_slots[r][c]
                 if slot_label and slot_label.winfo_exists():
                     # Reset the visual slot to look empty
                     slot_label.config(image='', bg=slot_label.master.cget('bg')) # Use parent background
                     slot_label.image = None # Clear ref
                 return True # Card found and removed
    print(f"Warning: Card {card_to_remove} not found in hand_card_data to remove.")
    return False

def clear_hand_display(hand_card_data, hand_card_slots):
    """Removes all cards from hand data and clears all visual slots."""
    print("Clearing player hand display...")
    cleared_count = 0
    for r in range(config.HAND_ROWS):
        for c in range(config.HAND_COLS):
            if hand_card_data[r][c] is not None:
                hand_card_data[r][c] = None # Clear data
                cleared_count += 1
            slot_label = hand_card_slots[r][c]
            if slot_label and slot_label.winfo_exists():
                # Reset the visual slot
                slot_label.config(image='', bg=slot_label.master.cget('bg'))
                slot_label.image = None
    print(f"- Cleared {cleared_count} cards from hand data and display.")

# --- END OF FILE hand_manager.py ---