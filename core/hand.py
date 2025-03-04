"""
Hand evaluation module for Texas Hold'em Poker.
Implements HandRank enum and hand evaluation functions.
"""
from __future__ import annotations
from enum import IntEnum
from typing import List, Tuple, Dict, Set, Optional
from collections import Counter
from itertools import combinations

from core.card import Card, Rank, Suit


class HandRank(IntEnum):
    """
    Hand rankings in poker, from highest to lowest.
    Higher enum values represent stronger hands.
    """
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


class Hand:
    """
    Represents a poker hand with evaluation logic.
    """
    def __init__(self, cards: List[Card] = None):
        """Initialize a hand with the given cards."""
        self.cards = cards or []

    def add_card(self, card: Card) -> None:
        """Add a card to the hand."""
        self.cards.append(card)

    def clear(self) -> None:
        """Clear all cards from the hand."""
        self.cards = []

    def __repr__(self) -> str:
        """String representation of the hand."""
        return " ".join(str(card) for card in self.cards)


class HandEvaluator:
    """
    Evaluates poker hands to determine the best 5-card combination.
    """
    @staticmethod
    def evaluate(cards: List[Card]) -> Tuple[HandRank, List[Card], str]:
        """
        Evaluate the best 5-card poker hand from the given cards.
        
        Args:
            cards: A list of cards (usually 7 cards in Texas Hold'em: 2 hole cards + 5 community cards)
            
        Returns:
            A tuple containing:
            - The hand rank enum
            - The 5 cards that make up the best hand
            - A human-readable description of the hand
        """
        if len(cards) < 5:
            raise ValueError("At least 5 cards are required for evaluation")

        # Generate all possible 5-card combinations
        five_card_combinations = list(combinations(cards, 5))
        
        # Evaluate each combination
        best_rank = HandRank.HIGH_CARD
        best_hand = None
        best_cards = []
        best_key = []
        
        for combo in five_card_combinations:
            combo_cards = list(combo)
            rank, description = HandEvaluator._evaluate_five_card_hand(combo_cards)
            
            # Generate kicker key for proper comparison
            current_key = HandEvaluator._get_kicker_key(combo_cards, rank)
            
            # Update best hand if this one is better
            if rank > best_rank:
                best_rank = rank
                best_hand = description
                best_cards = combo_cards
                best_key = current_key
            elif rank == best_rank:
                # If same rank, compare kickers
                if current_key > best_key:
                    best_cards = combo_cards
                    best_hand = description
                    best_key = current_key
        
        return best_rank, best_cards, best_hand

    @staticmethod
    def _evaluate_five_card_hand(cards: List[Card]) -> Tuple[HandRank, str]:
        """Evaluate a specific 5-card hand."""
        if len(cards) != 5:
            raise ValueError("Exactly 5 cards are required for evaluation")

        # Sort cards by rank (higher ranks first)
        sorted_cards = sorted(cards, key=lambda c: c.value, reverse=True)
        
        # Check for flush
        is_flush = len(set(card.suit for card in cards)) == 1
        
        # Check for straight
        ranks = [card.value for card in sorted_cards]
        is_straight = HandEvaluator._is_straight(ranks)
        
        # Handle Ace-low straight (A-2-3-4-5)
        if not is_straight and sorted(ranks) == [2, 3, 4, 5, 14]:
            is_straight = True
            # Move the Ace to the end for a low straight
            for i, card in enumerate(sorted_cards):
                if card.rank == Rank.ACE:
                    sorted_cards.append(sorted_cards.pop(i))
                    break
            ranks = [card.value for card in sorted_cards]
        
        # Count frequencies of ranks
        rank_counts = Counter(card.value for card in cards)
        rank_count_values = sorted(rank_counts.values(), reverse=True)
        
        # Check for Royal Flush
        if is_flush and is_straight and sorted_cards[0].rank == Rank.ACE and sorted_cards[1].rank == Rank.KING:
            return HandRank.ROYAL_FLUSH, "Royal Flush"
        
        # Check for Straight Flush
        if is_flush and is_straight:
            high_card = sorted_cards[0].rank.symbol
            return HandRank.STRAIGHT_FLUSH, f"Straight Flush, {high_card} high"
        
        # Check for Four of a Kind
        if rank_count_values[0] == 4:
            quads_rank = next(r for r, c in rank_counts.items() if c == 4)
            quads_symbol = next(c.rank.symbol for c in cards if c.value == quads_rank)
            return HandRank.FOUR_OF_A_KIND, f"Four of a Kind, {quads_symbol}s"
        
        # Check for Full House
        if rank_count_values[0] == 3 and rank_count_values[1] == 2:
            trips_rank = next(r for r, c in rank_counts.items() if c == 3)
            pair_rank = next(r for r, c in rank_counts.items() if c == 2)
            trips_symbol = next(c.rank.symbol for c in cards if c.value == trips_rank)
            pair_symbol = next(c.rank.symbol for c in cards if c.value == pair_rank)
            return HandRank.FULL_HOUSE, f"Full House, {trips_symbol}s full of {pair_symbol}s"
        
        # Check for Flush
        if is_flush:
            high_card = sorted_cards[0].rank.symbol
            return HandRank.FLUSH, f"Flush, {high_card} high"
        
        # Check for Straight
        if is_straight:
            high_card = sorted_cards[0].rank.symbol
            return HandRank.STRAIGHT, f"Straight, {high_card} high"
        
        # Check for Three of a Kind
        if rank_count_values[0] == 3:
            trips_rank = next(r for r, c in rank_counts.items() if c == 3)
            trips_symbol = next(c.rank.symbol for c in cards if c.value == trips_rank)
            return HandRank.THREE_OF_A_KIND, f"Three of a Kind, {trips_symbol}s"
        
        # Check for Two Pair
        if rank_count_values[0] == 2 and rank_count_values[1] == 2:
            pairs = [r for r, c in rank_counts.items() if c == 2]
            pairs.sort(reverse=True)
            high_pair_symbol = next(c.rank.symbol for c in cards if c.value == pairs[0])
            low_pair_symbol = next(c.rank.symbol for c in cards if c.value == pairs[1])
            return HandRank.TWO_PAIR, f"Two Pair, {high_pair_symbol}s and {low_pair_symbol}s"
        
        # Check for Pair
        if rank_count_values[0] == 2:
            pair_rank = next(r for r, c in rank_counts.items() if c == 2)
            pair_symbol = next(c.rank.symbol for c in cards if c.value == pair_rank)
            return HandRank.PAIR, f"Pair of {pair_symbol}s"
        
        # High Card
        high_card = sorted_cards[0].rank.symbol
        return HandRank.HIGH_CARD, f"High Card, {high_card}"

    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        """Check if the given ranks form a straight."""
        # Sort ranks in descending order
        sorted_ranks = sorted(set(ranks), reverse=True)
        
        # Check for 5 consecutive ranks
        if len(sorted_ranks) >= 5:
            for i in range(len(sorted_ranks) - 4):
                if sorted_ranks[i] - sorted_ranks[i + 4] == 4:
                    return True
                
        return False

    @staticmethod
    def _get_kicker_key(cards: List[Card], hand_rank: HandRank) -> List[int]:
        """
        Generate a key for comparing hands of the same rank.
        This key prioritizes the cards that make up the hand, then kickers.
        """
        sorted_cards = sorted(cards, key=lambda c: c.value, reverse=True)
        rank_counts = Counter(card.value for card in cards)
        
        if hand_rank == HandRank.FOUR_OF_A_KIND:
            # The quads rank followed by the kicker
            quads_rank = next(r for r, c in rank_counts.items() if c == 4)
            kicker = next(r for r in [c.value for c in sorted_cards] if r != quads_rank)
            return [quads_rank, kicker]
            
        elif hand_rank == HandRank.FULL_HOUSE:
            # The trips rank followed by the pair rank
            trips_rank = next(r for r, c in rank_counts.items() if c == 3)
            pair_rank = next(r for r, c in rank_counts.items() if c == 2)
            return [trips_rank, pair_rank]
            
        elif hand_rank == HandRank.THREE_OF_A_KIND:
            # The trips rank followed by the two kickers
            trips_rank = next(r for r, c in rank_counts.items() if c == 3)
            kickers = sorted([r for r in [c.value for c in sorted_cards] if r != trips_rank], reverse=True)
            return [trips_rank] + kickers[:2]
            
        elif hand_rank == HandRank.TWO_PAIR:
            # The high pair, the low pair, then the kicker
            pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
            kicker = next(r for r in [c.value for c in sorted_cards] if r not in pairs)
            return pairs + [kicker]
            
        elif hand_rank == HandRank.PAIR:
            # The pair followed by the three kickers
            pair_rank = next(r for r, c in rank_counts.items() if c == 2)
            kickers = sorted([r for r in [c.value for c in sorted_cards] if r != pair_rank], reverse=True)
            return [pair_rank] + kickers[:3]
            
        else:
            # For straights, flushes, straight flushes, and high cards,
            # just compare the ranks in descending order
            return [c.value for c in sorted_cards]