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

        # Add more player attributes as needed (e.g., inventory, health, status)
        print(f"Player initialized at position ({self._row}, {self._col})")

    @property
    def position(self):
        """ Returns the player's current (row, col) tuple. """
        return (self._row, self._col)

    def set_position(self, row, col):
        """ Updates the player's position. Add validation if needed. """
        if 0 <= row < config.ROWS and 0 <= col < config.COLUMNS:
            self._row = row
            self._col = col
            print(f"Player moved to ({self._row}, {self._col})")
            # Future: Trigger visual update of player on grid
        else:
            print(f"Error: Attempted to move player to invalid position ({row}, {col})")


    def move(self, d_row, d_col):
        """ Attempts to move the player by delta row/col. """
        new_row = self._row + d_row
        new_col = self._col + d_col
        # Basic bounds check (can add more complex collision checks later)
        if 0 <= new_row < config.ROWS and 0 <= new_col < config.COLUMNS:
            self.set_position(new_row, new_col)
            return True
        else:
            print("Move blocked: Out of bounds.")
            return False

    def is_adjacent(self, target_row, target_col):
        """ Checks if a target cell is directly adjacent (horizontally or vertically) to the player. """
        row_diff = abs(self._row - target_row)
        col_diff = abs(self._col - target_col)
        # Adjacent if exactly one coordinate differs by 1 and the other is the same
        return (row_diff == 1 and col_diff == 0) or (row_diff == 0 and col_diff == 1)

    def can_interact(self, target_row, target_col):
        """ Determines if the player can interact with the card at the target cell. """
        # RULE: Player can only interact with adjacent cards
        return self.is_adjacent(target_row, target_col)

    # --- Placeholder for future methods ---
    def perform_action_on_card(self, card, row, col, game_state_components):
         """ Placeholder: What the player does specifically when interacting. """
         print(f"Player interacting with {card} at ({row},{col})... (Logic TBD)")
         # This could eventually call functions from card_actions.py or other modules
         # based on the card type and game rules. It might need access to
         # game_state_components like grids, hand, etc.
         pass

# --- END OF FILE player.py ---