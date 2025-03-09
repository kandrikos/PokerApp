#!/usr/bin/env python
"""
Interactive Texas Hold'em Poker simulator.
This tool allows you to control every aspect of a poker game's flow.
"""
import sys
import os
import random
from typing import List, Dict, Optional, Tuple, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.card import Card, Rank, Suit, Deck, create_deck
from core.player import Player, PlayerStatus
from core.table import Table
from core.game import Game, GameAction, GameStatus, GameConfig, BettingRound
from core.hand import HandEvaluator, HandRank

def parse_card(card_str):
    """Parse a card string like 'As' or '10c' into a Card object."""
    card_str = card_str.strip()
    
    # Handle the value part
    if card_str[0] == '1' and len(card_str) > 2:  # Handle '10'
        value = card_str[:2]
        suit_char = card_str[2]
    else:
        value = card_str[0]
        suit_char = card_str[1]
    
    # Map value to Rank
    rank_map = {
        '2': Rank.TWO,
        '3': Rank.THREE,
        '4': Rank.FOUR,
        '5': Rank.FIVE,
        '6': Rank.SIX,
        '7': Rank.SEVEN,
        '8': Rank.EIGHT,
        '9': Rank.NINE,
        '10': Rank.TEN,
        'J': Rank.JACK,
        'j': Rank.JACK,
        'Q': Rank.QUEEN,
        'q': Rank.QUEEN,
        'K': Rank.KING,
        'k': Rank.KING,
        'A': Rank.ACE,
        'a': Rank.ACE
    }
    
    # Map suit char to Suit
    suit_map = {
        'c': Suit.CLUBS,
        'C': Suit.CLUBS,
        'd': Suit.DIAMONDS,
        'D': Suit.DIAMONDS,
        'h': Suit.HEARTS,
        'H': Suit.HEARTS,
        's': Suit.SPADES,
        'S': Suit.SPADES,
        '♣': Suit.CLUBS,
        '♦': Suit.DIAMONDS,
        '♥': Suit.HEARTS,
        '♠': Suit.SPADES
    }
    
    try:
        rank = rank_map[value]
        suit = suit_map[suit_char]
        return Card(rank, suit)
    except KeyError:
        raise ValueError(f"Invalid card format: {card_str}")

def parse_cards(cards_str):
    """Parse a string of multiple cards."""
    card_strings = cards_str.split()
    return [parse_card(card_str) for card_str in card_strings]

