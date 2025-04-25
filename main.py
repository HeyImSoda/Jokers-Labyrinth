# --- START OF FILE main.py ---

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import time # Potentially needed for delays if actions get complex

# --- Import from card logic module ---
try:
    # Assuming Card class has attributes like:
    # card.suit (e.g., "hearts", "clubs", "black_joker")
    # card.rank (e.g., 1 (Ace) to 13 (King), 14 (Joker))
    # card.rank_string (e.g., "ace", "two", "king", "fourteen")
    # card.get_suit() -> returns suit
    # card.get_rank_string() -> returns rank_string
    # card.get_color() -> returns 'red' or 'black' (or None for Jokers?) - ADD THIS TO card_logic.py if needed
    from card_logic import Card, create_shuffled_deck
except ImportError:
    print("Error: Could not import from card_logic.py.")
    print("Make sure card_logic.py is in the same directory as main.py.")
    print("Ensure the Card class has suit, rank, rank_string attributes/methods.")
    exit()
except AttributeError:
    print("Error: Imported Card class might be missing expected attributes/methods (suit, rank, rank_string).")
    exit()


# --- Configuration ---
assets_base_path = r"C:\Users\stell\Desktop\Python Files\Jokers_Labyrinth\assets" # <<< Use your actual path
card_faces_path = os.path.join(assets_base_path, "card_faces")
card_back_path = os.path.join(assets_base_path, "card_back.png")

rows = 7
columns = 7
animation_delay = 6
animation_steps = 36
card_scale_factor = 1.5
info_panel_width = 300

# --- NEW: Game State / Player Info ---
player_suit = "spades" # Example: Player is the Jack of Spades. Change as needed.
print(f"Player Suit Set To: {player_suit.upper()}")

# Card state tracking (optional but can be useful)
# 0: Face Down, 1: Face Up (Actionable), 2: Action Taken/Disabled
card_state_grid = [[0 for _ in range(columns)] for _ in range(rows)]


# --- Basic File/Directory Checks ---
# ... (keep existing checks) ...
if not os.path.exists(card_back_path):
    print(f"Error: Card back image file not found at path: {card_back_path}")
    exit()
if not os.path.isdir(card_faces_path):
    print(f"Error: Card faces directory not found at path: {card_faces_path}")
    exit()

# --- Create the main window ---
root = tk.Tk()
root.title("Joker's Labyrinth")
root.config(bg="dark green")

# --- Load Card Back Image and Apply Scaling ---
# ... (keep existing image loading and scaling) ...
try:
    card_back_pil_original = Image.open(card_back_path)
    original_width, original_height = card_back_pil_original.size
    scaled_width = int(original_width * card_scale_factor)
    scaled_height = int(original_height * card_scale_factor)
    card_back_pil_scaled = card_back_pil_original.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
    tk_photo_back_scaled = ImageTk.PhotoImage(card_back_pil_scaled)
except Exception as e:
    print(f"An error occurred while loading card back image: {e}")
    root.destroy()
    exit()

# --- Pre-load Card Face Images (Scaled) ---
# ... (keep existing image loading and scaling) ...
card_face_images_pil = {}
tk_card_face_images = {}
print("Loading and scaling card face images...")
if os.path.isdir(card_faces_path):
    loaded_count = 0
    # ... (rest of the image loading loop remains the same) ...
    for filename in os.listdir(card_faces_path):
        if filename.lower().endswith(".png"):
            image_path = os.path.join(card_faces_path, filename)
            image_key = filename.lower().replace('.png', '')
            try:
                img_pil_original = Image.open(image_path)
                img_pil_scaled = img_pil_original.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                card_face_images_pil[image_key] = img_pil_scaled
                tk_card_face_images[image_key] = ImageTk.PhotoImage(img_pil_scaled)
                loaded_count += 1
            except Exception as e:
                print(f"Warning: Could not load or process {filename}: {e}")
    print(f"Loaded {loaded_count} card face images.")
    expected_image_count = 54
    if loaded_count < expected_image_count:
         print(f"Warning: Expected {expected_image_count} images, but only found {loaded_count}.")
else:
    print(f"Error: Card faces directory not found: {card_faces_path}")
    # exit()


