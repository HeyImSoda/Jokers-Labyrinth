# --- START OF FILE hand_manager.py ---

import tkinter as tk
import config # For hand layout settings

def _redraw_hand_row(row_index, hand_card_data, hand_card_slots, tk_card_face_images, parent_bg_color):
    """
    Updates the visual display of a specific hand row based on the current hand_card_data.
    Assumes hand_card_data for this row is already compacted (no Nones between cards).
    """
    print(f"Redrawing hand row {row_index}...")
    card_count_in_row = 0
    for c_idx in range(config.HAND_COLS):
        card = hand_card_data[row_index][c_idx]
        label = hand_card_slots[row_index][c_idx]

        if not (label and label.winfo_exists()):
             print(f"  WARN: Label missing for slot ({row_index},{c_idx})")
             continue # Skip if label doesn't exist

        if card is not None:
            # Display this card
            suit_key = str(card.get_suit()).lower()
            rank_key = str(card.get_rank_string()).lower()
            image_key = f"{suit_key}_{rank_key}"
            tk_photo = tk_card_face_images.get(image_key)

            if tk_photo:
                label.config(image=tk_photo, bg=parent_bg_color, relief=tk.FLAT, borderwidth=0)
                label.image = tk_photo
                label.lift() # Ensure correct stacking order
                # print(f"  Placed {card} at visual slot ({row_index},{c_idx})") # Debug
                card_count_in_row += 1
            else:
                print(f"  ERROR: Image not found for {image_key} during redraw.")
                label.config(image='', bg=parent_bg_color) # Show empty if image missing
                label.image = None
        else:
            # Clear this slot (should be slots after the last card)
            label.config(image='', bg=parent_bg_color)
            label.image = None
            # print(f"  Cleared visual slot ({row_index},{c_idx})") # Debug

    print(f"- Row {row_index} redraw complete ({card_count_in_row} cards shown).")


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
                # Found empty data slot
                print(f"Adding {card_to_add} to hand slot ({r},{c})")
                hand_card_data[r][c] = card_to_add # Update data
                hand_label = hand_card_slots[r][c] # Get corresponding label

                suit_key = str(card_to_add.get_suit()).lower()
                rank_key = str(card_to_add.get_rank_string()).lower()
                image_key = f"{suit_key}_{rank_key}"
                tk_photo = tk_card_face_images.get(image_key)

                if tk_photo and hand_label and hand_label.winfo_exists():
                    # Update the specific label
                    hand_label.config(image=tk_photo, bg=parent_bg_color, relief=tk.FLAT, borderwidth=0)
                    hand_label.image = tk_photo
                    hand_label.lift()
                    return True
                else:
                    # Error handling...
                    error_msg = f"Error displaying hand card at ({r},{c}): "
                    if not tk_photo: error_msg += f"Image '{image_key}' not found. "
                    if not hand_label: error_msg += "Label widget is None. "
                    elif not hand_label.winfo_exists(): error_msg += "Label widget destroyed."
                    print(error_msg)
                    hand_card_data[r][c] = None # Revert data change on error
                    return False

    print(f"Hand is full. Cannot add card {card_to_add}.")
    return False

# --- MODIFIED: remove_card_from_hand ---
def remove_card_from_hand(card_to_remove, hand_card_data, hand_card_slots, tk_card_face_images):
    """
    Removes a specific card from the hand data, compacts the data row,
    and redraws the visual row.
    """
    if not card_to_remove: return False
    found = False
    removed_from_row = -1
    parent_bg_color = None # Will get this from a slot

    # Find the card and its row
    for r in range(config.HAND_ROWS):
        if card_to_remove in hand_card_data[r]:
            print(f"Removing {card_to_remove} from hand row {r}")
            # Get background color from one of the labels in this row
            # Find first valid label in row to get parent bg
            for slot_label in hand_card_slots[r]:
                if slot_label and slot_label.winfo_exists():
                    parent_bg_color = slot_label.master.cget('bg')
                    break

            if parent_bg_color is None:
                 print(f"Error: Could not determine background color for hand row {r}.")
                 return False # Cannot redraw without bg color

            # Remove the card from the data list for this row
            hand_card_data[r].remove(card_to_remove)
            # Pad the end with None to maintain list size
            hand_card_data[r].append(None)

            removed_from_row = r
            found = True
            break # Stop searching rows

    if found:
        # Redraw the entire visual row based on the updated data
        _redraw_hand_row(removed_from_row, hand_card_data, hand_card_slots, tk_card_face_images, parent_bg_color)
        return True
    else:
        print(f"Warning: Card {card_to_remove} not found in hand_card_data to remove.")
        return False
# ---------------------------------------

def clear_hand_display(hand_card_data, hand_card_slots):
    """Removes all cards from hand data and clears all visual slots."""
    print("Clearing player hand display...")
    cleared_count = 0
    parent_bg_color = None

    for r in range(config.HAND_ROWS):
        # Try to get bg color once per row
        if parent_bg_color is None:
             for slot_label in hand_card_slots[r]:
                if slot_label and slot_label.winfo_exists():
                    parent_bg_color = slot_label.master.cget('bg')
                    break

        bg_color_to_use = parent_bg_color if parent_bg_color else "grey20" # Fallback color

        for c in range(config.HAND_COLS):
            if hand_card_data[r][c] is not None:
                hand_card_data[r][c] = None # Clear data
                cleared_count += 1
            slot_label = hand_card_slots[r][c]
            if slot_label and slot_label.winfo_exists():
                # Reset the visual slot
                slot_label.config(image='', bg=bg_color_to_use) # Use determined/fallback bg
                slot_label.image = None

    print(f"- Cleared {cleared_count} cards from hand data and display.")

# --- END OF FILE hand_manager.py ---