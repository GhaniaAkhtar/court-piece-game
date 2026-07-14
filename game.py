class Card:
    """Represents a single playing card with a rank and suit."""
    
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{self.rank} of {self.suit}"


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

import random


def deal_cards(deck):
    """Shuffles the deck and deals 13 cards to each of 4 players."""
    
    shuffled_deck = deck.copy()
    random.shuffle(shuffled_deck)
    
    players = {
        "Player 1": [],
        "Player 2": [],
        "Player 3": [],
        "Player 4": []
    }
    
    player_names = list(players.keys())
    for i, card in enumerate(shuffled_deck):
        player = player_names[i % 4]
        players[player].append(card)
    
    return players

def determine_trick_winner(cards_played, led_suit, trump_suit):
    """
    Given the 4 cards played in a trick, figures out who wins.
    cards_played is a list of tuples: [(player_name, card), (player_name, card), ...]
    """
    
    rank_order = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
    
    def card_strength(card):
        # Trump cards always beat non-trump cards
        if card.suit == trump_suit:
            return (1, rank_order.index(card.rank))
        elif card.suit == led_suit:
            return (0, rank_order.index(card.rank))  
        else:
            return (-1, -1)  # can't win if it's neither trump nor the led suit
    
    winner = max(cards_played, key=lambda x: card_strength(x[1]))
    return winner  # returns (player_name, card)

def get_valid_moves(hand, led_suit):
    """
    Returns which cards a player is allowed to play.
    If they have the led suit, they MUST play from it.
    Otherwise, they can play anything (including trump).
    """
    if led_suit is None:
        return hand[:]  # leader can play ANY card

    cards_of_led_suit = [card for card in hand if card.suit == led_suit]

    if cards_of_led_suit:
        return cards_of_led_suit
    else:
        return hand[:]

def choose_card_manual(player_name, hand, valid_moves, led_suit, trump_suit):
    """Asks a real human player to pick a card. Shows their full hand,
    tells them which cards are legal, and won't accept an illegal move."""

    print(f"\n{player_name}'s turn.")
    print(f"Trump suit: {trump_suit}")
    print(f"Led suit: {led_suit if led_suit else '(you are leading this trick)'}")

    print(f"\n{player_name}'s hand:")
    for i, card in enumerate(hand, start=1):
        legal = card in valid_moves
        tag = "" if legal else "  (not playable)"
        print(f"{i}. {card}{tag}")

    while True:
        choice = input("Enter the number of the card you want to play: ")
        if not choice.isdigit():
            print("Please enter a number.")
            continue
        index = int(choice) - 1
        if index < 0 or index >= len(hand):
            print("That number isn't on your hand. Try again.")
            continue
        chosen_card = hand[index]
        if chosen_card not in valid_moves:
            print("That card isn't legal right now (you must follow suit if you can). Try again.")
            continue
        return chosen_card
    
def play_round(hands, seating_order, dealer_index, trump_suit):
    left_of_dealer = (dealer_index + 1) % 4
    right_of_dealer = (dealer_index - 1) % 4
    
    trump_selector = seating_order[left_of_dealer]
    first_leader = seating_order[right_of_dealer]
    
    
    teams = {
        "Team A": [seating_order[0], seating_order[2]],
        "Team B": [seating_order[1], seating_order[3]]
    }

    print("\n--- Team Assignments ---")
    for team_name, team_players in teams.items():
        print(f"{team_name}: {team_players[0]} & {team_players[1]}")

    scores = {"Team A": 0, "Team B": 0}
    
    def get_team(player):
        for team, players in teams.items():
            if player in players:
                return team
    
    current_leader = seating_order.index(first_leader)
    hands_played = 0
    
    while scores["Team A"] < 7 and scores["Team B"] < 7 and hands_played < 13:
        led_suit = None
        trick = []

        print(f"\n=========== Trick {hands_played + 1} ===========")

        for i in range(4):
            player = seating_order[(current_leader + i) % 4]
            valid_moves = get_valid_moves(hands[player], led_suit)
            card = choose_card_manual(player, hands[player], valid_moves, led_suit, trump_suit)
            hands[player].remove(card)
            trick.append((player, card))

            if led_suit is None:
                led_suit = card.suit

            print(f"\n--- Cards played so far in this trick ---")
            for played_player, played_card in trick:
                print(f"  {played_player}: {played_card}")

        winner_player, winner_card = determine_trick_winner(trick, led_suit, trump_suit)
        scores[get_team(winner_player)] += 1
        current_leader = seating_order.index(winner_player)
        hands_played += 1

        print(f"\n>>> Trick {hands_played} Summary <<<")
        for played_player, played_card in trick:
            print(f"  {played_player} played {played_card}")
        print(f"  Led suit: {led_suit} | Trump suit: {trump_suit}")
        print(f"  WINNER: {winner_player} ({get_team(winner_player)}) with {winner_card}")
        print(f"  Score now -> Team A: {scores['Team A']} | Team B: {scores['Team B']}")
    
    print("\n=========== ROUND OVER ===========")
    print(f"Final Score -> Team A: {scores['Team A']} | Team B: {scores['Team B']}")
    print(f"Total tricks played: {hands_played}")

    if scores["Team A"] > scores["Team B"]:
        round_winner = "Team A"
    else:
        round_winner = "Team B"

    print(f"🏆 {round_winner} WINS THE ROUND! 🏆")
    print(f"{round_winner} players: {teams[round_winner][0]} & {teams[round_winner][1]}")

    return scores, hands_played, trump_suit, trump_selector, first_leader