# --- Create Frames for Layout ---
# ... (keep existing frame setup) ...
grid_frame = tk.Frame(root, bg=root.cget('bg'))
info_frame = tk.Frame(root, bg="grey20", width=info_panel_width, padx=15, pady=15)
grid_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
info_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# --- Add Title & Info Panel Content ---
# ... (keep existing info panel setup) ...
title_label = tk.Label(info_frame, text="Joker's Labyrinth", font=("Arial", 24, "bold"), fg="white", bg=info_frame.cget('bg'))
title_label.pack(pady=10, anchor='n')
separator = ttk.Separator(info_frame, orient='horizontal')
separator.pack(fill='x', pady=10)
info_content_label = tk.Label(info_frame, text=f"Playing as Jack of {player_suit.title()}\n(Turn Info Placeholder)", justify=tk.LEFT, font=("Arial", 12), fg="light grey", bg=info_frame.cget('bg'))
info_content_label.pack(pady=20, anchor='n', fill='x')


# --- Create and Shuffle the Deck ---
# ... (keep existing deck creation and modification) ...
full_deck = create_shuffled_deck()
try:
    card_to_remove = Card(suit="clubs", rank=2, rank_string="two")
    # Ensure your Card class __eq__ method works correctly for removal
    if card_to_remove in full_deck:
        full_deck.remove(card_to_remove)
    else:
         print(f"Warning: Could not find {card_to_remove} in deck to remove.")
    full_deck.append(Card("black_joker", 14, "fourteen"))
    middle_index = len(full_deck) // 2
    full_deck.insert(middle_index, Card("red_joker", 14, "fourteen"))
except (ValueError, AttributeError, TypeError) as e:
    # Catch potential issues with Card comparison or attributes
    print(f"Error modifying deck: {e}. Check Card definition, __eq__, and presence.")

print(f"Deck size: {len(full_deck)}")
# --- Prepare Grids ---
card_data_grid = [[None for _ in range(columns)] for _ in range(rows)]
button_grid = [[None for _ in range(columns)] for _ in range(rows)]
# Card state grid already initialized above

# --- Deal Cards into the Grid ---
# ... (keep existing dealing logic) ...
print("Dealing cards into grid...")
cards_needed = rows * columns
card_index = 0
deal_complete = False
for r in range(rows):
    if deal_complete: break
    for c in range(columns):
        if card_index < len(full_deck):
            card_data_grid[r][c] = full_deck[card_index]
            card_state_grid[r][c] = 0 # State: Face Down
            card_index += 1
            if card_index >= cards_needed:
                deal_complete = True
                break
        else:
            print("Warning: Deck ran out of cards before filling the grid.")
            deal_complete = True
            break


# --- NEW: Function to Handle Action on Revealed Card ---
def handle_card_action(row, col):
    """
    Determines and executes the action for a revealed card based on game rules.
    This currently just prints placeholder actions.
    """
    button = button_grid[row][col]
    card = card_data_grid[row][col]

    if not card or not button or not button.winfo_exists():
        print(f"Error: Missing card, button, or button destroyed for action at ({row},{col}).")
        return

    # --- Permanently Disable after Action ---
    button.config(state=tk.DISABLED)
    card_state_grid[row][col] = 2 # State: Action Taken/Disabled
    print(f"--- Action taken for card {card} at ({row}, {col}) ---")

    # --- Determine Action Based on Card ---
    card_suit = card.get_suit().lower() # Ensure lowercase for comparison
    card_rank = card.rank # Assuming rank is an integer attribute
    card_color = None # Determine color (requires Card class support or logic here)

    # Basic color determination (add to Card class ideally)
    if card_suit in ["hearts", "diamonds"]:
        card_color = "red"
    elif card_suit in ["clubs", "spades"]:
        card_color = "black"

    # Jokers
    if "joker" in card_suit:
        print("Action: Joker! (Special effect TBD)")
        # Future: Implement Joker effect

    # Number Cards (Assuming Ace=1, 2-10)
    elif 1 <= card_rank <= 10:
        if card_color == "red":
            print(f"Action: Pickup Red Number ({card.rank_string.title()})")
            # Future: Implement pickup logic
        elif card_color == "black":
            print(f"Action: Battle Black Number ({card.rank_string.title()})")
            # Future: Implement battle logic
        else:
             print(f"Warning: Unknown color for number card {card}")

    # Face Cards (Assuming Jack=11, Queen=12, King=13)
    elif 11 <= card_rank <= 13:
        is_player_suit = (card_suit == player_suit)
        print(f"Action: Face Card ({card.rank_string.title()} of {card_suit.title()})")
        if is_player_suit:
            print("   - Option: Pickup (Player Suit)")
            print("   - Option: Battle (Player Suit)")
            # Future: Let player choose or implement rules
        else:
            print("   - Action: Battle (Other Suit)")
            # Future: Implement battle logic

    # Unknown Card Type
    else:
        print(f"Action: Unknown card type - {card}")

    print("-------------------------------------------------")
    # --- Add Effects Here (e.g., removing card image, updating score) ---
    # Example: Make the card visually disappear after action
    # button.config(image='') # Clear image
    # button.image = None
    # Or hide the button completely:
    # button.grid_forget()