class InteractivePokerSimulator:
    """Interactive Texas Hold'em Poker simulator."""
    
    def __init__(self):
        """Initialize the simulator."""
        self.game = None
        self.rigged_deck = []
        self.rigged_mode = False
        
    def setup_game(self):
        """Set up a new game."""
        print("Setting up a new poker game...")
        
        # Get number of players
        while True:
            try:
                num_players = int(input("Enter number of players (2-9): "))
                if 2 <= num_players <= 9:
                    break
                print("Number of players must be between 2 and 9.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Get starting chips
        while True:
            try:
                starting_chips = int(input("Enter starting chips (default 1000): ") or "1000")
                if starting_chips > 0:
                    break
                print("Starting chips must be positive.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Get blind values
        while True:
            try:
                small_blind = int(input("Enter small blind (default 5): ") or "5")
                big_blind = int(input("Enter big blind (default 10): ") or "10")
                if small_blind > 0 and big_blind >= small_blind:
                    break
                print("Big blind must be >= small blind, and both must be positive.")
            except ValueError:
                print("Please enter valid numbers.")
        
        # Create table
        table = Table("interactive_table", "Interactive Table", max_seats=9)
        
        # Create players
        players = []
        for i in range(num_players):
            name = input(f"Enter name for Player {i+1}: ") or f"Player {i+1}"
            player = Player(name=name, chips=starting_chips)
            players.append(player)
            table.add_player(player, position=i)
        
        # Create game config
        config = GameConfig(
            small_blind=small_blind,
            big_blind=big_blind,
            ante=0,
            min_players=2,
            max_players=9,
            starting_chips=starting_chips
        )
        
        # Create game
        self.game = Game("interactive_game", table, config)
        print(f"Game set up with {num_players} players.")
    
    def rig_deck(self):
        """Set up a rigged deck with predetermined cards."""
        self.rigged_deck = []
        self.rigged_mode = True
        
        print("\nRigging the deck. You can specify cards for players and community cards.")
        print("Use format like: Ah Kd Qc Js 10h")
        print("Enter a blank line when done.")
        
        # Get player hole cards
        for i, player in enumerate(self.game.table.seats):
            if player is None:
                continue
                
            while True:
                cards_str = input(f"Enter 2 cards for {player.name}: ")
                if not cards_str:
                    # Give random cards if not specified
                    break
                
                try:
                    cards = parse_cards(cards_str)
                    if len(cards) != 2:
                        print("Please enter exactly 2 cards.")
                        continue
                        
                    # Check for duplicate cards
                    if any(c in self.rigged_deck for c in cards):
                        print("Duplicate card detected. Please use unique cards.")
                        continue
                        
                    # Add cards to the rigged deck
                    self.rigged_deck.extend(cards)
                    break
                except Exception as e:
                    print(f"Error: {e}")
        
        # Get community cards
        while True:
            cards_str = input("Enter community cards (up to 5, or blank for random): ")
            if not cards_str:
                break
                
            try:
                cards = parse_cards(cards_str)
                if len(cards) > 5:
                    print("Please enter at most 5 community cards.")
                    continue
                    
                # Check for duplicate cards
                if any(c in self.rigged_deck for c in cards):
                    print("Duplicate card detected. Please use unique cards.")
                    continue
                    
                # Add cards to the rigged deck
                self.rigged_deck.extend(cards)
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Fill the rest of the deck with random cards
        all_cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        remaining_cards = [c for c in all_cards if c not in self.rigged_deck]
        random.shuffle(remaining_cards)
        
        # Complete the rigged deck
        self.rigged_deck.extend(remaining_cards)
        
        print(f"Deck rigged with {len(self.rigged_deck)} cards.")
    
    def _create_rigged_deck(self):
        """Create a rigged deck with predetermined cards."""
        if not self.rigged_mode or not self.rigged_deck:
            # Return normal shuffled deck if not in rigged mode
            return create_deck()
            
        # Create a deck with predetermined cards
        deck = Deck()
        deck.cards = list(self.rigged_deck)  # Make a copy
        
        # Reset rigged deck (used only once)
        self.rigged_deck = []
        self.rigged_mode = False
        
        return deck
    
    def start_hand(self):
        """Start a new hand."""
        if self.game is None:
            print("No game set up. Please set up a game first.")
            return
            
        if self.game.state.status != GameStatus.WAITING:
            print("Game is not in WAITING state. Resetting game...")
            self.game.reset_game()
        
        # Override the deck creation if in rigged mode
        if self.rigged_mode and self.rigged_deck:
            original_create_deck = create_deck
            
            # Monkey patch create_deck with our rigged version
            import core.card
            core.card.create_deck = self._create_rigged_deck
            
            # Start the hand
            result = self.game.start_hand()
            
            # Restore the original function
            core.card.create_deck = original_create_deck
        else:
            # Start with normal deck
            result = self.game.start_hand()
        
        if result:
            print("Hand started successfully.")
            self.print_game_state()
        else:
            print("Failed to start hand.")
    
    def print_game_state(self):
        """Print the current game state."""
        state = self.game.state
        
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
        for i, player in enumerate(self.game.table.seats):
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
        
        print("="*80)
        
        # Print available actions for current player
        if state.current_player_idx >= 0:
            current_player = self.game.table.get_player_at_position(state.current_player_idx)
            if current_player:
                actions = self.game.get_available_actions(current_player.id)
                if actions:
                    print(f"Available actions for {current_player.name}:")
                    for action, amount in actions.items():
                        if action in (GameAction.FOLD, GameAction.CHECK):
                            print(f"- {action.name}")
                        else:
                            print(f"- {action.name} (amount: {amount})")
        
        print()
    
    def handle_player_action(self):
        """Handle an action for the current player."""
        if self.game is None or self.game.state.status != GameStatus.BETTING:
            print("No active betting round.")
            return
            
        if self.game.state.current_player_idx < 0:
            print("No current player.")
            return
            
        current_player = self.game.table.get_player_at_position(self.game.state.current_player_idx)
        if current_player is None:
            print("No current player.")
            return
            
        actions = self.game.get_available_actions(current_player.id)
        if not actions:
            print("No available actions.")
            return
            
        print(f"Current player: {current_player.name}")
        print("Available actions:")
        
        # Display available actions
        action_list = []
        for i, (action, amount) in enumerate(actions.items(), 1):
            if action in (GameAction.FOLD, GameAction.CHECK):
                print(f"{i}. {action.name}")
            else:
                print(f"{i}. {action.name} (Min: {amount})")
            action_list.append((action, amount))
        
        # Get player choice
        while True:
            try:
                choice_idx = int(input("Enter action number: ")) - 1
                if 0 <= choice_idx < len(action_list):
                    action, min_amount = action_list[choice_idx]
                    break
                print("Invalid choice.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Get amount for betting actions
        amount = 0
        if action in (GameAction.BET, GameAction.RAISE, GameAction.ALL_IN):
            if action == GameAction.ALL_IN:
                amount = current_player.chips
            else:
                while True:
                    try:
                        amount = int(input(f"Enter amount (min {min_amount}): "))
                        if amount >= min_amount:
                            break
                        print(f"Amount must be at least {min_amount}.")
                    except ValueError:
                        print("Please enter a valid number.")
        
        # Execute the action
        result = self.game.handle_player_action(current_player.id, action, amount)
        
        if result:
            print(f"Action successful: {action.name}" + (f" {amount}" if amount > 0 else ""))
            # Check if we need to advance betting round or go to showdown
            if self.game.state.status in (GameStatus.SHOWDOWN, GameStatus.FINISHED):
                print("Hand is complete.")
                self.print_game_state()
                
                # Show all hands at showdown
                if self.game.state.status == GameStatus.SHOWDOWN:
                    self.print_showdown_results()
            else:
                self.print_game_state()
        else:
            print("Action failed.")
    
    def advance_betting_round(self):
        """Manually advance to the next betting round."""
        if self.game is None or self.game.state.status != GameStatus.BETTING:
            print("Cannot advance betting round - not in betting state.")
            return
            
        # Call the private method directly (not recommended in normal code)
        self.game._advance_betting_round()
        
        print("Advanced to next betting round.")
        self.print_game_state()
    
    def print_showdown_results(self):
        """Print the results of a showdown."""
        print("\n*** SHOWDOWN RESULTS ***")
        
        # Get active players
        active_players = [p for p in self.game.table.seats if p is not None and 
                         p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN)]
        
        if not active_players:
            print("No active players at showdown.")
            return
            
        # Evaluate each player's hand
        player_hands = {}
        for player in active_players:
            # Combine hole cards and community cards
            all_cards = player.hand.cards + self.game.state.community_cards
            
            # Evaluate the hand
            hand_rank, best_cards, description = HandEvaluator.evaluate(all_cards)
            
            player_hands[player.id] = {
                "player": player,
                "hand_rank": hand_rank,
                "best_cards": best_cards,
                "description": description
            }
            
            print(f"{player.name}: {description}")
            print(f"  Cards: {' '.join(str(card) for card in player.hand.cards)}")
            print(f"  Best 5: {' '.join(str(card) for card in best_cards)}")
        
        print("\nPot distribution:")
        # Get pot winners from action history (or we could recalculate)
        for action in self.game.state.action_history:
            if "wins" in action.__dict__:
                winner = next((p for p in active_players if p.id == action.player_id), None)
                if winner:
                    print(f"{winner.name} wins {action.amount} with {player_hands[winner.id]['description']}")
    
    def run(self):
        """Run the interactive simulator."""
        print("🃏 Interactive Texas Hold'em Poker Simulator 🃏")
        print("Control every aspect of a poker game's flow.")
        
        while True:
            print("\nMAIN MENU")
            print("1. Set up a new game")
            print("2. Rig the deck")
            print("3. Start a new hand")
            print("4. Player action")
            print("5. Advance betting round (debug)")
            print("6. Print game state")
            print("7. Reset game")
            print("8. Exit")
            
            choice = input("Enter choice: ")
            
            if choice == "1":
                self.setup_game()
            elif choice == "2":
                if self.game is None:
                    print("No game set up. Please set up a game first.")
                else:
                    self.rig_deck()
            elif choice == "3":
                self.start_hand()
            elif choice == "4":
                self.handle_player_action()
            elif choice == "5":
                self.advance_betting_round()
            elif choice == "6":
                if self.game is not None:
                    self.print_game_state()
                else:
                    print("No game set up.")
            elif choice == "7":
                if self.game is not None:
                    self.game.reset_game()
                    print("Game reset.")
                else:
                    print("No game set up.")
            elif choice == "8":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    simulator = InteractivePokerSimulator()
    simulator.run()