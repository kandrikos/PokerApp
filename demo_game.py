"""
Demo script to test the Texas Hold'em poker game functionality.
This runs a simple automated game with 6 players to verify the core logic.
"""
import time
import logging
import random
from typing import Dict, Any

from core.card import Card, Rank, Suit
from core.player import Player, PlayerStatus
from core.table import Table
from core.game import Game, GameAction, GameStatus, GameConfig, BettingRound


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("poker.demo")


def create_demo_game() -> Game:
    """Create a demo game with 6 players."""
    # Create table
    table = Table("demo_table", "Demo Table", max_seats=9)
    
    # Create players
    players = [
        Player(name=f"Player {i+1}", chips=1000)
        for i in range(6)
    ]
    
    # Add players to table
    for i, player in enumerate(players):
        table.add_player(player, position=i)
    
    # Create game config
    config = GameConfig(
        small_blind=5,
        big_blind=10,
        ante=0,
        min_players=2,
        max_players=9,
        starting_chips=1000
    )
    
    # Create game
    game = Game("demo_game", table, config)
    return game


def print_game_state(game: Game):
    """Print the current game state."""
    state = game.state
    
    print("\n" + "="*80)
    print(f"Game Status: {state.status.name}")
    print(f"Betting Round: {state.betting_round.name}")
    print(f"Pot: {state.pot}")
    print(f"Current Bet: {state.current_bet}")
    
    if state.community_cards:
        print(f"Community Cards: {' '.join(str(card) for card in state.community_cards)}")
    else:
        print("Community Cards: None")
    
    print("-"*80)
    print("Players:")
    for i, player in enumerate(game.table.seats):
        if player is None:
            continue
            
        status_symbol = {
            PlayerStatus.ACTIVE: "🟢",
            PlayerStatus.FOLDED: "🔴",
            PlayerStatus.ALL_IN: "⚪",
            PlayerStatus.SITTING_OUT: "⚫",
            PlayerStatus.ELIMINATED: "⚫"
        }.get(player.status, "?")
        
        position_marker = ""
        if player.is_dealer:
            position_marker += "D "
        if player.is_small_blind:
            position_marker += "SB "
        if player.is_big_blind:
            position_marker += "BB "
        
        current_marker = "→ " if i == state.current_player_idx else "  "
        
        cards_str = " ".join(str(card) for card in player.hand.cards) if player.hand.cards else "XX XX"
        
        print(f"{current_marker}{status_symbol} {player.name} ({position_marker}): ${player.chips} - Bet: ${player.current_bet} - Cards: {cards_str}")
    
    print("="*80 + "\n")


