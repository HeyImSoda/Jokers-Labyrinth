import tkinter as tk
from PIL import Image, ImageTk
import os
import time
import card_logic
from card_logic import Deck

# --- Configuration ---
card_back_path = r"C:\Users\stell\Desktop\Python Files\Jokers_Labyrinth\assets\card_back.png"
# Define the path for the card front image (Ace of Spades)
IMAGE_FRONT_PATH = r"C:\Users\stell\Desktop\Python Files\Jokers_Labyrinth\assets\card_Faces\clubs_ace.png"
rows = 7
columns = 7
animation_delay = 30 # Milliseconds between animation steps
animation_steps = 6     # How many steps to shrink (more = smoother but slower)
# ---

# --- Basic File Checks ---
if not os.path.exists(card_back_path):
    print(f"Error: Card back image file not found at path: {card_back_path}")
    exit()
if not os.path.exists(IMAGE_FRONT_PATH):
    print(f"Error: Card front image file (Ace) not found at path: {IMAGE_FRONT_PATH}")
    exit()
# ---

# --- Create the main window ---
root = tk.Tk()
root.title("The Joker's Labyrinth (4 Player Advanced)")

# --- Load Images ---
try:
    # Load the card back image (Pillow format)
    card_back = Image.open(card_back_path)
    original_width, original_height = card_back.size

    # Load the card front image (Ace of Spades - Pillow format)
    card_front = Image.open(IMAGE_FRONT_PATH)
    # --- IMPORTANT: Resize front image to match back image size ---
    # This ensures the card doesn't suddenly change size when flipped
    card_front = card_front.resize((original_width, original_height), Image.Resampling.LANCZOS)
    # ---

    # Convert images to Tkinter format
    tk_photo_back_original = ImageTk.PhotoImage(card_back)
    tk_photo_front = ImageTk.PhotoImage(card_front) # Keep reference to the front image

except Exception as e:
    print(f"An error occurred while loading images: {e}")
    root.destroy()
    exit()

suits = ["hearts", "diamonds", "clubs", "spades"]
ranks_string = ["two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "jack", "queen", "king", "ace"]
# It's often helpful if the integer ranks align with indices, but we can use the 1-13 values too
ranks_int = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13] # Values 1-13 as requested

# --- Card Class ---
class Card:
    # FIX 1: Assign arguments directly in __init__
    def __init__(self, suit=None, rank=None, rank_string=None):
        self.flipped = False
        self.suit = suit  # Assign the passed suit
        self.rank = rank  # Assign the passed rank value
        self.rank_string = rank_string # Assign the passed rank string

    def get_rank(self):
        return self.rank

    def get_rank_string(self):
        return self.rank_string

    def get_suit(self):
        return self.suit

    def get_color(self):
        return "red" if self.suit in ["hearts", "diamonds"] else "black"

    # Setters are less common in Python if using __init__ properly, but okay to keep
    def set_rank(self, value):
        self.rank = value

    def set_rank_string(self, value):
        self.rank_string = value

    def set_suit(self, suit):
        self.suit = suit

    # Add a __repr__ for easier printing/debugging
    def __repr__(self):
        return f"{self.rank_string.capitalize()} of {self.suit.capitalize()}"


# FIX 3: Initialize game_deck as an empty 1D list
game_deck = []

# FIX 2: Loop correctly using the values and indices appropriately
for suit_value in suits:  # Iterate through the actual suit strings
    # Iterate through the *indices* of the ranks lists
    for i in range(len(ranks_int)):
        rank_int_value = ranks_int[i]      # Get the integer rank for this index
        rank_string_value = ranks_string[i] # Get the string rank for this index

        # Create the card using the correct values for this iteration
        card = Card(suit=suit_value, rank=rank_int_value, rank_string=rank_string_value)
        game_deck.append(card) # Append the created card object to the 1D list
        
        # game_deck[r][c] = Card
        # game_deck[r][c].set_rank(ranks_int[c]) 
        # game_deck[r][c].set_suit(game_deck.get_card(index).split(",")[1]) 
        # index += 1



# game_deck = [[None for _ in range(columns)] for _ in range(rows)]
print(f"Buttons initialized: {game_deck}")
# Optional: Track if a card is flipped (useful for more complex logic)
# card_is_flipped = [[False for _ in range(columns)] for _ in range(rows)]





