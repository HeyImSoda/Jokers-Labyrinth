import pygame
from constants import *
from card import Card, Deck # Import both

class Board:
    """Manages the 7x7 game grid and the main deck/discard pile."""
    def __init__(self, card_images_dict):
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.all_cards = pygame.sprite.Group() # Group for drawing all card sprites on board
        board_width_pixels = GRID_COLS * CARD_WIDTH + (GRID_COLS + 1) * GRID_MARGIN
        board_height_pixels = GRID_ROWS * CARD_HEIGHT + (GRID_ROWS + 1) * GRID_MARGIN
        self.board_rect = pygame.Rect(0, 0, board_width_pixels, board_height_pixels) # Positioned in main.py

        self.card_images = card_images_dict
        if not isinstance(self.card_images, dict):
            print("ERROR: Board initialized with invalid card_images_dict.")
            self.card_images = {} # Prevent crashing

        self.deck = Deck(self.card_images, game_mode="empty") # Start empty, setup fills it
        self.discard_pile = Deck(self.card_images, game_mode="empty")

    def setup_board(self, game_mode="standard"):
        """Sets up the board grid and deck for the specified game mode."""
        print(f"Setting up board for game mode: {game_mode}...")
        if not self.card_images:
             print("ERROR: Cannot setup board, card images dictionary missing.")
             return None # Indicate failure

        self.deck = Deck(self.card_images, game_mode=game_mode)
        self.all_cards.empty()
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.discard_pile = Deck(self.card_images, game_mode="empty")

        if game_mode == "standard":
            jacks_for_players = [Card(suit, "Jack", self.card_images) for suit in SUITS]
            center_joker = None
            black_10 = None
            temp_deck_cards = []
            processed_cards = 0
            max_cards_to_process = len(self.deck.cards) + 10

            print(f"DEBUG: Starting separation loop. Initial deck size: {len(self.deck.cards)}")

            while not self.deck.is_empty() and processed_cards < max_cards_to_process:
                card = self.deck.draw()
                processed_cards += 1
                if card is None: continue

                # +++ Intensive Debugging for 10 of Clubs +++
                is_rank_10 = isinstance(card.rank, int) and card.rank == 10
                is_suit_clubs = card.suit == "Clubs"

                # Print EVERY card drawn
                # print(f"  DEBUG: Drawn card: {repr(card)} | Rank Type: {type(card.rank)} | Suit Type: {type(card.suit)}")

                # Print specifically if rank is 10 OR suit is Clubs
                if is_rank_10 or is_suit_clubs:
                     print(f"  >>> DEBUG: Potential Match Drawn: {repr(card)}")
                     print(f"      - Rank: {card.rank} (Type: {type(card.rank)}) | Is Int 10? {is_rank_10}")
                     print(f"      - Suit: {card.suit} (Type: {type(card.suit)}) | Is 'Clubs'? {is_suit_clubs}")
                # +++ End Intensive Debugging +++

                is_10_of_clubs = is_rank_10 and is_suit_clubs

                if card.card_type == TYPE_JOKER and center_joker is None:
                     center_joker = card
                     # print("Found Joker for center.")
                elif is_10_of_clubs and black_10 is None: # Use the combined check result
                     black_10 = card
                     print(f"  !!! DEBUG: SUCCESS - Assigned 10 of Clubs: {repr(card)}")
                elif card.card_type != TYPE_JACK:
                    temp_deck_cards.append(card)

            if processed_cards >= max_cards_to_process:
                 print("Warning: Card separation loop hit safety limit during setup.")

            self.deck.cards = temp_deck_cards
            self.deck.shuffle()
            print(f"Main deck shuffled with {len(self.deck.cards)} cards.")

            if center_joker is None:
                print("CRITICAL ERROR: Could not find a Joker for center! Setup failed.")
                return None
            if black_10 is None: # Check the variable itself
                print("CRITICAL ERROR: Could not find 10 of Clubs for setup! Setup failed.")
                print(f"DEBUG: Loop finished. Processed {processed_cards} cards.")
                print(f"DEBUG: center_joker found: {center_joker is not None}")
                print(f"DEBUG: black_10 found: {black_10 is not None}") # This will print False
                return None

            # --- Placement Logic (remains the same) ---
            center_row, center_col = GRID_ROWS // 2, GRID_COLS // 2
            center_joker.is_face_up = True
            self.place_card(center_joker, center_row, center_col)

            black_10.is_face_up = True
            target_col_10 = center_col + 1 if center_col + 1 < GRID_COLS else center_col - 1
            self.place_card(black_10, center_row, target_col_10)

            # --- Fill Grid Logic (remains the same) ---
            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    if self.grid[r][c] is None:
                        card = self.deck.draw()
                        if card:
                            card.is_face_up = False
                            self.place_card(card, r, c)
                        else:
                             if r * GRID_COLS + c < (GRID_ROWS * GRID_COLS - 2):
                                print(f"Warning: Deck empty while filling grid at ({r},{c})")
                             break
                if self.deck.is_empty() and r < GRID_ROWS -1 :
                     print(f"Warning: Deck emptied prematurely during setup (Row {r}). Grid may be incomplete.")

            print("Board setup complete.")
            return jacks_for_players

        else:
            print(f"Game mode '{game_mode}' setup not implemented.")
            return None

    # --- Other Board methods remain the same (place_card, get_card_at, etc.) ---
    # Make sure to copy the whole class if needed, only setup_board is shown modified here.

    def place_card(self, card, row, col):
        if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
            print(f"Error: Tried to place card at invalid grid position ({row}, {col})")
            return
        if card is None:
             if self.grid[row][col] is not None:
                 if isinstance(self.grid[row][col], pygame.sprite.Sprite): # Check before removing
                     self.all_cards.remove(self.grid[row][col])
             self.grid[row][col] = None
             return

        if self.grid[row][col] is not None and self.grid[row][col] != card:
             if isinstance(self.grid[row][col], pygame.sprite.Sprite): # Check before removing
                 self.all_cards.remove(self.grid[row][col])

        self.grid[row][col] = card
        card_x = self.board_rect.left + GRID_MARGIN + col * (CARD_WIDTH + GRID_MARGIN)
        card_y = self.board_rect.top + GRID_MARGIN + row * (CARD_HEIGHT + GRID_MARGIN)
        if card.rect is None:
             if card.image: card.rect = card.image.get_rect()
             else: card.rect = pygame.Rect(0,0,CARD_WIDTH, CARD_HEIGHT) # Fallback rect
        card.rect.topleft = (card_x, card_y)

        if isinstance(card, pygame.sprite.Sprite):
             self.all_cards.add(card)

    def get_card_at(self, row, col):
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            return self.grid[row][col]
        return None

    def remove_card_at(self, row, col):
        card = self.get_card_at(row, col)
        if card:
            self.grid[row][col] = None
            if isinstance(card, pygame.sprite.Sprite): # Check before removing
                self.all_cards.remove(card)
            self.discard_pile.add_card(card)
            return card
        return None

    def get_grid_pos_from_screen(self, screen_x, screen_y):
        if not self.board_rect.collidepoint(screen_x, screen_y):
            return None
        relative_x = screen_x - self.board_rect.left
        relative_y = screen_y - self.board_rect.top
        if relative_x < GRID_MARGIN or relative_y < GRID_MARGIN:
             return None
        col = (relative_x - GRID_MARGIN) // (CARD_WIDTH + GRID_MARGIN)
        row = (relative_y - GRID_MARGIN) // (CARD_HEIGHT + GRID_MARGIN)
        card_x_start = GRID_MARGIN + col * (CARD_WIDTH + GRID_MARGIN)
        card_y_start = GRID_MARGIN + row * (CARD_HEIGHT + GRID_MARGIN)
        card_x_end = card_x_start + CARD_WIDTH
        card_y_end = card_y_start + CARD_HEIGHT
        if (card_x_start <= relative_x < card_x_end and
            card_y_start <= relative_y < card_y_end):
            if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                 return row, col
        return None

    def draw(self, surface):
        self.all_cards.draw(surface)

    def update_cards(self):
        self.all_cards.update()