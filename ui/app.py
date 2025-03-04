"""
Web server for the Texas Hold'em Poker game.
"""
import asyncio
import enum
import os
import json
from typing import Any
import uuid
import sys

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import our poker game modules
from core.game import Game, GameStatus, GameAction, GameConfig, BettingRound
from core.player import Player, PlayerStatus
from core.table import Table

# Create FastAPI app
app = FastAPI(title="Texas Hold'em Poker")

# Set up templates and static files directories
# Use absolute paths or paths relative to the module location
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))
app.mount("/assets", StaticFiles(directory=os.path.join(current_dir, "assets")), name="assets")

# Store active games in memory (in a real app, you'd use a database)
active_games = {}
active_players = {}
active_connections = {}



@app.get("/", response_class=HTMLResponse)
async def get_home_page(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/game/{game_id}", response_class=HTMLResponse)
async def get_game_page(request: Request, game_id: str):
    """Render the game page."""
    # Check if game exists
    if game_id not in active_games:
        # Redirect to home page if game doesn't exist
        return templates.TemplateResponse("index.html", {"request": request, "error": "Game not found"})
    
    return templates.TemplateResponse("game.html", {
        "request": request,
        "game_id": game_id
    })

@app.post("/api/create_game")
async def create_game():
    """Create a new game."""
    # Generate a unique game ID
    game_id = str(uuid.uuid4())
    
    # Create a new table
    table = Table(game_id, "Poker Table", max_seats=6)
    
    # Create a new game
    config = GameConfig(
        small_blind=5,
        big_blind=10,
        ante=0,
        min_players=2,
        max_players=6,
        starting_chips=1000
    )
    game = Game(game_id, table, config)
    
    # Store the game
    active_games[game_id] = game
    
    return {"game_id": game_id}

@app.post("/api/join_game/{game_id}")
async def join_game(game_id: str, player_name: str):
    """Join an existing game."""
    # Check if game exists
    if game_id not in active_games:
        return {"error": "Game not found"}
    
    game = active_games[game_id]
    
    # Create a new player
    player_id = str(uuid.uuid4())
    player = Player(player_id, name=player_name, chips=game.config.starting_chips)
    
    # Add player to the table
    if not game.table.add_player(player):
        return {"error": "Table is full"}
    
    # Store the player
    active_players[player_id] = player
    
    return {
        "player_id": player_id,
        "game_id": game_id
    }

@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    """WebSocket endpoint for real-time game updates."""
    # Check if game and player exist
    if game_id not in active_games or player_id not in active_players:
        await websocket.close(code=1000)
        return
    
    # Get the game and player
    game = active_games[game_id]
    player = active_players[player_id]
    
    # Accept the WebSocket connection
    await websocket.accept()
    
    # Store the connection
    active_connections[player_id] = websocket
    
    try:
        # Send initial game state
        await send_game_state(game, player_id)
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle player action
            if message["type"] == "action":
                action_type = message["action"]
                amount = message.get("amount", 0)
                
                # Convert action string to enum
                action = GameAction[action_type]
                
                # Process the action
                if game.state.current_player_idx >= 0:
                    current_player = game.table.get_player_at_position(game.state.current_player_idx)
                    if current_player and current_player.id == player_id:
                        # Handle the action
                        game.handle_player_action(player_id, action, amount)
                        
                        # Send updated game state to all players
                        await broadcast_game_state(game)
            
            # Handle start game request
            elif message["type"] == "start_game":
                if game.state.status == GameStatus.WAITING:
                    # Start the game
                    game.start_hand()
                    
                    # Send updated game state to all players
                    await broadcast_game_state(game)
    
    except WebSocketDisconnect:
        # Remove the connection
        if player_id in active_connections:
            del active_connections[player_id]
        
        # If this is a game in progress, make the player sit out
        if player.status == PlayerStatus.ACTIVE:
            player.sit_out()
            
            # Send updated game state to all players
            await broadcast_game_state(game)

async def send_game_state(game: Game, player_id: str):
    """Send game state to a specific player."""
    if player_id not in active_connections:
        return
    
    # Get the player's view of the game state
    game_state = game.get_game_state_for_player(player_id)
    
    # If the game is finished, automatically start a new hand after 3 seconds
    if game_state['status'] == 'FINISHED':
        # We use asyncio.create_task to avoid blocking this function
        asyncio.create_task(start_next_hand(game, 3))
    
    # Convert the game state to be JSON serializable
    game_state_json = prepare_for_json(game_state)
    
    # Convert to JSON and send
    await active_connections[player_id].send_text(json.dumps({
        "type": "game_state",
        "state": game_state_json
    }))

def prepare_for_json(obj: Any) -> Any:
    """
    Recursively convert objects to JSON-serializable types.
    Handles Enum objects, nested dictionaries, and lists.
    """
    if isinstance(obj, enum.Enum):
        return obj.name  # Convert Enum to string
    elif isinstance(obj, dict):
        # Convert dictionary keys and values
        return {
            prepare_for_json(key): prepare_for_json(value)
            for key, value in obj.items()
        }
    elif isinstance(obj, list):
        # Convert list items
        return [prepare_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Convert custom objects to dictionaries
        return prepare_for_json(obj.__dict__)
    else:
        # Return basic types as-is
        return obj

async def broadcast_game_state(game: Game):
    """Broadcast game state to all connected players."""
    for player in game.table.seats:
        if player is not None:
            await send_game_state(game, player.id)

async def start_next_hand(game: Game, delay_seconds: int = 3):
    """Wait for a delay and then start the next hand."""
    try:
        # Wait for the specified delay
        await asyncio.sleep(delay_seconds)
        
        # Check if the game is still in FINISHED state
        if game.state.status == GameStatus.FINISHED:
            # Reset the game
            game.reset_game()
            
            # Start a new hand
            game.start_hand()
            
            # Broadcast the new game state
            await broadcast_game_state(game)
            
            print(f"Started next hand for game {game.game_id}")
    except Exception as e:
        print(f"Error starting next hand: {e}")

# Run the server with: uvicorn ui.app:app --reload

# Run the server with: uvicorn ui.app:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)