# --- Modified Function called AFTER the GROW animation finishes ---
def on_card_revealed(row, col):
    """
    Finalizes the card reveal after animation.
    Sets the final face image AND RE-ENABLES the button for the second click.
    """
    button = button_grid[row][col]
    card = card_data_grid[row][col]

    if button and card and button.winfo_exists():
        # print(f"Card revealed (final state): {card} at ({row},{col})") # Less verbose

        image_key = f"{card.get_suit()}_{card.get_rank_string()}"
        tk_photo_final = tk_card_face_images.get(image_key)

        if tk_photo_final:
            button.config(image=tk_photo_final)
            button.image = tk_photo_final
            # --- CHANGE: Re-enable the button for the next action ---
            button.config(state=tk.NORMAL)
            card_state_grid[row][col] = 1 # State: Face Up (Actionable)
            # print(f"Button ({row},{col}) re-enabled for action.") # Debug
        else:
            print(f"Error: Could not find pre-loaded image for key: {image_key} in on_card_revealed")
            button.config(image=tk_photo_back_scaled)
            button.image = tk_photo_back_scaled
            # Keep disabled if image loading failed? Or allow retry? For now, disable.
            button.config(state=tk.DISABLED)
            card_state_grid[row][col] = 2 # State: Disabled (Error)

    # No else needed, error handled in calling function or here


# --- Helper function to update the button image during animation ---
def _update_animation_step(button, image_to_resize_pil, target_width, target_height):
    # ... (keep existing helper function - no changes needed here) ...
    if not button.winfo_exists(): return
    target_width = max(1, target_width)
    target_height = max(1, target_height)
    try:
        resized_image_pil = image_to_resize_pil.resize((target_width, target_height), Image.Resampling.LANCZOS)
        new_tk_image = ImageTk.PhotoImage(resized_image_pil)
        button.config(image=new_tk_image)
        button.image = new_tk_image
    except Exception as e:
        if button.winfo_exists():
             # Check TclError specifically which can happen on window close during animation
             if isinstance(e, tk.TclError):
                 pass # Ignore Tcl errors likely due to widget destruction
             else:
                 print(f"Error in _update_animation_step (resizing/PhotoImage): {e}")


