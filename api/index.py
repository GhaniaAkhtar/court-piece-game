import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from upstash_redis import Redis

from game import (
    Card,
    card_to_dict,
    card_from_dict,
    create_deck,
    select_dealer,
    deal_five_cards,
    deal_remaining_cards,
    get_valid_moves,
    determine_trick_winner,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

redis = Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])
STATE_KEY = "court_piece_game_state"

CARD_LIST_KEYS = {"deck", "remaining_deck"}
PLAYER_HAND_DICT_KEYS = {"five_card_hands", "full_hands"}
TRICK_KEY = "current_trick"


def serialize_state(state):
    data = {}
    for key, value in state.items():
        if key in CARD_LIST_KEYS:
            data[key] = [card_to_dict(c) for c in value]
        elif key in PLAYER_HAND_DICT_KEYS:
            data[key] = {player: [card_to_dict(c) for c in hand] for player, hand in value.items()}
        elif key == TRICK_KEY:
            data[key] = [{"player": p, "card": card_to_dict(c)} for p, c in value]
        else:
            data[key] = value
    return data


def deserialize_state(data):
    state = {}
    for key, value in data.items():
        if key in CARD_LIST_KEYS:
            state[key] = [card_from_dict(c) for c in value]
        elif key in PLAYER_HAND_DICT_KEYS:
            state[key] = {player: [card_from_dict(c) for c in hand] for player, hand in value.items()}
        elif key == TRICK_KEY:
            state[key] = [(item["player"], card_from_dict(item["card"])) for item in value]
        else:
            state[key] = value
    return state


def load_state():
    raw = redis.get(STATE_KEY)
    if not raw:
        return {}
    return deserialize_state(json.loads(raw))


def save_state(state):
    redis.set(STATE_KEY, json.dumps(serialize_state(state)))


@app.get("/api")
def read_root():
    return {"message": "Server is working!"}


@app.post("/api/deal")
def deal():
    game_state = load_state()
    deck = create_deck()
    game_state["deck"] = deck
    save_state(game_state)
    return {"message": "Deck created", "deck_size": len(deck)}


@app.get("/api/game-state")
def get_game_state():
    game_state = load_state()
    if "deck" not in game_state:
        return {"message": "No deck yet. Call /deal first."}
    return {"deck_size": len(game_state["deck"])}


@app.post("/api/start-game")
def start_game():
    deck = create_deck()
    dealer, dealer_reveal = select_dealer(deck)

    seating_order = ["Player 1", "Player 2", "Player 3", "Player 4"]
    dealer_index = seating_order.index(dealer)
    left_of_dealer = (dealer_index + 1) % 4
    right_of_dealer = (dealer_index - 1) % 4
    trump_selector = seating_order[left_of_dealer]
    first_leader = seating_order[right_of_dealer]

    five_card_hands, remaining_deck = deal_five_cards(deck)

    game_state = {
        "seating_order": seating_order,
        "dealer": dealer,
        "dealer_index": dealer_index,
        "trump_selector": trump_selector,
        "first_leader": first_leader,
        "five_card_hands": five_card_hands,
        "remaining_deck": remaining_deck,
    }
    save_state(game_state)

    return {
        "message": "Game started",
        "dealer": dealer,
        "dealer_reveal": {player: str(card) for player, card in dealer_reveal.items()},
        "trump_selector": trump_selector,
        "trump_selector_hand": [str(card) for card in five_card_hands[trump_selector]]
    }


@app.post("/api/select-trump")
def select_trump_choice(suit: str):
    valid_suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    suit = suit.capitalize()

    if suit not in valid_suits:
        return {"error": f"Invalid suit. Choose from {valid_suits}"}

    game_state = load_state()
    game_state["trump_suit"] = suit
    save_state(game_state)

    return {
        "message": "Trump suit selected",
        "trump_suit": suit,
        "trump_selector": game_state["trump_selector"]
    }


