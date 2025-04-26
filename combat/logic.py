# --- START OF FILE combat/logic.py ---

# Needs Card definition if type hinting or checking card properties
# from card_logic import Card # Assuming card_logic.py is at the project root

def get_card_combat_value(card):
    """Helper to get the combat value (Q=12, K=13, Num=Value, else 0)."""
    if not card: return 0
    rank = card.get_rank()
    if rank == 12: return 12
    if rank == 13: return 13
    if rank is not None and 2 <= rank <= 10: return rank
    return 0 # Default for Aces, Jokers, etc. (and invalid cards)

def calculate_combat_parameters(attacker_card, defender_card):
    """Calculates attacker/defender values, difference, and number of dice."""
    attacker_total = get_card_combat_value(attacker_card)
    defender_total = get_card_combat_value(defender_card)
    difference = abs(attacker_total - defender_total) # Absolute difference for dice count

    num_diff_dice = 0
    if attacker_total > defender_total:
        num_diff_dice = 0 # Automatic win case handled before rolling
    elif difference <= 1: num_diff_dice = 2
    elif difference <= 3: num_diff_dice = 3
    elif difference <= 6: num_diff_dice = 4
    elif difference <= 8: num_diff_dice = 5
    else: num_diff_dice = 6 # 9+ difference

    return {
        "attacker_total": attacker_total,
        "defender_total": defender_total,
        "difference": difference, # Store absolute difference
        "num_diff_dice": num_diff_dice,
    }

def check_combat_win_condition(diff_dice_rolls, danger_die_roll, num_diff_dice):
    """Determines if combat is won based on dice rolls."""
    if danger_die_roll is None: # Safety check
        print("  Warning: Danger die was not rolled. Assuming loss.")
        return False
    if num_diff_dice > 0 and danger_die_roll in diff_dice_rolls:
        print(f"  Danger die ({danger_die_roll}) matches a difference roll. LOSS!")
        return False
    else:
        print(f"  Danger die ({danger_die_roll}) does not match difference rolls. WIN!")
        return True

# --- END OF FILE combat/logic.py ---