# --- Flip Animation Function using Loops and root.after ---
def animate_flip(button, row, col):
    # ... (keep existing animation logic - no changes needed here) ...
    card = card_data_grid[row][col]
    if not card:
        print(f"Error: No card data found for animation at ({row},{col})")
        if button.winfo_exists(): button.config(state=tk.NORMAL)
        return

    image_key = f"{card.get_suit()}_{card.get_rank_string()}"
    card_face_pil_to_grow = card_face_images_pil.get(image_key)

    if not card_face_pil_to_grow:
        print(f"Error: Could not find PIL face image for key: {image_key} to animate.")
        on_card_revealed(row, col) # Reveal instantly without animation (will re-enable)
        return

    # --- 1. Schedule Shrinking Steps ---
    for step in range(animation_steps):
        delay = (step + 1) * animation_delay
        fraction = 1.0 - (step + 1) / animation_steps
        new_width = int(scaled_width * fraction)
        root.after(delay, _update_animation_step, button, card_back_pil_scaled, new_width, scaled_height)

    # --- 2. Schedule Growing Steps ---
    base_grow_delay = animation_steps * animation_delay
    for step in range(animation_steps):
        delay = base_grow_delay + (step + 1) * animation_delay
        fraction = (step + 1) / animation_steps
        new_width = int(scaled_width * fraction)
        root.after(delay, _update_animation_step, button, card_face_pil_to_grow, new_width, scaled_height)

    # --- 3. Schedule the final reveal function call ---
    final_delay = (animation_steps * 2) * animation_delay + (animation_delay // 2)
    root.after(final_delay, on_card_revealed, row, col) # This will re-enable button


# --- MODIFIED Click Handler ---
def handle_card_click(row, col):
    """
    Called when a button is clicked.
    Determines if it's the first click (flip) or second click (action).
    """
    button = button_grid[row][col]
    card = card_data_grid[row][col]
    current_state = card_state_grid[row][col]

    if not button or not card or not button.winfo_exists():
        print(f"Warning: Clicked on invalid/empty/destroyed grid position ({row},{col})")
        return

    # --- Check State to Decide Action ---

    # State 0: Face Down - First click, initiate flip
    if current_state == 0 and button['state'] == tk.NORMAL:
        print(f"First click on ({row},{col}). Flipping card...")
        button.config(state=tk.DISABLED) # Disable *during* animation ONLY
        # card_state_grid[row][col] # State will be updated to 1 in on_card_revealed
        animate_flip(button, row, col)

    # State 1: Face Up / Actionable - Second click, initiate action
    elif current_state == 1 and button['state'] == tk.NORMAL:
        print(f"Second click on ({row},{col}). Performing action...")
        # Action function will disable the button permanently and set state to 2
        handle_card_action(row, col)

    # State 2: Action Taken / Disabled OR button is currently DISABLED (e.g., animating)
    elif current_state == 2 or button['state'] == tk.DISABLED:
        # print(f"Button ({row},{col}) is already actioned or currently busy.") # Ignored click
        pass # Do nothing

    else:
        # Should not happen with current logic, but good for debugging
        print(f"Warning: Unhandled click state for ({row},{col}) - State: {current_state}, Button State: {button['state']}")


# --- Create and place the buttons in the grid_frame ---
# ... (keep existing button creation loop, ensure command calls handle_card_click) ...
print("Creating button grid...")
for r in range(rows):
    for c in range(columns):
        if card_data_grid[r][c] is not None:
            button_bg = grid_frame.cget('bg')
            button = tk.Button(grid_frame, image=tk_photo_back_scaled,
                               # Command now handles both clicks via state check
                               command=lambda row=r, col=c: handle_card_click(row, col),
                               borderwidth=0,
                               highlightthickness=0,
                               relief=tk.FLAT,
                               bg=button_bg,
                               activebackground=button_bg,
                               # Start enabled if there's a card
                               state=tk.NORMAL if card_data_grid[r][c] else tk.DISABLED)

            button.image = tk_photo_back_scaled
            button.grid(row=r, column=c, padx=1, pady=1)
            button_grid[r][c] = button
        else:
            # Create placeholder if no card dealt here
            placeholder = tk.Frame(grid_frame,
                                   width=scaled_width,
                                   height=scaled_height,
                                   bg=grid_frame.cget('bg'))
            placeholder.grid(row=r, column=c, padx=1, pady=1)
            button_grid[r][c] = None
            card_state_grid[r][c] = 2 # Mark empty slots as 'Disabled' state


# --- Simple Grid Printout Function (Definition only) ---
def simple_print_grid(grid_to_print, title="Grid"):
    # ... (keep existing print function) ...
    print(f"\n--- Simple {title} Printout ---")
    if not grid_to_print:
        print("[Grid is empty]")
        return
    for row_idx, row in enumerate(grid_to_print):
        print(f"Row {row_idx}: ", end="")
        for item in row:
            print(f"{repr(item):<25}", end=" ")
        print()
    print("--------------------------\n")

# Example usage (optional, call when needed for debugging):
# simple_print_grid(card_data_grid, title="Card Data")
# simple_print_grid(card_state_grid, title="Card State")


# --- Start the Tkinter event loop ---
print("Starting Tkinter main loop...")
root.mainloop()

print("Window closed.")
# --- END OF FILE main.py ---