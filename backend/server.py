from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import uuid
import random
import logging

# Setup logging
logger = logging.getLogger("game")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Game state storage
class GameState:
    def __init__(self):
        self.games: Dict[str, Game] = {}

    def get_game(self, game_id: str) -> 'Game':
        if game_id not in self.games:
            self.games[game_id] = Game()
        return self.games[game_id]

    def remove_game(self, game_id: str):
        if game_id in self.games:
            del self.games[game_id]

game_state = GameState()

# Define the game deck
FULL_DECK = [
    {"name": "Fighter Jet", "strength": 6, "theater": "Air", "ability": None},
    {"name": "Stealth Bomber", "strength": 5, "theater": "Air", "ability": "flip"},
    {"name": "Helicopter", "strength": 4, "theater": "Air", "ability": "move"},
    {"name": "Air Strike", "strength": 3, "theater": "Air", "ability": "weaken"},
    {"name": "Paratroopers", "strength": 2, "theater": "Air", "ability": "reinforce"},
    {"name": "Spy Drone", "strength": 1, "theater": "Air", "ability": "peek"},
    {"name": "Tank", "strength": 6, "theater": "Land", "ability": None},
    {"name": "Artillery", "strength": 5, "theater": "Land", "ability": "weaken"},
    {"name": "Infantry", "strength": 4, "theater": "Land", "ability": "reinforce"},
    {"name": "Sniper", "strength": 3, "theater": "Land", "ability": "disable"},
    {"name": "Ambush", "strength": 2, "theater": "Land", "ability": "flip"},
    {"name": "Scout", "strength": 1, "theater": "Land", "ability": "peek"},
    {"name": "Battleship", "strength": 6, "theater": "Sea", "ability": None},
    {"name": "Submarine", "strength": 5, "theater": "Sea", "ability": "move"},
    {"name": "Destroyer", "strength": 4, "theater": "Sea", "ability": "disable"},
    {"name": "Naval Mine", "strength": 3, "theater": "Sea", "ability": "flip"},
    {"name": "Torpedo Boat", "strength": 2, "theater": "Sea", "ability": "weaken"},
    {"name": "Radar", "strength": 1, "theater": "Sea", "ability": "peek"},
]

class Game:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.players: Dict[int, WebSocket] = {}
        self.board = {"Air": [], "Land": [], "Sea": []}
        self.hands = {}
        self.turn = 0
        self.scores = {0: 0, 1: 0}
        self.victory_points = {0: 0, 1: 0}
        self.deck = FULL_DECK.copy()
        self.deal_hands()

    def deal_hands(self):
        random.shuffle(self.deck)
        self.hands[0] = self.deck[:6]
        self.hands[1] = self.deck[6:12]

    def play_card(self, card: Dict, theater: str, player_id: int, face_down: bool = False):
        if face_down:
            card = {"name": "Face Down", "strength": 2, "theater": theater, "ability": None, "player": player_id}
        else:
            card["player"] = player_id
        
        self.board[theater].append(card)
        self.hands[player_id].remove(card)

        if not face_down:
            self.apply_ability(card, theater, player_id)

        self.turn = 1 - self.turn

    def apply_ability(self, card: Dict, theater: str, player_id: int):
        opponent = 1 - player_id

        if card["ability"] == "flip":
            for played_card in reversed(self.board[theater]):
                if played_card.get("player") != player_id and played_card["name"] != "Face Down":
                    played_card["strength"] = 0
                    break

        elif card["ability"] == "move":
            if self.board[theater]:
                moved_card = self.board[theater].pop()
                new_theater = random.choice(["Air", "Land", "Sea"])
                self.board[new_theater].append(moved_card)

        elif card["ability"] == "weaken":
            if self.board[theater]:
                self.board[theater][-1]["strength"] = max(0, self.board[theater][-1]["strength"] - 2)

        elif card["ability"] == "reinforce":
            if self.board[theater]:
                self.board[theater][-1]["strength"] += 2

        elif card["ability"] == "disable":
            for i, c in enumerate(self.hands[opponent]):
                if c == card:
                    self.hands[opponent][i] = {"name": c["name"], "strength": c["strength"], "theater": c["theater"], "ability": None}

        elif card["ability"] == "peek":
            if self.hands[opponent]:
                peeked_card = self.hands[opponent][0]
                logger.info(f"Peeked at opponent's card: {peeked_card['name']} (Strength: {peeked_card['strength']})")

    def calculate_victory_points(self):
        player_0_control = sum(1 for theater in self.board if sum(card["strength"] for card in self.board[theater] if card["player"] == 0) >
                               sum(card["strength"] for card in self.board[theater] if card["player"] == 1))
        player_1_control = 3 - player_0_control

        if player_0_control >= 2:
            self.victory_points[0] += self.get_round_score()
        elif player_1_control >= 2:
            self.victory_points[1] += self.get_round_score()

    def get_round_score(self):
        return 6 - sum(len(theater) for theater in self.board.values())

@app.websocket("/game/{game_id}/{player_id}")
async def game_socket(websocket: WebSocket, game_id: str, player_id: int):
    try:
        player_id = int(player_id)
        await websocket.accept()

        if player_id not in [0, 1]:
            await websocket.close(code=1003, reason="Invalid player ID")
            return

        game = game_state.get_game(game_id)

        if len(game.players) >= 2:
            await websocket.close(code=1003, reason="Game already full")
            return

        game.players[player_id] = websocket

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    move = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_json({"error": "Invalid move format"})
                    continue

                if move["action"] == "play_card":
                    await game.handle_move(move, websocket, player_id)

                elif move["action"] == "withdraw":
                    game.scores[1 - player_id] += game.get_round_score()
                    game.board = {"Air": [], "Land": [], "Sea": []}
                    game.hands = {0: [], 1: []}

                game.calculate_victory_points()

                for player in game.players.values():
                    await player.send_json({
                        "board": game.board,
                        "hands": game.hands,
                        "turn": game.turn,
                        "scores": game.scores,
                        "victory_points": game.victory_points,
                    })

        except WebSocketDisconnect:
            del game.players[player_id]
            if not game.players:
                game_state.remove_game(game_id)

    except Exception as e:
        logger.error(f"Error: {e}")
        await websocket.close(code=1003, reason=str(e))