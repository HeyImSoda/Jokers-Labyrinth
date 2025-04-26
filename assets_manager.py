# --- START OF FILE assets_manager.py ---

import os
from PIL import Image, ImageOps # Added ImageOps for potential future use (like borders)
import config
import sys # For exit

def load_pil_assets():
    """Loads card back, face, dice images, and placeholder icon using PIL."""
    print("Loading PIL assets...")
    assets = {}

    # --- Basic File/Directory Checks ---
    if not os.path.exists(config.CARD_BACK_PATH):
        print(f"FATAL Error: Card back image file not found at path: {config.CARD_BACK_PATH}")
        sys.exit(f"Asset Error: Card back not found at {config.CARD_BACK_PATH}")
    if not os.path.isdir(config.CARD_FACES_PATH):
        print(f"FATAL Error: Card faces directory not found at path: {config.CARD_FACES_PATH}")
        sys.exit(f"Asset Error: Card faces directory not found at {config.CARD_FACES_PATH}")

    dice_dir_exists = os.path.isdir(config.DICE_FACES_PATH)
    if not dice_dir_exists:
        print(f"WARNING: Dice faces directory not found at path: {config.DICE_FACES_PATH}. Dice images will be unavailable.")
        # Proceed without dice if not found, combat UI will show text fallback

    # --- Load Card Back ---
    try:
        card_back_pil_original = Image.open(config.CARD_BACK_PATH).convert("RGBA") # Ensure RGBA
        original_width, original_height = card_back_pil_original.size
        scaled_width = int(original_width * config.CARD_SCALE_FACTOR)
        scaled_height = int(original_height * config.CARD_SCALE_FACTOR)
        # Ensure minimum size
        scaled_width = max(1, scaled_width)
        scaled_height = max(1, scaled_height)
        assets["card_back_pil_scaled"] = card_back_pil_original.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        assets["width"] = scaled_width
        assets["height"] = scaled_height
        print(f"- Card back PIL loaded and scaled to {scaled_width}x{scaled_height}")
    except Exception as e:
        sys.exit(f"FATAL ERROR loading card back PIL image: {e}")

    # --- Load Card Faces ---
    assets["pil_faces_scaled"] = {}
    loaded_card_faces = 0
    if os.path.isdir(config.CARD_FACES_PATH):
        for filename in os.listdir(config.CARD_FACES_PATH):
            # Process only PNG files, case-insensitive
            if filename.lower().endswith(".png"):
                image_path = os.path.join(config.CARD_FACES_PATH, filename)
                # Create key: clubs_ace, hearts_king, red_joker, etc.
                image_key = filename.lower().replace('.png', '')
                try:
                    img_pil_original = Image.open(image_path).convert("RGBA") # Ensure RGBA
                    img_pil_scaled = img_pil_original.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                    assets["pil_faces_scaled"][image_key] = img_pil_scaled
                    loaded_card_faces += 1
                except Exception as e:
                    print(f"Warning: Could not load/process card face '{filename}': {e}")
        print(f"- Loaded {loaded_card_faces} card face PIL images.")
    else:
        # This case should have been caught by the exit check earlier, but good practice
        print(f"- Card faces directory not found, skipping face loading.")


    # --- Load Dice Faces and Icon (PIL only) ---
    assets["pil_dice_scaled"] = {} # Use this dict for BOTH dice and icon
    loaded_dice_faces = 0
    # Mapping: key (int or 'icon') -> filename
    dice_filenames = {
        1: "die_one.png", 2: "die_two.png", 3: "die_three.png",
        4: "die_four.png", 5: "die_five.png", 6: "die_six.png",
        # --- ADDED ICON MAPPING ---
        'icon': "die_isometric_big.png"
        # --------------------------
    }
    print(f"Attempting to load dice and icon from directory: {config.DICE_FACES_PATH}")
    if dice_dir_exists:
        first_die_found = False # To get reference size for scaling
        dice_ref_w, dice_ref_h = 50, 50 # Default ref size if no dice found but icon exists

        for key, filename in dice_filenames.items(): # Key can be int or 'icon'
            image_path = os.path.join(config.DICE_FACES_PATH, filename)
            print(f"  Checking for asset key '{key}': expecting file '{filename}' at '{image_path}'")
            if os.path.exists(image_path):
                print(f"    File FOUND: {image_path}")
                try:
                    img_pil_original = Image.open(image_path).convert("RGBA") # Ensure RGBA
                    print(f"      Opened PIL image for key '{key}' successfully (Size: {img_pil_original.size}).")

                    # Get reference size ONLY from the first actual die (integer key)
                    if isinstance(key, int) and not first_die_found:
                        dice_ref_w, dice_ref_h = img_pil_original.size
                        first_die_found = True
                        print(f"      Set dice reference size based on '{filename}': {dice_ref_w}x{dice_ref_h}")

                    # Apply scaling based on DICE_SCALE_FACTOR and ref size
                    # Ensure minimum dimensions after scaling
                    dw = max(1, int(dice_ref_w * config.DICE_SCALE_FACTOR))
                    dh = max(1, int(dice_ref_h * config.DICE_SCALE_FACTOR))

                    # Scale all dice/icon based on the *first die's* scaled size for consistency in the combat window
                    img_pil_scaled = img_pil_original.resize((dw, dh), Image.Resampling.LANCZOS)

                    # Store using the original key (integer or 'icon')
                    assets["pil_dice_scaled"][key] = img_pil_scaled

                    print(f"      Resized to {dw}x{dh} and stored PIL image for key '{key}' in assets['pil_dice_scaled'].")
                    if isinstance(key, int): # Only count actual dice faces
                        loaded_dice_faces += 1
                except Exception as e:
                    print(f"    ERROR processing file '{filename}' for key '{key}': {e}")
                    # Store None if loading failed
                    assets["pil_dice_scaled"][key] = None
            else:
                print(f"    WARNING: File NOT FOUND for key '{key}': {image_path}")
                 # Store None if file not found
                assets["pil_dice_scaled"][key] = None

        print(f"- Loaded {loaded_dice_faces} dice face PIL images (plus potentially icon).")
        # Log which specific keys were successfully loaded (i.e., have a non-None value)
        # Convert keys to string for sorting in this print statement
        final_keys = sorted([str(k) for k, v in assets.get('pil_dice_scaled', {}).items() if v is not None])
        print(f"- Final keys with valid images in assets['pil_dice_scaled']: {final_keys}")
        # Check specifically if icon was loaded successfully
        if 'icon' in assets.get('pil_dice_scaled', {}) and assets['pil_dice_scaled']['icon'] is not None:
             print("- Icon image loaded successfully.")
        else:
             print("- WARNING: Icon image ('icon' key) was NOT loaded successfully.")

    else:
         print(f"- Dice face directory not found or inaccessible, SKIPPING dice/icon image loading.")



    # --- Return PIL assets and dimensions ---
    # Ensure the dice dict exists even if empty
    if "pil_dice_scaled" not in assets:
        assets["pil_dice_scaled"] = {}
        print(f"--- Returning assets. Dice keys: []")
    else:
        # *** FIX HERE: Convert keys to strings before sorting for printing ***
        print(f"--- Returning assets. Dice keys: {sorted([str(k) for k in assets['pil_dice_scaled'].keys()])}")
        # ********************************************************************

    return assets

# --- END OF FILE assets_manager.py ---