@app.post("/api/deal-remaining")
def deal_remaining():
    game_state = load_state()

    if "trump_suit" not in game_state:
        return {"error": "Trump suit not selected yet. Call /select-trump first."}

    full_hands = deal_remaining_cards(game_state["remaining_deck"], game_state["five_card_hands"])
    game_state["full_hands"] = full_hands

    seating_order = game_state["seating_order"]
    teams = {
        "Team A": [seating_order[0], seating_order[2]],
        "Team B": [seating_order[1], seating_order[3]]
    }

    game_state["teams"] = teams
    game_state["scores"] = {"Team A": 0, "Team B": 0}
    game_state["current_leader"] = game_state["first_leader"]
    game_state["current_trick"] = []
    game_state["led_suit"] = None
    game_state["hands_played"] = 0
    game_state["round_over"] = False
    game_state["round_winner"] = None

    save_state(game_state)

    return {
        "message": "Remaining cards dealt",
        "hand_sizes": {player: len(hand) for player, hand in full_hands.items()},
        "teams": teams,
        "current_turn": game_state["current_leader"]
    }


@app.get("/api/my-hand")
def my_hand(player: str):
    game_state = load_state()

    if "full_hands" not in game_state:
        return {"error": "Hands not dealt yet. Call /deal-remaining first."}

    if player not in game_state["full_hands"]:
        return {"error": f"Unknown player: {player}"}

    hand = game_state["full_hands"][player]
    valid_moves = get_valid_moves(hand, game_state["led_suit"])

    return {
        "player": player,
        "hand": [str(card) for card in hand],
        "valid_moves": [str(card) for card in valid_moves],
        "led_suit": game_state["led_suit"],
        "trump_suit": game_state["trump_suit"]
    }


@app.post("/api/play-card")
def play_card_endpoint(player: str, rank: str, suit: str):
    game_state = load_state()

    if "current_leader" not in game_state:
        return {"error": "Game not ready. Call /deal-remaining first."}

    if game_state.get("round_over"):
        return {"error": "The round is already over. Start a new game with /start-game."}

    seating_order = game_state["seating_order"]
    current_trick = game_state["current_trick"]
    turn_index = (seating_order.index(game_state["current_leader"]) + len(current_trick)) % 4
    expected_player = seating_order[turn_index]

    if player != expected_player:
        return {"error": f"It's not {player}'s turn. It's {expected_player}'s turn."}

    hand = game_state["full_hands"][player]
    matching_cards = [c for c in hand if c.rank == rank and c.suit == suit]
    if not matching_cards:
        return {"error": f"{player} does not have {rank} of {suit} in hand."}
    card = matching_cards[0]

    valid_moves = get_valid_moves(hand, game_state["led_suit"])
    if card not in valid_moves:
        return {"error": "Illegal move. You must follow suit if you can."}

    hand.remove(card)
    current_trick.append((player, card))
    if game_state["led_suit"] is None:
        game_state["led_suit"] = card.suit

    result = {
        "message": f"{player} played {card}",
        "trick_so_far": [{"player": p, "card": str(c)} for p, c in current_trick]
    }

    if len(current_trick) < 4:
        next_index = (seating_order.index(game_state["current_leader"]) + len(current_trick)) % 4
        result["current_turn"] = seating_order[next_index]

    if len(current_trick) == 4:
        winner_player, winner_card = determine_trick_winner(current_trick, game_state["led_suit"], game_state["trump_suit"])
        team = "Team A" if winner_player in game_state["teams"]["Team A"] else "Team B"
        game_state["scores"][team] += 1
        game_state["hands_played"] += 1
        game_state["current_leader"] = winner_player
        game_state["current_trick"] = []
        game_state["led_suit"] = None

        result["trick_winner"] = winner_player
        result["trick_winner_team"] = team
        result["scores"] = game_state["scores"]

        scores = game_state["scores"]
        if scores["Team A"] >= 7 or scores["Team B"] >= 7 or game_state["hands_played"] >= 13:
            round_winner = "Team A" if scores["Team A"] > scores["Team B"] else "Team B"
            game_state["round_over"] = True
            game_state["round_winner"] = round_winner

            result["round_over"] = True
            result["round_winner"] = round_winner
            result["round_winner_players"] = game_state["teams"][round_winner]
        else:
            result["round_over"] = False

    save_state(game_state)

    return result
