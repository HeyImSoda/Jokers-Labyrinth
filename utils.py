# --- START OF FILE utils.py ---

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
            # Handle potential errors if grid ragged and cols not provided
            try:
                 item_repr = repr(grid_to_print[r][c])
                 if len(item_repr) > max_len: max_len = len(item_repr)
            except IndexError:
                 pass # Ignore cells outside inferred width if grid is ragged

    # Print grid
    for row_idx, row in enumerate(grid_to_print):
        print(f"Row {row_idx}: ", end="")
        for c_idx in range(num_cols):
            try:
                 item_repr = repr(row[c_idx])
            except IndexError:
                 item_repr = " " # Print space for missing columns
            print(f"{item_repr:<{max_len+2}}", end="")
        print()
    print("-" * (num_cols * (max_len + 2) + 5) + "\n")


# --- END OF FILE utils.py ---