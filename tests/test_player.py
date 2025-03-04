"""Unit tests for the Player module."""
import unittest
from core.player import Player, PlayerStatus
from core.card import Card, Rank, Suit


class TestPlayer(unittest.TestCase):
    def setUp(self):
        """Set up a player for testing."""
        self.player = Player(name="TestPlayer", chips=1000)
    
    def test_player_creation(self):
        """Test that players can be created with proper attributes."""
        self.assertEqual(self.player.name, "TestPlayer")
        self.assertEqual(self.player.chips, 1000)
        self.assertEqual(self.player.status, PlayerStatus.SITTING_OUT)
        self.assertEqual(self.player.current_bet, 0)
    
    def test_receive_card(self):
        """Test that a player can receive cards."""
        card = Card(Rank.ACE, Suit.SPADES)
        self.player.receive_card(card)
        
        self.assertEqual(len(self.player.hand.cards), 1)
        self.assertEqual(self.player.hand.cards[0], card)
    
    def test_place_bet(self):
        """Test that a player can place a bet."""
        # Normal bet
        amount = self.player.place_bet(100)
        self.assertEqual(amount, 100)
        self.assertEqual(self.player.chips, 900)
        self.assertEqual(self.player.current_bet, 100)
        self.assertEqual(self.player.total_bet, 100)
        
        # Bet more than available chips
        amount = self.player.place_bet(1000)
        self.assertEqual(amount, 900)  # Only remaining chips
        self.assertEqual(self.player.chips, 0)
        self.assertEqual(self.player.current_bet, 1000)
        self.assertEqual(self.player.total_bet, 1000)
        self.assertEqual(self.player.status, PlayerStatus.ALL_IN)
    
    def test_fold(self):
        """Test that a player can fold."""
        self.player.status = PlayerStatus.ACTIVE
        self.player.fold()
        self.assertEqual(self.player.status, PlayerStatus.FOLDED)
    
    def test_sit_in_out(self):
        """Test that a player can sit in and out."""
        # Sit in
        self.player.sit_in()
        self.assertEqual(self.player.status, PlayerStatus.ACTIVE)
        
        # Sit out
        self.player.sit_out()
        self.assertEqual(self.player.status, PlayerStatus.SITTING_OUT)
    
    def test_reset_for_new_hand(self):
        """Test resetting player for a new hand."""
        # Set up some state
        self.player.status = PlayerStatus.ACTIVE
        self.player.current_bet = 50
        self.player.total_bet = 200
        self.player.is_dealer = True
        self.player.is_small_blind = False
        self.player.is_big_blind = False
        self.player.has_acted = True
        
        # Add cards to hand
        self.player.receive_card(Card(Rank.ACE, Suit.SPADES))
        self.player.receive_card(Card(Rank.KING, Suit.HEARTS))
        
        # Reset for new hand
        self.player.reset_for_new_hand()
        
        # Check reset state
        self.assertEqual(self.player.status, PlayerStatus.ACTIVE)
        self.assertEqual(self.player.current_bet, 0)
        self.assertEqual(self.player.total_bet, 0)
        self.assertFalse(self.player.is_dealer)
        self.assertFalse(self.player.is_small_blind)
        self.assertFalse(self.player.is_big_blind)
        self.assertFalse(self.player.has_acted)
        self.assertEqual(len(self.player.hand.cards), 0)
    
    def test_reset_for_new_betting_round(self):
        """Test resetting player for a new betting round."""
        # Set up some state
        self.player.current_bet = 50
        self.player.has_acted = True
        
        # Reset for new betting round
        self.player.reset_for_new_betting_round()
        
        # Check reset state
        self.assertEqual(self.player.current_bet, 0)
        self.assertFalse(self.player.has_acted)
    
    def test_can_act(self):
        """Test checking if a player can act."""
        # Player is active with chips
        self.player.status = PlayerStatus.ACTIVE
        self.player.has_acted = False
        self.assertTrue(self.player.can_act())
        
        # Player has already acted
        self.player.has_acted = True
        self.assertFalse(self.player.can_act())
        
        # Player has no chips
        self.player.has_acted = False
        self.player.chips = 0
        self.assertFalse(self.player.can_act())
        
        # Player is folded
        self.player.chips = 1000
        self.player.status = PlayerStatus.FOLDED
        self.assertFalse(self.player.can_act())
    
    def test_update_statistics(self):
        """Test updating player statistics."""
        # Win a hand
        self.player.update_statistics(won=True, amount=500, hand_description="Two Pair, Aces and Kings")
        
        self.assertEqual(self.player.statistics["hands_played"], 1)
        self.assertEqual(self.player.statistics["hands_won"], 1)
        self.assertEqual(self.player.statistics["total_winnings"], 500)
        self.assertEqual(self.player.statistics["biggest_pot"], 500)
        self.assertEqual(self.player.statistics["best_hand"], "Two Pair, Aces and Kings")
        
        # Lose a hand with better hand
        self.player.update_statistics(won=False, amount=0, hand_description="Full House, Aces full of Kings")
        
        self.assertEqual(self.player.statistics["hands_played"], 2)
        self.assertEqual(self.player.statistics["hands_won"], 1)
        self.assertEqual(self.player.statistics["total_winnings"], 500)
        self.assertEqual(self.player.statistics["best_hand"], "Full House, Aces full of Kings")
        
        # Win a bigger pot
        self.player.update_statistics(won=True, amount=800, hand_description="Two Pair, Queens and Jacks")
        
        self.assertEqual(self.player.statistics["hands_played"], 3)
        self.assertEqual(self.player.statistics["hands_won"], 2)
        self.assertEqual(self.player.statistics["total_winnings"], 1300)
        self.assertEqual(self.player.statistics["biggest_pot"], 800)
        self.assertEqual(self.player.statistics["best_hand"], "Full House, Aces full of Kings")


if __name__ == "__main__":
    unittest.main()