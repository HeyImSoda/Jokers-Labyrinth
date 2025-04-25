# --- START OF FILE assets_manager.py ---

import os
# No tkinter needed here anymore!
from PIL import Image # Keep PIL
import config # Import settings

def load_pil_assets(): # Renamed for clarity
    """Loads card back and face images using PIL, applies scaling, and returns PIL assets."""
    print("Loading PIL assets...")

    # --- Basic File/Directory Checks ---
    if not os.path.exists(config.CARD_BACK_PATH):
        print(f"Error: Card back image file not found at path: {config.CARD_BACK_PATH}")
        exit()
    if not os.path.isdir(config.CARD_FACES_PATH):
        print(f"Error: Card faces directory not found at path: {config.CARD_FACES_PATH}")
        exit()

    # --- Load Card Back (PIL only) ---
    try:
        card_back_pil_original = Image.open(config.CARD_BACK_PATH)
        original_width, original_height = card_back_pil_original.size

        scaled_width = int(original_width * config.CARD_SCALE_FACTOR)
        scaled_height = int(original_height * config.CARD_SCALE_FACTOR)

        card_back_pil_scaled = card_back_pil_original.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        print(f"- Card back PIL loaded and scaled to {scaled_width}x{scaled_height}")

    except Exception as e:
        print(f"FATAL ERROR loading card back PIL image: {e}")
        exit()

    # --- Load Card Faces (PIL only) ---
    pil_faces_scaled = {} # Scaled PIL images
    loaded_count = 0

    if os.path.isdir(config.CARD_FACES_PATH):
        for filename in os.listdir(config.CARD_FACES_PATH):
            if filename.lower().endswith(".png"):
                image_path = os.path.join(config.CARD_FACES_PATH, filename)
                image_key = filename.lower().replace('.png', '')
                try:
                    img_pil_original = Image.open(image_path)
                    img_pil_scaled = img_pil_original.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                    pil_faces_scaled[image_key] = img_pil_scaled # Store scaled PIL
                    loaded_count += 1
                except Exception as e:
                    print(f"Warning: Could not load/process PIL face {filename}: {e}")
        print(f"- Loaded {loaded_count} card face PIL images.")
    else:
        print(f"Error: Card faces directory invalid: {config.CARD_FACES_PATH}")
        exit()

    # --- Return PIL assets and dimensions ---
    return {
        "card_back_pil_scaled": card_back_pil_scaled,
        "pil_faces_scaled": pil_faces_scaled,
        "width": scaled_width,
        "height": scaled_height
    }

# --- END OF FILE assets_manager.py ---