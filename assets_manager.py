# --- START OF FILE assets_manager.py ---

import os
from PIL import Image
import config # Import settings

def load_pil_assets():
    """Loads card back, face, and dice images using PIL, applies scaling, and returns PIL assets."""
    print("Loading PIL assets...")
    assets = {}

    # --- Basic File/Directory Checks ---
    if not os.path.exists(config.CARD_BACK_PATH): exit(f"Error: Card back image file not found at path: {config.CARD_BACK_PATH}")
    if not os.path.isdir(config.CARD_FACES_PATH): exit(f"Error: Card faces directory not found at path: {config.CARD_FACES_PATH}")
    if not os.path.isdir(config.DICE_FACES_PATH): print(f"Warning: Dice faces directory not found at path: {config.DICE_FACES_PATH}") # Warning instead of exit

    # --- Load Card Back (PIL only) ---
    try:
        card_back_pil_original = Image.open(config.CARD_BACK_PATH)
        original_width, original_height = card_back_pil_original.size
        scaled_width = int(original_width * config.CARD_SCALE_FACTOR)
        scaled_height = int(original_height * config.CARD_SCALE_FACTOR)
        assets["card_back_pil_scaled"] = card_back_pil_original.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        assets["width"] = scaled_width  # Store card dimensions
        assets["height"] = scaled_height
        print(f"- Card back PIL loaded and scaled to {scaled_width}x{scaled_height}")
    except Exception as e:
        exit(f"FATAL ERROR loading card back PIL image: {e}")

    # --- Load Card Faces (PIL only) ---
    assets["pil_faces_scaled"] = {}
    loaded_card_faces = 0
    if os.path.isdir(config.CARD_FACES_PATH):
        for filename in os.listdir(config.CARD_FACES_PATH):
            if filename.lower().endswith(".png"):
                image_path = os.path.join(config.CARD_FACES_PATH, filename)
                image_key = filename.lower().replace('.png', '')
                try:
                    img_pil_original = Image.open(image_path)
                    img_pil_scaled = img_pil_original.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                    assets["pil_faces_scaled"][image_key] = img_pil_scaled
                    loaded_card_faces += 1
                except Exception as e:
                    print(f"Warning: Could not load/process card face {filename}: {e}")
        print(f"- Loaded {loaded_card_faces} card face PIL images.")

    # --- Load Dice Faces (PIL only) ---
    assets["pil_dice_scaled"] = {}
    loaded_dice_faces = 0
    # --- Define expected dice filenames ---
    dice_filenames = {
        1: "die_one.png", 2: "die_two.png", 3: "die_three.png",
        4: "die_four.png", 5: "die_five.png", 6: "die_six.png"
    }
    # --------------------------------------
    if os.path.isdir(config.DICE_FACES_PATH):
        for value, filename in dice_filenames.items():
            image_path = os.path.join(config.DICE_FACES_PATH, filename)
            if os.path.exists(image_path):
                try:
                    img_pil_original = Image.open(image_path)
                    # Apply optional scaling
                    ow, oh = img_pil_original.size
                    dw = int(ow * config.DICE_SCALE_FACTOR)
                    dh = int(oh * config.DICE_SCALE_FACTOR)
                    img_pil_scaled = img_pil_original.resize((max(1, dw), max(1, dh)), Image.Resampling.LANCZOS)
                    assets["pil_dice_scaled"][value] = img_pil_scaled # Store by integer value
                    loaded_dice_faces += 1
                except Exception as e:
                    print(f"Warning: Could not load/process dice face {filename}: {e}")
            else:
                print(f"Warning: Dice face image not found: {image_path}")
        print(f"- Loaded {loaded_dice_faces} dice face PIL images.")
    else:
         print(f"- Dice face directory not found, skipping dice image loading.")


    # --- Return PIL assets and dimensions ---
    return assets

# --- END OF FILE assets_manager.py ---