# --- Function called AFTER the animation finishes ---
def on_card_revealed(row, col):
    """
    Called when a card's flip animation completes.
    Sets the final image to the Ace of Spades and leaves button disabled.
    Add your game logic here.
    """
    revealed_Card_path = "e"
    print(f"Card revealed: Row={row}, Col={col}")
    button = game_deck[row][col]
    if button: # Make sure button exists

        # --- Set the final image to the Ace of Spades ---
        button.config(image=tk_photo_front)
        button.image = revealed_Card_path # Keep reference to the new image
        # ---

        # Update state if tracking
        # card_is_flipped[row][col] = True

        # --- YOUR ADDITIONAL LOGIC GOES HERE ---
        # Example:
        # - Check if this is the first or second card flipped in a pair
        # - Check for a match
        # - Update score, etc.
        # --- END YOUR LOGIC ---

        # Keep the button disabled after flipping to the Ace
        # You might change this based on your game rules (e.g., flip back if no match)
        button.config(state=tk.DISABLED)
        # print(game_deck)

    else:
        print(f"Error accessing button at ({row},{col}) in on_card_revealed")


# --- Helper function to update the button image during animation ---
def _update_animation_step(button, image_to_resize, target_width, target_height):
    """
    Updates the button's image to a specific size.
    Called by root.after during the animation sequence.
    """
    # Check if the button widget still exists (window might have been closed)
    if not button.winfo_exists():
        return

    # Ensure width is at least 1 pixel
    target_width = max(1, target_width)

    try:
        # Resize the provided Pillow image
        resized_image = image_to_resize.resize((target_width, target_height), Image.Resampling.LANCZOS)
        new_tk_image = ImageTk.PhotoImage(resized_image)

        # Update the button's image
        button.config(image=new_tk_image)
        # IMPORTANT: Keep a reference to the new image on the button
        # to prevent it from being garbage collected by Python.
        button.image = new_tk_image
    except Exception as e:
        print(f"Error resizing/updating image in _update_animation_step: {e}")


# --- Flip Animation Function using Loops and root.after ---
def animate_flip(button, row, col):
    """
    Simulates a flip using scheduled image updates:
    1. Shrinks the card back horizontally.
    2. Switches to the card front (shrunk).
    3. Grows the card front horizontally.
    Uses root.after within loops to schedule steps without recursion or lambda.
    Calls on_card_revealed when the animation completes.
    """
    # --- Schedule Shrinking Steps (Card Back) ---
    for step in range(animation_steps):
        # Calculate delay for this step
        delay = (step + 1) * animation_delay
        # Calculate the width for this shrinking step
        fraction = 1.0 - (step + 1) / animation_steps
        new_width = int(original_width * fraction)

        # Schedule the update using the helper function
        root.after(delay, _update_animation_step, button, card_back, new_width, original_height)

    # --- Schedule Growing Steps (Card Front) ---
    # Start growing *after* all shrinking steps are scheduled
    base_grow_delay = animation_steps * animation_delay

    for step in range(animation_steps):
        # Calculate delay for this step (starts after shrinking finishes)
        delay = base_grow_delay + (step + 1) * animation_delay
        # Calculate the width for this growing step
        fraction = (step + 1) / animation_steps
        new_width = int(original_width * fraction)

        # Schedule the update using the helper function, but with the card_front image
        root.after(delay, _update_animation_step, button, card_front, new_width, original_height)

    # --- Schedule the final reveal function call ---
    # This should happen after the last growing step completes
    final_delay = (animation_steps * 2) * animation_delay + (animation_delay // 2) # Small buffer
    root.after(final_delay, on_card_revealed, row, col)


# --- Click Handler ---
def handle_card_click(row, col):
    """
    Called when a button is clicked. Starts the animation.
    """
    print(f"Button clicked: Row={row}, Col={col}") # Debug print
    button = game_deck[row][col]

    # Prevent clicking again while animating or if already flipped
    button.config(state=tk.DISABLED)

    # Start the flip animation (shrinking phase)
    animate_flip(button, row, col)


# --- Create and place the game_deck in a grid ---
for row in range(rows):
    for column in range(columns):
        # Create a Button widget with the card back image initially
        button = tk.Button(root, image=tk_photo_back_original,
                           command=lambda row=row, col=column: handle_card_click(row, col),
                           borderwidth=0,
                           highlightthickness=0,
                           activebackground=root.cget('bg'))

        # Store the initial image reference on the button itself
        button.image = tk_photo_back_original

        # Place the button in the grid
        button.grid(row=row, column=column, padx=1, pady=1)

        # Store the button object in our 2D list
        game_deck[row][column] = button


# --- Start the Tkinter event loop ---
root.mainloop()

print("Window closed.")