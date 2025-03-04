"""Unit tests for the Game module."""
import unittest
from unittest.mock import patch, MagicMock
from core.game import Game, GameStatus, GameAction, BettingRound, GameConfig
from core.player import Player, PlayerStatus
from core.table import Table
from core.card import Card, Rank, Suit


class TestGame(unittest.TestCase):
    def setUp(self):
        """Set up a game with a table and players for testing."""
        # Create table
        self.table = Table("test_table", "Test Table", max_seats=6)
        
        # Create players
        self.players = [
            Player(f"player{i}", name=f"Player {i}", chips=1000)
            for i in range(4)
        ]
        
        # Add players to table
        for i, player in enumerate(self.players):
            self.table.add_player(player, position=i)
            player.status = PlayerStatus.ACTIVE
        
        # Create game
        self.config = GameConfig(
            small_blind=5,
            big_blind=10,
            ante=0,
            min_players=2,
            max_players=6,
            starting_chips=1000
        )
        self.game = Game("test_game", self.table, self.config)
    
    def test_game_creation(self):
        """Test that games can be created with proper attributes."""
        self.assertEqual(self.game.game_id, "test_game")
        self.assertEqual(self.game.table, self.table)
        self.assertEqual(self.game.config, self.config)
        self.assertEqual(self.game.state.status, GameStatus.WAITING)
    
    @patch('core.game.create_deck')
    def test_start_hand(self, mock_create_deck):
        """Test starting a new hand."""
        # Mock deck
        mock_deck = MagicMock()
        mock_deck.deal.return_value = Card(Rank.ACE, Suit.SPADES)
        mock_create_deck.return_value = mock_deck
        
        # Start hand
        result = self.game.start_hand()
        
        # Check result
        self.assertTrue(result)
        self.assertEqual(self.game.state.status, GameStatus.BETTING)
        self.assertEqual(self.game.state.betting_round, BettingRound.PREFLOP)
        self.assertEqual(self.game.state.hand_number, 1)
        
        # Check dealer button
        self.assertEqual(self.table.dealer_position, 0)
        
        # Check blinds
        sb_player = self.table.get_player_at_position(1)
        bb_player = self.table.get_player_at_position(2)
        self.assertTrue(sb_player.is_small_blind)
        self.assertTrue(bb_player.is_big_blind)
        self.assertEqual(sb_player.current_bet, 5)
        self.assertEqual(bb_player.current_bet, 10)
        
        # Check pot
        self.assertEqual(self.game.state.pot, 15)
        
        # Check current bet
        self.assertEqual(self.game.state.current_bet, 10)
        
        # Each player should have 2 cards
        for player in self.players:
            self.assertEqual(len(player.hand.cards), 2)
    
    @patch('core.game.create_deck')
    def test_handle_player_action_fold(self, mock_create_deck):
        """Test handling a fold action."""
        # Mock deck
        mock_deck = MagicMock()
        mock_deck.deal.return_value = Card(Rank.ACE, Suit.SPADES)
        mock_create_deck.return_value = mock_deck
        
        # Start hand
        self.game.start_hand()
        
        # Set up current player
        self.game.state.current_player_idx = 3
        current_player = self.players[3]
        
        # Fold
        result = self.game.handle_player_action(current_player.id, GameAction.FOLD)
        
        # Check result
        self.assertTrue(result)
        self.assertEqual(current_player.status, PlayerStatus.FOLDED)
        self.assertTrue(current_player.has_acted)
    
    @patch('core.game.create_deck')
    def test_handle_player_action_check(self, mock_create_deck):
        """Test handling a check action."""
        # Mock deck
        mock_deck = MagicMock()
        mock_deck.deal.return_value = Card(Rank.ACE, Suit.SPADES)
        mock_create_deck.return_value = mock_deck
        
        # Start hand and advance to flop
        self.game.start_hand()
        self.game.state.betting_round = BettingRound.FLOP
        self.game.state.current_bet = 0
        
        # Reset player bets for new betting round
        for player in self.players:
            player.reset_for_new_betting_round()
            player.has_acted = False
        
        # Set up current player
        self.game.state.current_player_idx = 0
        current_player = self.players[0]
        
        # Check
        result = self.game.handle_player_action(current_player.id, GameAction.CHECK)
        
        # Check result
        self.assertTrue(result)
        self.assertTrue(current_player.has_acted)
        self.assertEqual(current_player.current_bet, 0)
    
    @patch('core.game.create_deck')
    def test_handle_player_action_call(self, mock_create_deck):
        """Test handling a call action."""
        # Mock deck
        mock_deck = MagicMock()
        mock_deck.deal.return_value = Card(Rank.ACE, Suit.SPADES)
        mock_create_deck.return_value = mock_deck
        
        # Start hand
        self.game.start_hand()
        
        # Set up current player
        self.game.state.current_player_idx = 3
        current_player = self.players[3]
        initial_chips = current_player.chips
        
        # Call
        result = self.game.handle_player_action(current_player.id, GameAction.CALL)
        
        # Check result
        self.assertTrue(result)
        self.assertTrue(current_player.has_acted)
        self.assertEqual(current_player.current_bet, 10)  # Match the BB
        self.assertEqual(current_player.chips, initial_chips - 10)
        self.assertEqual(self.game.state.pot, 25)  # SB + BB + Call
    
    @patch('core.game.create_deck')
    def test_handle_player_action_raise(self, mock_create_deck):
        """Test handling a raise action."""
        # Mock deck
        mock_deck = MagicMock()
        mock_deck.deal.return_value = Card(Rank.ACE, Suit.SPADES)
        mock_create_deck.return_value = mock_deck
        
        # Start hand
        self.game.start_hand()
        
        # Set up current player
        self.game.state.current_player_idx = 3
        current_player = self.players[3]
        initial_chips = current_player.chips
        
        # Raise to 30
        result = self.game.handle_player_action(current_player.id, GameAction.RAISE, 30)
        
        # Check result
        self.assertTrue(result)
        self.assertTrue(current_player.has_acted)
        self.assertEqual(current_player.current_bet, 30)
        self.assertEqual(current_player.chips, initial_chips - 30)
        self.assertEqual(self.game.state.pot, 45)  # SB + BB + Raise
        self.assertEqual(self.game.state.current_bet, 30)
        
        # Other players should need to act again
        for player in self.players[:3]:
            self.assertFalse(player.has_acted)
    
    @patch('core.game.create_deck')
    def test_get_available_actions(self, mock_create_deck):
        """Test getting available actions for a player."""
        # Mock deck
        mock_deck = MagicMock()
        mock_deck.deal.return_value = Card(Rank.ACE, Suit.SPADES)
        mock_create_deck.return_value = mock_deck
        
        # Start hand
        self.game.start_hand()
        
        # Set up current player (after the BB)
        self.game.state.current_player_idx = 3
        current_player = self.players[3]
        
        # Get available actions
        actions = self.game.get_available_actions(current_player.id)
        
        # Preflop after BB, player should be able to fold, call, or raise
        self.assertIn(GameAction.FOLD, actions)
        self.assertIn(GameAction.CALL, actions)
        self.assertIn(GameAction.RAISE, actions)
        self.assertNotIn(GameAction.CHECK, actions)
        
        # Call amount should be the big blind
        self.assertEqual(actions[GameAction.CALL], 10)
        
        # Minimum raise should be double the big blind
        self.assertEqual(actions[GameAction.RAISE], 20)
        
        # Simulate moving to flop with no bets
        self.game.state.betting_round = BettingRound.FLOP
        self.game.state.current_bet = 0
        for player in self.players:
            player.reset_for_new_betting_round()
        
        # Get available actions again
        actions = self.game.get_available_actions(current_player.id)
        
        # On flop with no bets, player should be able to check or bet
        self.assertIn(GameAction.CHECK, actions)
        self.assertIn(GameAction.BET, actions)
        self.assertNotIn(GameAction.FOLD, actions)  # Can't fold when can check
        self.assertNotIn(GameAction.CALL, actions)
        self.assertNotIn(GameAction.RAISE, actions)
    
    @patch('core.game.create_deck')
    def test_reset_game(self, mock_create_deck):
        """Test resetting the game."""
        # Mock deck
        mock_deck = MagicMock()
        mock_deck.deal.return_value = Card(Rank.ACE, Suit.SPADES)
        mock_create_deck.return_value = mock_deck
        
        # Start hand
        self.game.start_hand()
        
        # Advance to showdown
        self.game.state.status = GameStatus.SHOWDOWN
        self.game.state.betting_round = BettingRound.SHOWDOWN
        self.game.state.pot = 100
        self.game.state.current_bet = 20
        
        # Reset game
        self.game.reset_game()
        
        # Check reset state
        self.assertEqual(self.game.state.status, GameStatus.WAITING)
        self.assertEqual(len(self.game.state.community_cards), 0)
        self.assertEqual(self.game.state.pot, 0)
        self.assertEqual(self.game.state.current_bet, 0)
        self.assertEqual(self.game.state.min_raise, self.config.big_blind)
        
        # Players should be reset
        for player in self.players:
            self.assertEqual(player.current_bet, 0)
            self.assertEqual(player.total_bet, 0)
            self.assertEqual(len(player.hand.cards), 0)


if __name__ == "__main__":
    unittest.main()