def select_trump(player_name, hand):
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    
    print(f"\n{player_name}'s hand:")
    for i, card in enumerate(hand, start=1):
        print(f"{i}. {card}")
    
    print(f"\n{player_name}, please choose the trump suit:")
    for i, suit in enumerate(suits, start=1):
        print(f"{i}. {suit}")
    
    while True:
        choice = input("Enter the number of your choice: ")
        if choice.isdigit() and 1 <= int(choice) <= 4:
            return suits[int(choice) - 1]
        print("Invalid choice, please enter a number between 1 and 4.")
    
def select_dealer(deck):
    rank_order = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
    players = ["Player 1", "Player 2", "Player 3", "Player 4"]
    
    round_num = 1
    
    while True:
        shuffled = deck.copy()
        random.shuffle(shuffled)
        
        revealed = {
            "Player 1": shuffled[0],
            "Player 2": shuffled[1],
            "Player 3": shuffled[2],
            "Player 4": shuffled[3]
        }
        
        print(f"\n--- Round {round_num}: Dealer Selection ---")
        for player in players:
            print(f"{player}: {revealed[player]}")
        
        highest_rank = max(rank_order.index(card.rank) for card in revealed.values())
        winners = [player for player, card in revealed.items() if rank_order.index(card.rank) == highest_rank]
        
        if len(winners) == 1:
            return winners[0], revealed
        
        print(f"\nTie between: {winners}, reshuffling and redrawing...")
        round_num += 1

def choose_game_level():
    """Asks the user which mode to play: 4 humans, or 1 human vs 3 AI."""
    print("\n--- Choose Game Mode ---")
    print("1. Level 1: 4 Players (all human)")
    print("2. Level 2: 1 Human vs 3 AI")

    while True:
        choice = input("Enter 1 or 2: ")
        if choice == "1":
            return 1
        elif choice == "2":
            return 2
        else:
            print("Invalid choice, please enter 1 or 2.")

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
    batch_num = 1
    
    while remaining:
        print(f"\n--- Dealing batch {batch_num} ---")
        for player in seating_order:
            batch = remaining[:4]
            remaining = remaining[4:]
            full_hands[player].extend(batch)
            print(f"{player} receives 4 cards. Total now: {len(full_hands[player])}")
            
            if not remaining:
                break
        batch_num += 1
    
    return full_hands
1
#===TESTING===
if __name__ == "__main__":
    game_level = choose_game_level()
    my_deck = create_deck()

    if game_level == 2:
        print("\nLevel 2 (AI) isn't built yet — coming in the next step.")
        exit()
    
    dealer, dealer_reveal = select_dealer(my_deck)
    print("\nDealer selected:", dealer)
    
    seating_order = ["Player 1", "Player 2", "Player 3", "Player 4"]
    dealer_index = seating_order.index(dealer)
    left_of_dealer = (dealer_index + 1) % 4
    right_of_dealer = (dealer_index - 1) % 4
    
    trump_selector = seating_order[left_of_dealer]
    first_leader = seating_order[right_of_dealer]
    
    five_card_hands, my_deck = deal_five_cards(my_deck)
    
    trump_suit = select_trump(trump_selector, five_card_hands[trump_selector])
    
    print("\n--- After Trump Selection ---")
    print("Deck size before final deal:", len(my_deck))
    
    full_hands = deal_remaining_cards(my_deck, five_card_hands)
    
    for player in seating_order:
        print(f"{player}: {len(full_hands[player])} cards")
    
    print("\n--- Summary ---")
    print("Dealer:", dealer)
    print("Trump selector:", trump_selector)
    print("First leader:", first_leader)
    print("Trump suit chosen:", trump_suit)

    for player in seating_order:
        print(f"{player}: {len(full_hands[player])} cards")
    
    print("\n--- Everyone's Full Hands ---")
    for player in seating_order:
        print(f"\n{player}:")
        for card in full_hands[player]:
            print(f"  {card}")
    
    print("\n--- Playing the round ---")
    scores, hands_played, trump_suit, trump_selector, first_leader = play_round(
        full_hands, seating_order, dealer_index, trump_suit
    )
    print("\n--- Round Over ---")
    print("Final scores:", scores)
    print("Tricks played:", hands_played)
