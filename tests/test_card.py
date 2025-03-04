"""Unit tests for the Card module."""
import unittest
from core.card import Card, Suit, Rank, Deck


class TestCard(unittest.TestCase):
    def test_card_creation(self):
        """Test that cards can be created with proper attributes."""
        card = Card(Rank.ACE, Suit.SPADES)
        self.assertEqual(card.rank, Rank.ACE)
        self.assertEqual(card.suit, Suit.SPADES)
        self.assertEqual(card.value, 14)
    
    def test_card_representation(self):
        """Test the string representation of cards."""
        card = Card(Rank.ACE, Suit.HEARTS)
        self.assertEqual(str(card), "A♥")
        
        card = Card(Rank.TEN, Suit.CLUBS)
        self.assertEqual(str(card), "10♣")
    
    def test_card_equality(self):
        """Test that cards can be compared for equality."""
        card1 = Card(Rank.KING, Suit.DIAMONDS)
        card2 = Card(Rank.KING, Suit.DIAMONDS)
        card3 = Card(Rank.KING, Suit.HEARTS)
        
        self.assertEqual(card1, card2)
        self.assertNotEqual(card1, card3)
    
    def test_card_hash(self):
        """Test that cards can be used as dictionary keys."""
        card1 = Card(Rank.QUEEN, Suit.CLUBS)
        card2 = Card(Rank.QUEEN, Suit.CLUBS)
        
        card_dict = {card1: "test"}
        self.assertEqual(card_dict[card2], "test")


class TestDeck(unittest.TestCase):
    def test_deck_creation(self):
        """Test that a new deck has 52 cards."""
        deck = Deck()
        self.assertEqual(len(deck.cards), 52)
    
    def test_deck_deal(self):
        """Test dealing cards from the deck."""
        deck = Deck()
        initial_count = len(deck.cards)
        
        card = deck.deal()
        self.assertIsNotNone(card)
        self.assertEqual(len(deck.cards), initial_count - 1)
        
        # Deal all remaining cards
        for _ in range(initial_count - 1):
            deck.deal()
        
        # Deck should be empty
        self.assertEqual(len(deck.cards), 0)
        self.assertIsNone(deck.deal())
    
    def test_deck_shuffle(self):
        """Test that shuffling changes the order of cards."""
        deck1 = Deck()
        deck2 = Deck()
        
        # Before shuffling, decks should have same order
        self.assertEqual([str(c) for c in deck1.cards], [str(c) for c in deck2.cards])
        
        # After shuffling, order should very likely be different
        deck2.shuffle()
        
        # There's a tiny chance this could fail if the shuffle doesn't change anything
        # but that's extremely unlikely with 52 cards
        self.assertNotEqual([str(c) for c in deck1.cards], [str(c) for c in deck2.cards])
    
    def test_deck_reset(self):
        """Test resetting the deck."""
        deck = Deck()
        original_cards = [str(c) for c in deck.cards]
        
        # Deal some cards
        for _ in range(10):
            deck.deal()
        
        self.assertEqual(len(deck.cards), 42)
        
        # Reset the deck
        deck.reset()
        
        self.assertEqual(len(deck.cards), 52)
        self.assertEqual([str(c) for c in deck.cards], original_cards)


if __name__ == "__main__":
    unittest.main()