def simulate_player_action(game: Game, player_id: str) -> bool:
    """Simulate a player taking an action."""
    # Get available actions
    actions = game.get_available_actions(player_id)
    
    if not actions:
        return False
    
    # Get player
    player = None
    for p in game.table.seats:
        if p is not None and p.id == player_id:
            player = p
            break
    
    if player is None:
        return False
    
    # Decide on action (simple AI)
    # 1. If check is available, check 70% of the time
    # 2. If call is available and affordable, call 60% of the time
    # 3. If raise is available and affordable, raise 30% of the time
    # 4. Otherwise fold
    
    # Check if player has a strong hand (pair or better)
    has_strong_hand = False
    if len(player.hand.cards) == 2:
        if player.hand.cards[0].rank == player.hand.cards[1].rank:  # Pocket pair
            has_strong_hand = True
        elif player.hand.cards[0].rank.value >= Rank.QUEEN.value and player.hand.cards[1].rank.value >= Rank.QUEEN.value:
            has_strong_hand = True
    
    # Decision probabilities
    check_prob = 0.4
    call_prob = 0.5 if not has_strong_hand else 0.7
    raise_prob = 0.5 if not has_strong_hand else 0.8
    
    action_taken = False
    
    # Special case for big blind in preflop with no raises
    if player.is_big_blind and game.state.betting_round == BettingRound.PREFLOP and game.state.current_bet == player.current_bet:
        # If no one raised beyond the BB, check instead of folding (100% of the time)
        logger.info(f"Player {player.name} (BB) decides to check")
        action_taken = game.handle_player_action(player_id, GameAction.CHECK)
        return action_taken
    
    # If CHECK is available, always prioritize it over folding
    if GameAction.CHECK in actions:
        if random.random() < check_prob:
            logger.info(f"Player {player.name} decides to check")
            action_taken = game.handle_player_action(player_id, GameAction.CHECK)
        else:
            # Even if we don't "want" to check based on probability,
            # still check rather than fold when there's no bet to call
            logger.info(f"Player {player.name} decides to check (no bet to call)")
            action_taken = game.handle_player_action(player_id, GameAction.CHECK)
        return action_taken
    
    # Try to call
    if GameAction.CALL in actions and random.random() < call_prob:
        call_amount = actions[GameAction.CALL]
        # Check if affordable (less than 25% of stack unless strong hand)
        affordable = call_amount <= player.chips * (0.25 if not has_strong_hand else 0.5)
        
        if affordable or random.random() < 0.3:  # Sometimes call anyway
            logger.info(f"Player {player.name} decides to call {call_amount}")
            action_taken = game.handle_player_action(player_id, GameAction.CALL)
    
    # Try to raise
    elif GameAction.RAISE in actions and random.random() < raise_prob:
        min_raise = actions[GameAction.RAISE]
        # Calculate raise amount (1.5-3x the minimum)
        raise_amount = min(int(min_raise * (1.5 + random.random() * 1.5)), player.chips)
        
        logger.info(f"Player {player.name} decides to raise to {raise_amount}")
        action_taken = game.handle_player_action(player_id, GameAction.RAISE, raise_amount)
    
    # Try to bet
    elif GameAction.BET in actions and random.random() < raise_prob:
        min_bet = actions[GameAction.BET]
        # Calculate bet amount (1-3x the big blind)
        bet_amount = min(int(game.config.big_blind * (1 + random.random() * 2)), player.chips)
        bet_amount = max(bet_amount, min_bet)  # Ensure minimum bet
        
        logger.info(f"Player {player.name} decides to bet {bet_amount}")
        action_taken = game.handle_player_action(player_id, GameAction.BET, bet_amount)
    
    # Fold as a last resort (only possible if there's a bet to call)
    if not action_taken and GameAction.FOLD in actions:
        logger.info(f"Player {player.name} decides to fold")
        action_taken = game.handle_player_action(player_id, GameAction.FOLD)
    
    return action_taken


def play_hand(game: Game):
    """Play a single hand of poker."""
    # Start the hand
    if not game.start_hand():
        logger.error("Failed to start hand")
        return
    
    print_game_state(game)
    
    # Play until hand is finished
    while game.state.status in (GameStatus.BETTING, GameStatus.DEALING):
        # Get current player
        if game.state.current_player_idx < 0:
            break
            
        current_player = game.table.get_player_at_position(game.state.current_player_idx)
        if current_player is None:
            logger.warning("No current player")
            break
        
        # Simulate player action
        simulate_player_action(game, current_player.id)
        
        # Display game state
        print_game_state(game)
        
        # Small delay for readability
        time.sleep(0.5)
    
    # Print final state
    print_game_state(game)
    
    # Make sure we're ready for the next hand
    if game.state.status == GameStatus.FINISHED:
        game.reset_game()


def main():
    """Run the demo."""
    logger.info("Starting poker game demo")
    
    # Create demo game
    game = create_demo_game()
    
    # Play 3 hands
    for i in range(6):
        logger.info(f"Starting hand #{i+1}")
        play_hand(game)
        logger.info(f"Hand #{i+1} complete")
    
    logger.info("Demo complete")


if __name__ == "__main__":
    main()