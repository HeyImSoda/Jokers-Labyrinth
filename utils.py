# --- START OF FILE utils.py ---

import random # <--- Added missing import

def simple_print_grid(grid_to_print, title="Grid", cols=None):
    """Prints a 2D grid to the console with basic formatting."""
    print(f"\n--- Simple {title} Printout ---")
    if not grid_to_print or not grid_to_print[0]:
        print("[Grid is empty or invalid]")
        return

    num_rows = len(grid_to_print)
    num_cols = cols if cols else len(grid_to_print[0]) # Use provided cols or infer

    # Find max width for alignment
    max_len = 0
    for r in range(num_rows):
        for c in range(num_cols):
            try:
                 item_repr = repr(grid_to_print[r][c])
                 if len(item_repr) > max_len: max_len = len(item_repr)
            except IndexError:
                 pass

    # Print grid
    for row_idx, row in enumerate(grid_to_print):
        print(f"Row {row_idx}: ", end="")
        for c_idx in range(num_cols):
            try:
                 item_repr = repr(row[c_idx])
            except IndexError:
                 item_repr = " "
            print(f"{item_repr:<{max_len+2}}", end="")
        print()
    print("-" * (num_cols * (max_len + 2) + 5) + "\n")

# --- ADDED Missing Dice Rolling Function ---
def roll_dice(num_dice):
    """ Rolls a specified number of standard 6-sided dice. """
    if num_dice <= 0:
        return []
    # Ensure random is imported at the top
    return [random.randint(1, 6) for _ in range(num_dice)]
# -----------------------------------------

# --- END OF FILE utils.py ---