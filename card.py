import pygame
import random
import os
from constants import * # Import all constants

class Card(pygame.sprite.Sprite):
    """Represents a single playing card."""
    def __init__(self, suit, rank, card_images_dict, game_mode="standard"):
        super().__init__()
        self.suit = suit
        # --- FIX: Convert numerical ranks to integers ---
        try:
            # If the rank can be converted to an int, store it as an int
            self.rank = int(rank)
        except ValueError:
            # Otherwise, keep it as a string (Ace, Jack, Queen, King, Joker)
            self.rank = rank
        # --- END FIX ---

        self._game_mode = game_mode # Store game mode if needed
        self.value = self._get_value()
        self.card_type = self._get_card_type()
        self.is_face_up = False

        self.card_images = card_images_dict
        if not isinstance(self.card_images, dict):
            print(f"ERROR: Card initialized with invalid card_images_dict for {suit} {rank}")
            self.card_images = {}

        self.image_face = None
        self.image_back = None
        self.image = None
        self.rect = None
        self.is_animating_flip = False
        self.animation_progress = 0
        self.target_face_up = False

        self.assign_images()

    # --- Rest of the Card class (_get_value, _get_card_type, assign_images, etc.) remains the same ---
    # Make sure methods correctly handle self.rank being an int or str now
    def _get_value(self):
        if isinstance(self.rank, int): # Check if it's an integer
            return self.rank
        # Handle string ranks
        elif self.rank == "Ace": return 1
        elif self.rank == "Queen": return 12
        elif self.rank == "King": return 13
        elif self.rank == "Joker": return 14
        elif self.rank == "Jack": return 11
        return 0

    def _get_card_type(self):
        if self.suit == "Joker": return TYPE_JOKER
        # Handle string ranks first
        elif self.rank == "Ace": return TYPE_ACE
        elif self.rank == "Queen": return TYPE_QUEEN
        elif self.rank == "King": return TYPE_KING
        elif self.rank == "Jack": return TYPE_JACK
        # Handle integer ranks
        elif isinstance(self.rank, int):
            if self.suit in ["Hearts", "Diamonds"]: return TYPE_EQUIPMENT
            elif self.suit in ["Clubs", "Spades"]: return TYPE_HAZARD
        return "Unknown"

    def assign_images(self):
        if not self.card_images:
            print(f"ERROR: Cannot assign images for {self.rank} of {self.suit}, image dictionary is missing or invalid.")
            self.image_face = pygame.Surface([CARD_WIDTH, CARD_HEIGHT]); self.image_face.fill(RED)
            self.image_back = pygame.Surface([CARD_WIDTH, CARD_HEIGHT]); self.image_back.fill(BLUE)
            self.image = self.image_back
            self.rect = self.image.get_rect()
            return

        try:
            rank_str = str(self.rank).lower()
            suit_str = self.suit.lower()
            face_key = f"{suit_str}_{rank_str}"

            self.image_face = self.card_images.get(face_key)
            if self.image_face is None:
                print(f"Warning: Image not found for key: '{face_key}'")
                self.image_face = pygame.Surface([CARD_WIDTH, CARD_HEIGHT]); self.image_face.fill(RED)

            self.image_back = self.card_images.get("card_back")
            if self.image_back is None:
                print(f"Warning: Card back image not found!")
                self.image_back = pygame.Surface([CARD_WIDTH, CARD_HEIGHT]); self.image_back.fill(BLUE)

            self.image = self.image_back if not self.is_face_up else self.image_face
            self.rect = self.image.get_rect()

        except Exception as e:
            print(f"Error assigning images for {self}: {e}")
            self.image_face = pygame.Surface([CARD_WIDTH, CARD_HEIGHT]); self.image_face.fill(RED)
            self.image_back = pygame.Surface([CARD_WIDTH, CARD_HEIGHT]); self.image_back.fill(BLUE)
            self.image = self.image_back
            self.rect = pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT)

    def start_flip(self):
        if not self.is_animating_flip:
            self.is_animating_flip = True
            self.target_face_up = not self.is_face_up
            self.animation_progress = 0

    def update(self):
        if self.is_animating_flip:
            self.animation_progress += 1
            half_flip_point = FLIP_SPEED
            scale_factor = abs(half_flip_point - self.animation_progress) / half_flip_point
            current_width = max(1, int(CARD_WIDTH * scale_factor))

            if self.animation_progress <= half_flip_point:
                image_to_scale = self.image_face if self.is_face_up else self.image_back
            else:
                image_to_scale = self.image_face if self.target_face_up else self.image_back

            if image_to_scale:
                self.image = pygame.transform.scale(image_to_scale, (current_width, CARD_HEIGHT))
            else:
                self.image = pygame.Surface((current_width, CARD_HEIGHT))
                self.image.fill(WHITE if self.animation_progress > half_flip_point else BLACK)

            center_pos = self.rect.center
            self.rect = self.image.get_rect(center=center_pos)

            if self.animation_progress >= half_flip_point * 2:
                self.is_animating_flip = False
                self.is_face_up = self.target_face_up
                if self.is_face_up: self.image = self.image_face
                else: self.image = self.image_back
                if self.image:
                    self.image = pygame.transform.scale(self.image, (CARD_WIDTH, CARD_HEIGHT))
                    self.rect = self.image.get_rect(center=center_pos)

    def draw(self, surface):
        if self.image and self.rect:
            surface.blit(self.image, self.rect)

    def __repr__(self):
        state = "[UP]" if self.is_face_up else "[DN]"
        return f"{self.rank} of {self.suit} {state}"

    def __str__(self):
        # Use str(self.rank) in case it's an int
        return f"{str(self.rank)} of {self.suit}"


# --- Modify Deck Class ---
class Deck:
    def __init__(self, card_images_dict, game_mode="standard"):
        self.cards = []
        self.game_mode = game_mode
        self.card_images = card_images_dict
        if game_mode != "empty":
            self.create_deck()

    def create_deck(self):
        """Populates the deck based on the game mode."""
        self.cards = []
        if not self.card_images:
            print("ERROR: Cannot create deck, card images dictionary is missing.")
            return

        if self.game_mode == "standard":
            # Use constants.RANKS which contains strings and numbers
            for suit in SUITS:
                for rank in RANKS: # Iterate through the original RANKS list
                    if rank != "Jack": # Exclude Jacks
                        # The Card __init__ now handles converting '2'..'10' to int
                        self.cards.append(Card(suit, rank, self.card_images, self.game_mode))

            # Add Jokers
            self.cards.append(Card("Joker", "Joker", self.card_images, self.game_mode))
            self.cards.append(Card("Joker", "Joker", self.card_images, self.game_mode))
            print(f"Standard deck created with {len(self.cards)} cards.")
            self.shuffle()

        # elif self.game_mode == "advanced": etc...
        else:
            if self.game_mode != "empty":
                print(f"Warning: Deck creation not implemented for game mode '{self.game_mode}'. Deck is empty.")

    # --- Rest of Deck class methods (shuffle, draw, etc.) remain the same ---
    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        if self.cards:
            return self.cards.pop()
        else:
            return None

    def add_card(self, card):
        if isinstance(card, Card):
            self.cards.append(card)

    def add_cards(self, card_list):
        for card in card_list:
            self.add_card(card)

    def is_empty(self):
        return len(self.cards) == 0

    def __len__(self):
        return len(self.cards)