# --- START OF FILE player.py ---

import config

class Player:
    """ Represents the player character in the game. """

    def __init__(self, start_row, start_col):
        """ Initializes the player at a starting position. """
        if not (0 <= start_row < config.ROWS and 0 <= start_col < config.COLUMNS):
            print(f"Warning: Invalid start position ({start_row}, {start_col}). Defaulting to center.")
            self._row = config.ROWS // 2
            self._col = config.COLUMNS // 2
        else:
            self._row = start_row
            self._col = start_col

        self.suit = None # Player's associated suit (e.g., "spades") - set in main.py
        self._skip_next_turn = False # Flag for King loss effect

        print(f"Player initialized at position ({self._row}, {self._col})")

    @property
    def position(self):
        return (self._row, self._col)

    def set_position(self, row, col):
        if 0 <= row < config.ROWS and 0 <= col < config.COLUMNS:
            self._row = row
            self._col = col
            print(f"Player moved to ({self._row}, {self._col})")
            # TODO: Trigger visual update of player on grid
        else:
            print(f"Error: Attempted to move player to invalid position ({row}, {col})")

    def move(self, d_row, d_col, card_data_grid): # Pass card_data_grid for collision checks
        """ Attempts to move the player by delta row/col. """
        new_row = self._row + d_row
        new_col = self._col + d_col

        # Check bounds
        if not (0 <= new_row < config.ROWS and 0 <= new_col < config.COLUMNS):
             print("Move blocked: Out of bounds.")
             return False

        # Check collision (basic: can't move into an unrevealed/uncleared card space)
        # More complex rules needed based on rulebook (move onto revealed/blank)
        target_card = card_data_grid[new_row][new_col]
        # Add check for state grid as well - can only move to ACTION_TAKEN (empty) or FACE_UP?

        # Simplified check for now: just allow if in bounds
        self.set_position(new_row, new_col)
        return True


    def is_adjacent(self, target_row, target_col):
        row_diff = abs(self._row - target_row)
        col_diff = abs(self._col - target_col)
        return (row_diff == 1 and col_diff == 0) or (row_diff == 0 and col_diff == 1)

    def can_interact(self, target_row, target_col):
        # RULE: Player can only interact with adjacent cards (Reveal or Fight)
        return self.is_adjacent(target_row, target_col)

    # --- Skip Turn Logic ---
    def set_skip_turn(self, skip):
        """Sets or clears the skip turn flag."""
        self._skip_next_turn = bool(skip)
        if self._skip_next_turn:
            print("Player flag set: Skip next turn.")

    def should_skip_turn(self):
        """Checks if the player should skip their upcoming turn."""
        return self._skip_next_turn

    def clear_skip_turn_flag(self):
        """Resets the skip turn flag (usually called after the skipped turn)."""
        self._skip_next_turn = False
    # ----------------------

    # --- Placeholder ---
    def perform_action_on_card(self, card, row, col, game_state_components):
         print(f"Player interacting with {card} at ({row},{col})... (Logic TBD)")
         pass

# --- END OF FILE player.py ---