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

    def play_card(self, card: Dict, theater: str, player_id: int):
        self.board[theater].append(card)
        self.hands[player_id].remove(card)
        self.apply_ability(card, theater, player_id)
        self.turn = 1 - self.turn  # Switch turn

    def apply_ability(self, card: Dict, theater: str, player_id: int):
        """Apply special abilities based on card effects."""
        opponent = 1 - player_id  # Get the opponent's ID

        if card["ability"] == "flip":
            if self.board[theater]:  
                self.board[theater][-1]["strength"] = 0  

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
            self.hands[opponent] = [{"name": card["name"], "strength": card["strength"], "theater": card["theater"], "ability": None} if c == card else c for c in self.hands[opponent]]

        elif card["ability"] == "peek":
            if self.hands[opponent]:  
                peeked_card = self.hands[opponent][0]  
                print(f"Peeked at opponent's card: {peeked_card['name']} (Strength: {peeked_card['strength']})")

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
                        game.play_card(card, theater, player_id)
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
