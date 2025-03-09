#!/usr/bin/env python
"""
CLI-based Texas Hold'em Poker Game.
This script allows manual control of all player actions for testing purposes.
"""
import sys
import os
import time
import random
from typing import List, Dict, Optional, Tuple, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.card import Card, Rank, Suit, Deck, create_deck
from core.player import Player, PlayerStatus
from core.table import Table
from core.game import Game, GameAction, GameStatus, GameConfig, BettingRound
from core.hand import HandEvaluator, HandRank

class PokerCLI:
    """Command-line interface for playing Texas Hold'em Poker."""
    
    def __init__(self):
        """Initialize the CLI poker game."""
        self.game = None
        self.table = None
        self.rigged_deck = []
        self.rigged_mode = False
        self.auto_advance = False
        self.custom_player_names = ["Alice", "Bob", "Charlie", "Dave"]
    
    def setup_game(self, num_players=4, starting_chips=1000, small_blind=5, big_blind=10):
        """Set up a new game with specified parameters."""
        print(f"Setting up a new poker game with {num_players} players...")
        
        # Create table
        self.table = Table("cli_table", "CLI Table", max_seats=9)
        
        # Create players
        players = []
        for i in range(num_players):
            player_name = input(f"Enter name for Player {i+1} (default: {self.custom_player_names[i]}): ") or self.custom_player_names[i]
            player = Player(name=player_name, chips=starting_chips)
            players.append(player)
            self.table.add_player(player, position=i)
        
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
        self.game = Game("cli_game", self.table, config)
        print(f"Game set up with {num_players} players, {starting_chips} chips each, blinds {small_blind}/{big_blind}.")
    
    def print_cards(self, cards):
        """Pretty-print a list of cards."""
        return " ".join(str(card) for card in cards)
    
    def print_game_state(self):
        """Print the current game state in a well-formatted way."""
        if not self.game:
            print("No game in progress.")
            return
            
        state = self.game.state
        
        print("\n" + "="*80)
        print(f"Game Status: {state.status.name}")
        print(f"Betting Round: {state.betting_round.name}")
        print(f"Total Pot: ${state.pot}")
        
        # Display pot information
        if hasattr(state, 'main_pot') and state.main_pot > 0:
            print(f"Main Pot: ${state.main_pot}")
            
            if hasattr(state, 'side_pots') and state.side_pots:
                for i, pot in enumerate(state.side_pots, 1):
                    eligible_players = pot.get("eligible_players", [])
                    player_names = []
                    for player_id in eligible_players:
                        player = next((p for p in self.table.seats if p is not None and p.id == player_id), None)
                        if player:
                            player_names.append(player.name)
                    
                    print(f"Side Pot {i}: ${pot['amount']} - Eligible: {', '.join(player_names)}")
        
        print("-"*80)
        
        # Display community cards
        if state.community_cards:
            print(f"Community Cards: {self.print_cards(state.community_cards)}")
        else:
            print("Community Cards: None")
        
        print("-"*80)
        
        # Display player information
        print("Players:")
        for i, player in enumerate(self.table.seats):
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
            
            cards_str = self.print_cards(player.hand.cards) if player.hand.cards else ""
            
            print(f"{current_marker}{status_symbol} {player.name} ({position_marker}): ${player.chips} - Bet: ${player.current_bet}")
            print(f"     Cards: {cards_str}")
        
        print("="*80)
        
        # Display current player and available actions
        if state.status == GameStatus.BETTING and state.current_player_idx >= 0:
            current_player = self.table.get_player_at_position(state.current_player_idx)
            if current_player:
                print(f"Current Player: {current_player.name}")
                
                actions = self.game.get_available_actions(current_player.id)
                if actions:
                    print("Available Actions:")
                    for action, amount in actions.items():
                        if action in (GameAction.FOLD, GameAction.CHECK):
                            print(f"- {action.name}")
                        else:
                            print(f"- {action.name} (Min: ${amount})")
                print()
    
    def print_hand_result(self):
        """Print the results of the hand."""
        if not self.game or self.game.state.status not in (GameStatus.SHOWDOWN, GameStatus.FINISHED):
            return
        
        print("\n" + "="*40 + " HAND RESULTS " + "="*40)
        
        # Get active players
        active_players = [p for p in self.table.seats if p is not None and 
                         p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN)]
        
        if not active_players:
            print("No active players at showdown.")
            return
        
        # If only one active player, they win uncontested
        if len(active_players) == 1:
            winner = active_players[0]
            print(f"{winner.name} wins ${self.game.state.pot} uncontested")
            return
        
        # Evaluate each player's hand
        print("Player Hands:")
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
            print(f"  Cards: {self.print_cards(player.hand.cards)}")
            print(f"  Best 5: {self.print_cards(best_cards)}")
        
        # Determine winners
        best_rank = HandRank.HIGH_CARD
        for hand_info in player_hands.values():
            if hand_info["hand_rank"] > best_rank:
                best_rank = hand_info["hand_rank"]
        
        best_players = [info for info in player_hands.values() if info["hand_rank"] == best_rank]
        
        if len(best_players) == 1:
            winner = best_players[0]["player"]
            print(f"\n{winner.name} wins ${self.game.state.pot} with {best_players[0]['description']}")
        else:
            # Compare kickers
            best_kicker = None
            tied_winners = []
            
            for player_info in best_players:
                player = player_info["player"]
                best_cards = player_info["best_cards"]
                kicker = HandEvaluator._get_kicker_key(best_cards, best_rank)
                
                if best_kicker is None or kicker > best_kicker:
                    best_kicker = kicker
                    tied_winners = [player]
                elif kicker == best_kicker:
                    tied_winners.append(player)
            
            if len(tied_winners) == 1:
                winner = tied_winners[0]
                print(f"\n{winner.name} wins ${self.game.state.pot} with {player_hands[winner.id]['description']}")
            else:
                # True tie
                winner_names = [p.name for p in tied_winners]
                split_amount = self.game.state.pot // len(tied_winners)
                print(f"\nTie between {', '.join(winner_names)}. Each wins ${split_amount}.")
        
        print("="*90)
    
    def rig_deck(self):
        """Set up a rigged deck with predetermined cards."""
        self.rigged_deck = []
        self.rigged_mode = True
        
        print("\nRigging the deck. You can specify cards for players and community cards.")
        print("Use format like: Ah Kd Qc Js 10h")
        print("Enter a blank line when done.")
        
        # Get player hole cards
        for i, player in enumerate(self.table.seats):
            if player is None:
                continue
                
            while True:
                cards_str = input(f"Enter 2 cards for {player.name} (or blank for random): ")
                if not cards_str:
                    # Give random cards if not specified
                    break
                
                try:
                    cards = self.parse_cards(cards_str)
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
                cards = self.parse_cards(cards_str)
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
    
    def parse_cards(self, cards_str):
        """Parse a string of cards into Card objects."""
        card_strings = cards_str.split()
        cards = []
        
        for card_str in card_strings:
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
                cards.append(Card(rank, suit))
            except KeyError:
                raise ValueError(f"Invalid card format: {card_str}")
        
        return cards
    
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
    
    def handle_player_action(self):
        """Handle an action for the current player."""
        if self.game is None or self.game.state.status != GameStatus.BETTING:
            print("No active betting round.")
            return False
            
        if self.game.state.current_player_idx < 0:
            print("No current player.")
            return False
            
        current_player = self.table.get_player_at_position(self.game.state.current_player_idx)
        if current_player is None:
            print("No current player.")
            return False
            
        actions = self.game.get_available_actions(current_player.id)
        if not actions:
            print("No available actions.")
            return False
            
        print(f"Current player: {current_player.name}")
        print("Available actions:")
        
        # Display available actions
        action_list = []
        for i, (action, amount) in enumerate(actions.items(), 1):
            if action in (GameAction.FOLD, GameAction.CHECK):
                print(f"{i}. {action.name}")
            else:
                print(f"{i}. {action.name} (Min: ${amount})")
            action_list.append((action, amount))
        
        # Get player choice
        while True:
            try:
                choice = input("Enter action number (or 'q' to quit): ")
                if choice.lower() == 'q':
                    return False
                    
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(action_list):
                    action, min_amount = action_list[choice_idx]
                    break
                print("Invalid choice.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Get amount for betting actions
        amount = 0
        if action in (GameAction.BET, GameAction.RAISE):
            while True:
                try:
                    amount_input = input(f"Enter amount (min ${min_amount}, max ${current_player.chips}): ")
                    amount = int(amount_input)
                    if amount >= min_amount and amount <= current_player.chips:
                        break
                    print(f"Amount must be between ${min_amount} and ${current_player.chips}.")
                except ValueError:
                    print("Please enter a valid number.")
        elif action == GameAction.ALL_IN:
            amount = current_player.chips
            print(f"Going all-in for ${amount}")
        
        # Execute the action
        result = self.game.handle_player_action(current_player.id, action, amount)
        
        if result:
            print(f"Action successful: {action.name}" + (f" ${amount}" if amount > 0 else ""))
            # Check if we need to advance betting round or go to showdown
            if self.game.state.status in (GameStatus.SHOWDOWN, GameStatus.FINISHED):
                print("Hand is complete.")
                self.print_game_state()
                self.print_hand_result()
                return True
            else:
                self.print_game_state()
                return True
        else:
            print("Action failed.")
            return False
    
    def auto_play_hand(self):
        """Automatically play a hand with simple AI decisions."""
        print("Auto-playing hand...")
        self.auto_advance = True
        
        # Auto-play until hand is complete
        while self.game.state.status == GameStatus.BETTING:
            if not self.handle_player_action_auto():
                break
            time.sleep(0.5)  # Slight delay between actions
        
        self.auto_advance = False
    
    def handle_player_action_auto(self):
        """Automatically handle current player's action with simple AI."""
        if self.game is None or self.game.state.status != GameStatus.BETTING:
            return False
            
        if self.game.state.current_player_idx < 0:
            return False
            
        current_player = self.table.get_player_at_position(self.game.state.current_player_idx)
        if current_player is None:
            return False
            
        actions = self.game.get_available_actions(current_player.id)
        if not actions:
            return False
        
        # Simple AI decision
        action = None
        amount = 0
        
        # Choose action based on available options
        if GameAction.CHECK in actions:
            # Always check if possible
            action = GameAction.CHECK
        elif GameAction.CALL in actions:
            # Call if the call amount is less than 25% of chips
            call_amount = actions[GameAction.CALL]
            if call_amount <= current_player.chips * 0.25:
                action = GameAction.CALL
            else:
                action = GameAction.FOLD
        elif GameAction.FOLD in actions:
            action = GameAction.FOLD
        
        if action is None:
            # Default to fold
            action = GameAction.FOLD
        
        # Execute the action
        print(f"Auto-action for {current_player.name}: {action.name}" + (f" ${amount}" if amount > 0 else ""))
        result = self.game.handle_player_action(current_player.id, action, amount)
        
        if result:
            # Check if we need to advance betting round or go to showdown
            if self.game.state.status in (GameStatus.SHOWDOWN, GameStatus.FINISHED):
                self.print_game_state()
                self.print_hand_result()
                return False
            else:
                self.print_game_state()
                return True
        else:
            print("Action failed.")
            return False
    
    def run(self):
        """Run the CLI poker game."""
        print("🃏 CLI Texas Hold'em Poker Game 🃏")
        print("Control all player actions from the command line.")
        
        # Set up initial game with default values
        self.setup_game(num_players=4, starting_chips=1000, small_blind=5, big_blind=10)
        
        while True:
            print("\nMAIN MENU")
            print("1. Start new hand")
            print("2. Rig the deck")
            print("3. Player action")
            print("4. Auto-play hand")
            print("5. Reset game")
            print("6. Show game state")
            print("7. Setup new game")
            print("8. Exit")
            
            choice = input("Enter choice: ")
            
            if choice == "1":
                self.start_hand()
            elif choice == "2":
                self.rig_deck()
            elif choice == "3":
                if self.game and self.game.state.status == GameStatus.BETTING:
                    keep_acting = True
                    while keep_acting:
                        keep_acting = self.handle_player_action()
                else:
                    print("No active betting round.")
            elif choice == "4":
                if self.game and self.game.state.status == GameStatus.BETTING:
                    self.auto_play_hand()
                else:
                    print("No active betting round.")
            elif choice == "5":
                if self.game:
                    self.game.reset_game()
                    print("Game reset.")
                else:
                    print("No game to reset.")
            elif choice == "6":
                if self.game:
                    self.print_game_state()
                else:
                    print("No game in progress.")
            elif choice == "7":
                num_players = int(input("Enter number of players (2-9): ") or "4")
                starting_chips = int(input("Enter starting chips (default 1000): ") or "1000")
                small_blind = int(input("Enter small blind (default 5): ") or "5")
                big_blind = int(input("Enter big blind (default 10): ") or "10")
                self.setup_game(num_players, starting_chips, small_blind, big_blind)
            elif choice == "8":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    cli = PokerCLI()
    cli.run()