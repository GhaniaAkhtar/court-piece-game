import random


class Card:
    """Represents a single playing card with a rank and suit."""

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{self.rank} of {self.suit}"

    def __eq__(self, other):
        return isinstance(other, Card) and self.rank == other.rank and self.suit == other.suit


def card_to_dict(card):
    """Turns a Card object into a plain dict so it can be saved as JSON."""
    return {"rank": card.rank, "suit": card.suit}


def card_from_dict(data):
    """Turns a plain dict (loaded from JSON) back into a Card object."""
    return Card(data["rank"], data["suit"])


def create_deck():
    """Builds a standard 52-card deck (4 suits x 13 ranks)."""

    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]

    deck = []
    for suit in suits:
        for rank in ranks:
            card = Card(rank, suit)
            deck.append(card)

    return deck


def determine_trick_winner(cards_played, led_suit, trump_suit):
    """
    Given the 4 cards played in a trick, figures out who wins.
    cards_played is a list of tuples: [(player_name, card), (player_name, card), ...]
    """

    rank_order = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]

    def card_strength(card):
        if card.suit == trump_suit:
            return (1, rank_order.index(card.rank))
        elif card.suit == led_suit:
            return (0, rank_order.index(card.rank))
        else:
            return (-1, -1)

    winner = max(cards_played, key=lambda x: card_strength(x[1]))
    return winner


def get_valid_moves(hand, led_suit):
    """
    Returns which cards a player is allowed to play.
    If they have the led suit, they MUST play from it.
    Otherwise, they can play anything (including trump).
    """
    if led_suit is None:
        return hand[:]

    cards_of_led_suit = [card for card in hand if card.suit == led_suit]

    if cards_of_led_suit:
        return cards_of_led_suit
    else:
        return hand[:]


def select_dealer(deck):
    rank_order = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
    players = ["Player 1", "Player 2", "Player 3", "Player 4"]

    while True:
        shuffled = deck.copy()
        random.shuffle(shuffled)

        revealed = {
            "Player 1": shuffled[0],
            "Player 2": shuffled[1],
            "Player 3": shuffled[2],
            "Player 4": shuffled[3]
        }

        highest_rank = max(rank_order.index(card.rank) for card in revealed.values())
        winners = [player for player, card in revealed.items() if rank_order.index(card.rank) == highest_rank]

        if len(winners) == 1:
            return winners[0], revealed


def deal_five_cards(deck):
    random.shuffle(deck)

    five_card_hands = {
        "Player 1": deck[0:5],
        "Player 2": deck[5:10],
        "Player 3": deck[10:15],
        "Player 4": deck[15:20]
    }

    remaining_deck = deck[20:]

    return five_card_hands, remaining_deck


def deal_remaining_cards(deck, five_card_hands):
    seating_order = ["Player 1", "Player 2", "Player 3", "Player 4"]
    full_hands = {player: five_card_hands[player].copy() for player in seating_order}

    remaining = deck.copy()

    while remaining:
        for player in seating_order:
            batch = remaining[:4]
            remaining = remaining[4:]
            full_hands[player].extend(batch)

            if not remaining:
                break

    return full_hands
