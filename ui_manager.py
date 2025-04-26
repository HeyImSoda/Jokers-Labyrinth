# --- START OF FILE ui_manager.py ---

import tkinter as tk
from tkinter import ttk
import config

# (create_main_window, setup_layout remain the same)
def create_main_window():
    """Creates and configures the main Tkinter window."""
    root = tk.Tk()
    root.title("Joker's Labyrinth")
    root.config(bg="dark green")
    # Consider setting a minimum size based on grid/info panel?
    # root.minsize(width=..., height=...)
    return root

def setup_layout(root, scaled_width, scaled_height):
    """Creates main layout frames (grid, info) and configures resizing."""
    grid_frame = tk.Frame(root, bg=root.cget('bg'))
    info_frame = tk.Frame(root, bg="grey20", width=config.INFO_PANEL_WIDTH, padx=15, pady=15)

    pad_x = int(scaled_width * config.GRID_PADDING_FACTOR)
    pad_y = int(scaled_height * config.GRID_PADDING_FACTOR)

    grid_frame.grid(row=0, column=0, sticky="nsew", padx=pad_x, pady=pad_y)
    info_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    # Let info panel expand, grid frame + padding stay fixed width relative to cards
    root.grid_columnconfigure(0, weight=0)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)

    return grid_frame, info_frame


def setup_info_panel_content(info_frame, player_identity_text="Player Info"):
    """Adds title, separator, and player info/status label to the info panel."""
    title_label = tk.Label(info_frame, text="Joker's Labyrinth", font=("Arial", 24, "bold"), fg="white", bg=info_frame.cget('bg'))
    title_label.pack(pady=10, anchor='n')

    separator = ttk.Separator(info_frame, orient='horizontal')
    separator.pack(fill='x', pady=10)

    # Use a StringVar for the info label text so it can be updated easily later
    info_text_var = tk.StringVar()
    # --- MODIFICATION: Use passed player identity text ---
    initial_info = f"{player_identity_text}\n(Position, Actions, Turn Info Placeholder)"
    info_text_var.set(initial_info)
    # -----------------------------------------------------
    info_content_label = tk.Label(info_frame, textvariable=info_text_var, justify=tk.LEFT, font=("Arial", 12), fg="light grey", bg=info_frame.cget('bg'), wraplength=config.INFO_PANEL_WIDTH - 40) # Add wraplength
    info_content_label.pack(pady=20, anchor='n', fill='x')

    return info_text_var # Return the StringVar for future updates

# (setup_hand_display remains the same)
def setup_hand_display(info_frame, scaled_width, scaled_height):
    """Creates the hand frame and invisible placeholder slots."""
    hand_frame = tk.Frame(info_frame, bg=info_frame.cget('bg'))
    # Pack below the info label, allow space
    hand_frame.pack(pady=(40, 20), anchor='n') # Increased top padding

    overlap_step_x = int(scaled_width * config.HAND_OVERLAP_FACTOR)
    overlap_step_x = max(1, overlap_step_x)

    hand_card_slots = [[None for _ in range(config.HAND_COLS)] for _ in range(config.HAND_ROWS)]

    print(f"Creating hand display area ({config.HAND_ROWS}x{config.HAND_COLS})...")
    for hr in range(config.HAND_ROWS):
        for hc in range(config.HAND_COLS):
            slot_label = tk.Label(hand_frame,
                                  bg=hand_frame.cget('bg'),
                                  borderwidth=0,
                                  relief=tk.FLAT)

            pos_x = hc * overlap_step_x
            pos_y = hr * (scaled_height + config.HAND_VERTICAL_PADDING)

            # Use place for overlapping layout
            slot_label.place(x=pos_x, y=pos_y, width=scaled_width, height=scaled_height)
            hand_card_slots[hr][hc] = slot_label

    # Configure hand_frame size explicitly to ensure it contains the placed labels
    # Height calculation needs to account for full height of cards + padding between rows
    # Width calculation needs to account for overlap + full width of last card
    hand_frame_height = config.HAND_ROWS * scaled_height + max(0, config.HAND_ROWS - 1) * config.HAND_VERTICAL_PADDING
    hand_frame_width = (config.HAND_COLS - 1) * overlap_step_x + scaled_width
    hand_frame.config(width=max(1, hand_frame_width), height=max(1, hand_frame_height)) # Ensure non-zero size
    # Make the frame not propagate its size from children, we set it explicitly
    hand_frame.pack_propagate(False)


    return hand_frame, hand_card_slots
# --- END OF FILE ui_manager.py ---