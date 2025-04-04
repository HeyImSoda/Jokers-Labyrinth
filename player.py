# player.py
import pygame
from constants import *
from card import Card, Deck # Import Deck as well

class Player:
    """Represents a player in the game."""
    def __init__(self, player_id, jack_suit, color, card_images_dict):
        self.id = player_id
        self.jack_suit = jack_suit # Store suit for comparison
        # Player's Jack card also needs the images dict (though maybe not displayed directly often)
        self.jack_card = Card(jack_suit, "Jack", card_images_dict)
        self.color = color
        # Initialize hand Deck with the images dict and 'empty' mode
        self.hand = Deck(card_images_dict, game_mode="empty")

        self.position = (-1, -1) # Grid position (row, col), -1 means off-board initially
        self.token_rect = pygame.Rect(0, 0, PLAYER_TOKEN_RADIUS * 2, PLAYER_TOKEN_RADIUS * 2)
        self.actions_left = 0
        self.is_turn = False
        self.jokers_found = 0
        # Add other status effects as needed (e.g., self.in_debt for advanced)
        self.can_reroll = False # For King ability tracking

    def update_token_position(self, board_offset_x, board_offset_y):
        """Calculates screen pixel position for the player's token based on grid position."""
        if self.position != (-1, -1):
            row, col = self.position
            # Calculate center based on CARD size and MARGIN
            center_x = board_offset_x + col * (CARD_WIDTH + GRID_MARGIN) + GRID_MARGIN + CARD_WIDTH // 2
            center_y = board_offset_y + row * (CARD_HEIGHT + GRID_MARGIN) + GRID_MARGIN + CARD_HEIGHT // 2
            self.token_rect.center = (center_x, center_y)
        else:
            # Default position if off-board (e.g., corner of info panel)
             info_panel_x_start = BOARD_AREA_WIDTH + board_offset_x
             self.token_rect.topleft = (info_panel_x_start + 10 + self.id * 30, 10) # Position in info panel

    def draw_token(self, surface):
        """Draws the player's circular token on the screen."""
        # Draw the main token circle
        pygame.draw.circle(surface, self.color, self.token_rect.center, PLAYER_TOKEN_RADIUS)
        # Add outline if it's this player's turn
        if self.is_turn:
            pygame.draw.circle(surface, WHITE, self.token_rect.center, PLAYER_TOKEN_RADIUS + 1, 2) # Slightly larger outline
        # Optional: Draw player number inside
        # font = pygame.font.Font(None, 18)
        # text = font.render(str(self.id + 1), True, BLACK)
        # text_rect = text.get_rect(center=self.token_rect.center)
        # surface.blit(text, text_rect)


    def draw_hand(self, surface, hand_area_rect):
        """Draws the player's hand cards in an overlapping layout."""
        start_x = hand_area_rect.left + 10
        card_spacing = -int(CARD_WIDTH * 0.4)  # Overlap effect
        y_pos = hand_area_rect.centery - CARD_HEIGHT // 2  # Center vertically in hand area

        for i, card in enumerate(self.hand.cards):
            card.is_face_up = True  # Cards in hand are always face up
            if card.image_face:
                temp_image = pygame.transform.scale(card.image_face, (CARD_WIDTH, CARD_HEIGHT))
                card_rect = temp_image.get_rect()
                card_rect.topleft = (start_x + i * card_spacing, y_pos)

                # Draw the card
                surface.blit(temp_image, card_rect)

                # Highlight the selected card
                if card == self.hand.cards[0]:  # Example: Highlight the first card
                    pygame.draw.rect(surface, GOLD, card_rect, 3)


    def add_card_to_hand(self, card):
        """Adds a card to the player's hand and checks for Jokers."""
        if card:
            self.hand.add_card(card)
            print(f"Player {self.id+1} received: {card}")
            if card.card_type == TYPE_JOKER:
                self.jokers_found += 1
                print(f"Player {self.id+1} found a Joker! Total: {self.jokers_found}")
        else:
             print(f"Warning: Tried to add 'None' card to Player {self.id+1}'s hand.")


    def check_win_condition(self):
         """Checks if the player has met the win condition (Standard: 2 Jokers)."""
         return self.jokers_found >= 2

    def get_adjacent_positions(self, include_diagonals=False):
        """Gets valid adjacent grid positions (orthogonally by default)."""
        if self.position == (-1,-1): return [] # Cannot be adjacent if off board

        row, col = self.position
        adj = []
        # Orthogonal moves
        potential = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        # Diagonal moves (only if include_diagonals is True, e.g., for Ace reveal)
        if include_diagonals:
            potential.extend([(row - 1, col - 1), (row - 1, col + 1),
                              (row + 1, col - 1), (row + 1, col + 1)])

        # Filter for valid grid coordinates
        for r, c in potential:
            if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                adj.append((r, c))
        return adj

    def can_move_to(self, target_pos, board):
        """Checks if the player can legally move to the target grid position."""
        if target_pos not in self.get_adjacent_positions():
             # print(f"DEBUG: {target_pos} not adjacent to {self.position}")
             return False # Not adjacent

        target_card = board.get_card_at(target_pos[0], target_pos[1])

        # Can always move to an empty space
        if target_card is None:
             return True

        # Can move onto revealed cards, EXCEPT hostile NPCs (unless fighting)
        if target_card.is_face_up:
             # Check for hostile NPCs (Standard rules: Queen/King of different suit)
             is_hostile_npc = (target_card.card_type in [TYPE_QUEEN, TYPE_KING] and
                                target_card.suit != self.jack_suit)
             if is_hostile_npc:
                  # print(f"DEBUG: Cannot move onto Hostile {target_card.rank} at {target_pos} without fighting.")
                  return False # Blocked by hostile NPC
             else:
                  return True # Can move onto revealed friendly NPCs, Equipment, Ace, Hazard (to fight)
        else:
            # print(f"DEBUG: Cannot move onto face-down card at {target_pos}")
            return False # Cannot move onto face-down cards directly

    def can_reveal(self, target_pos, board):
        """Checks if the player can reveal the card at the target grid position."""
        if target_pos not in self.get_adjacent_positions():
             return False
        target_card = board.get_card_at(target_pos[0], target_pos[1])
        # Can only reveal if a card exists and it's face-down
        return target_card is not None and not target_card.is_face_up

    def can_fight(self, target_pos, board):
         """Checks if the player can initiate a fight with the card at the target position."""
         if target_pos not in self.get_adjacent_positions():
             return False
         target_card = board.get_card_at(target_pos[0], target_pos[1])

         # Can only fight revealed cards
         if target_card and target_card.is_face_up:
              # Standard mode: Fight Hazards or Hostile NPCs or Jokers
              is_hostile_npc = (target_card.card_type in [TYPE_QUEEN, TYPE_KING] and
                                target_card.suit != self.jack_suit)
              if target_card.card_type == TYPE_HAZARD or is_hostile_npc or target_card.card_type == TYPE_JOKER:
                   return True
         return False

    def has_card_rank(self, rank):
         """Checks if the player has a card of a specific rank in hand."""
         for card in self.hand.cards:
              if card.rank == rank:
                   return True
         return False

    def use_king_reroll(self):
         """Handles the King's reroll ability."""
         # Simple check for now, assumes player confirmed they have a King
         # In a full implementation, might need to track which King if multiple
         print("Player used King's reroll ability!")
         # Need logic in the combat phase to allow the actual reroll
         self.can_reroll = False # Mark ability as used for this combat potentially