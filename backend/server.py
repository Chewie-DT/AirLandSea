from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import uuid
import random

app = FastAPI()

# Game state storage
games: Dict[str, Any] = {}

# Define the game deck
FULL_DECK = [
    {"name": "Fighter Jet", "strength": 6, "theater": "Air", "ability": None},
    {"name": "Stealth Bomber", "strength": 5, "theater": "Air", "ability": "flip"},
    {"name": "Helicopter", "strength": 4, "theater": "Air", "ability": "move"},
    # Add more cards...
]

class Game:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.players: List[WebSocket] = []
        self.board = {"Air": [], "Land": [], "Sea": []}
        self.hands = {}
        self.turn = 0
        self.scores = {0: 0, 1: 0}
        self.deck = FULL_DECK.copy()
        self.deal_hands()

    def deal_hands(self):
        """Shuffle and distribute cards to players."""
        random.shuffle(self.deck)
        self.hands[0] = self.deck[:6]
        self.hands[1] = self.deck[6:12]

@app.websocket("/game/{game_id}/{player_id}")
async def game_socket(websocket: WebSocket, game_id: str, player_id: int):
    try:
        player_id = int(player_id)
        await websocket.accept()
        
        if game_id not in games:
            games[game_id] = Game()

        game = games[game_id]
        
        if player_id not in [0, 1]:
            await websocket.close(code=1003, reason="Invalid player ID")
            return

        game.players.append(websocket)

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    move = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_json({"error": "Invalid move format"})
                    continue

                if move["action"] == "play_card":
                    card = move["card"]
                    theater = move["theater"]

                    if card in game.hands[player_id]:
                        game.board[theater].append(card)
                        game.hands[player_id].remove(card)
                        game.turn = 1 - game.turn  # Switch turn
                    else:
                        await websocket.send_json({"error": "Card not in hand"})
                        continue

                elif move["action"] == "withdraw":
                    game.scores[1 - player_id] += 6

                for player in game.players:
                    await player.send_json({
                        "board": game.board,
                        "hands": game.hands,
                        "turn": game.turn,
                        "scores": game.scores,
                    })

        except WebSocketDisconnect:
            game.players.remove(websocket)
            if not game.players:
                del games[game_id]

    except Exception as e:
        await websocket.close(code=1003, reason=str(e))
