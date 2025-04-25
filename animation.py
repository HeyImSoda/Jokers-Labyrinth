# --- START OF FILE animation.py ---

import tkinter as tk
from PIL import Image, ImageTk
import config # Import settings

def _update_animation_step(button, image_to_resize_pil, target_width, target_height):
    """ Helper: Updates button image to a specific size during animation. """
    if not button.winfo_exists(): return # Check if button still exists
    target_width = max(1, target_width) # Ensure width is at least 1 pixel
    target_height = max(1, target_height) # Ensure height is at least 1
    try:
        # Add check if image_to_resize_pil is valid
        if image_to_resize_pil is None:
             print(f"Error in _update_animation_step: Attempted to resize a None image.")
             return
        resized_image_pil = image_to_resize_pil.resize((target_width, target_height), Image.Resampling.LANCZOS)
        new_tk_image = ImageTk.PhotoImage(resized_image_pil)
        button.config(image=new_tk_image)
        button.image = new_tk_image # IMPORTANT: Keep reference
    except Exception as e:
        if button.winfo_exists():
             if isinstance(e, tk.TclError): pass
             else: print(f"Error in _update_animation_step: {e}")

def animate_flip(root, button, card, assets, on_reveal_callback, row, col):
    """
    Simulates a flip using scheduled image updates.
    Args:
        root: The main Tkinter window (for root.after).
        button: The tk.Button widget to animate.
        card: The Card object being flipped.
        assets: Dictionary containing loaded image assets and dimensions.
        on_reveal_callback: Function to call after animation (takes row, col).
        row, col: Grid coordinates of the card.
    """
    if not card:
        print(f"Error: No card data for animation at ({row},{col})")
        if button.winfo_exists(): button.config(state=tk.NORMAL)
        return

    suit_key = str(card.get_suit()).lower()
    rank_key = str(card.get_rank_string()).lower()
    image_key = f"{suit_key}_{rank_key}"

    # --- CORRECTED KEY LOOKUPS ---
    card_face_pil_to_grow = assets["pil_faces_scaled"].get(image_key) # Use "pil_faces_scaled"
    card_back_pil_scaled = assets["card_back_pil_scaled"]           # Use "card_back_pil_scaled"
    # -----------------------------

    # --- Check if images were found ---
    if not card_back_pil_scaled:
        print(f"FATAL Error in animate_flip: Scaled PIL card back not found in assets.")
        # Cannot proceed with animation without back image
        if on_reveal_callback: on_reveal_callback(row, col) # Reveal instantly
        return
    if not card_face_pil_to_grow:
        print(f"Error in animate_flip: Could not find PIL face image for key: {image_key} to animate.")
        # Cannot proceed with grow phase, reveal instantly
        if on_reveal_callback: on_reveal_callback(row, col)
        return
    # ----------------------------------

    scaled_width = assets["width"]
    scaled_height = assets["height"]


    # --- 1. Schedule Shrinking Steps (Using CORRECTED card_back_pil_scaled) ---
    for step in range(config.ANIMATION_STEPS):
        delay = (step + 1) * config.ANIMATION_DELAY
        fraction = 1.0 - (step + 1) / config.ANIMATION_STEPS
        new_width = int(scaled_width * fraction)
        root.after(delay, _update_animation_step, button, card_back_pil_scaled, new_width, scaled_height) # Pass correct back image

    # --- 2. Schedule Growing Steps (Using CORRECTED card_face_pil_to_grow) ---
    base_grow_delay = config.ANIMATION_STEPS * config.ANIMATION_DELAY
    for step in range(config.ANIMATION_STEPS):
        delay = base_grow_delay + (step + 1) * config.ANIMATION_DELAY
        fraction = (step + 1) / config.ANIMATION_STEPS
        new_width = int(scaled_width * fraction)
        root.after(delay, _update_animation_step, button, card_face_pil_to_grow, new_width, scaled_height) # Pass correct face image

    # --- 3. Schedule the final reveal function call ---
    final_delay = (config.ANIMATION_STEPS * 2) * config.ANIMATION_DELAY + (config.ANIMATION_DELAY // 2)
    if on_reveal_callback:
        root.after(final_delay, on_reveal_callback, row, col)

# --- END OF FILE animation.py ---