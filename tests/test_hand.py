"""Unit tests for the Hand module."""
import unittest
from core.card import Card, Suit, Rank
from core.hand import Hand, HandEvaluator, HandRank


class TestHandEvaluator(unittest.TestCase):
    def test_royal_flush(self):
        """Test identification of a royal flush."""
        cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.TEN, Suit.HEARTS),
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.ROYAL_FLUSH)
        self.assertEqual(len(best_cards), 5)
    
    def test_straight_flush(self):
        """Test identification of a straight flush."""
        cards = [
            Card(Rank.NINE, Suit.CLUBS),
            Card(Rank.EIGHT, Suit.CLUBS),
            Card(Rank.SEVEN, Suit.CLUBS),
            Card(Rank.SIX, Suit.CLUBS),
            Card(Rank.FIVE, Suit.CLUBS),
            Card(Rank.TWO, Suit.HEARTS),
            Card(Rank.THREE, Suit.DIAMONDS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.STRAIGHT_FLUSH)
        self.assertEqual(len(best_cards), 5)
    
    def test_four_of_a_kind(self):
        """Test identification of four of a kind."""
        cards = [
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.DIAMONDS),
            Card(Rank.QUEEN, Suit.CLUBS),
            Card(Rank.QUEEN, Suit.SPADES),
            Card(Rank.TWO, Suit.HEARTS),
            Card(Rank.THREE, Suit.DIAMONDS),
            Card(Rank.FOUR, Suit.CLUBS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.FOUR_OF_A_KIND)
        self.assertEqual(len(best_cards), 5)
    
    def test_full_house(self):
        """Test identification of a full house."""
        cards = [
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.SIX, Suit.HEARTS),
            Card(Rank.SIX, Suit.DIAMONDS),
            Card(Rank.THREE, Suit.CLUBS),
            Card(Rank.FOUR, Suit.CLUBS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.FULL_HOUSE)
        self.assertEqual(len(best_cards), 5)
    
    def test_flush(self):
        """Test identification of a flush."""
        cards = [
            Card(Rank.ACE, Suit.DIAMONDS),
            Card(Rank.JACK, Suit.DIAMONDS),
            Card(Rank.NINE, Suit.DIAMONDS),
            Card(Rank.SEVEN, Suit.DIAMONDS),
            Card(Rank.THREE, Suit.DIAMONDS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.QUEEN, Suit.HEARTS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.FLUSH)
        self.assertEqual(len(best_cards), 5)
    
    def test_straight(self):
        """Test identification of a straight."""
        cards = [
            Card(Rank.EIGHT, Suit.HEARTS),
            Card(Rank.SEVEN, Suit.DIAMONDS),
            Card(Rank.SIX, Suit.CLUBS),
            Card(Rank.FIVE, Suit.SPADES),
            Card(Rank.FOUR, Suit.HEARTS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.STRAIGHT)
        self.assertEqual(len(best_cards), 5)
    
    def test_three_of_a_kind(self):
        """Test identification of three of a kind."""
        cards = [
            Card(Rank.TEN, Suit.HEARTS),
            Card(Rank.TEN, Suit.DIAMONDS),
            Card(Rank.TEN, Suit.CLUBS),
            Card(Rank.FIVE, Suit.SPADES),
            Card(Rank.THREE, Suit.HEARTS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.THREE_OF_A_KIND)
        self.assertEqual(len(best_cards), 5)
    
    def test_two_pair(self):
        """Test identification of two pair."""
        cards = [
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.JACK, Suit.DIAMONDS),
            Card(Rank.FOUR, Suit.CLUBS),
            Card(Rank.FOUR, Suit.SPADES),
            Card(Rank.THREE, Suit.HEARTS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.TWO_PAIR)
        self.assertEqual(len(best_cards), 5)
    
    def test_pair(self):
        """Test identification of a pair."""
        cards = [
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.DIAMONDS),
            Card(Rank.TEN, Suit.CLUBS),
            Card(Rank.EIGHT, Suit.SPADES),
            Card(Rank.THREE, Suit.HEARTS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.PAIR)
        self.assertEqual(len(best_cards), 5)
    
    def test_high_card(self):
        """Test identification of high card."""
        cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.NINE, Suit.SPADES),
            Card(Rank.SEVEN, Suit.HEARTS),
            Card(Rank.FIVE, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.HIGH_CARD)
        self.assertEqual(len(best_cards), 5)
    
    def test_ace_low_straight(self):
        """Test identification of A-2-3-4-5 straight."""
        cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.TWO, Suit.DIAMONDS),
            Card(Rank.THREE, Suit.CLUBS),
            Card(Rank.FOUR, Suit.SPADES),
            Card(Rank.FIVE, Suit.HEARTS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.QUEEN, Suit.DIAMONDS)
        ]
        
        rank, best_cards, description = HandEvaluator.evaluate(cards)
        self.assertEqual(rank, HandRank.STRAIGHT)
        self.assertEqual(len(best_cards), 5)


if __name__ == "__main__":
    unittest.main()