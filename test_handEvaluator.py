#!/usr/bin/env python
"""
Detailed poker hand comparison tool for Texas Hold'em.
Shows comprehensive comparison information between multiple players' hands.
"""
import sys
import os
from typing import List, Tuple
import itertools

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.card import Card, Rank, Suit
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

def rank_value_to_name(value):
    """Convert a card rank value to a readable name."""
    rank_names = {
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine",
        10: "Ten",
        11: "Jack",
        12: "Queen",
        13: "King",
        14: "Ace"
    }
    return rank_names.get(value, str(value))

def get_comparison_explanation(players_hands):
    """
    Generate detailed explanations of why one hand ranks above another.
    Returns a list of explanation strings.
    """
    if len(players_hands) < 2:
        return []
    
    explanations = []
    
    # Group players by hand rank
    rank_groups = {}
    for i, (name, hand_rank, best_cards, description) in enumerate(players_hands):
        if hand_rank not in rank_groups:
            rank_groups[hand_rank] = []
        rank_groups[hand_rank].append((i, name, best_cards, description))
    
    # Sort rank groups by hand rank (highest first)
    sorted_ranks = sorted(rank_groups.keys(), reverse=True)
    
    # If all players have different hand ranks, explain the ranking order
    if len(rank_groups) == len(players_hands):
        top_rank = sorted_ranks[0]
        top_player = rank_groups[top_rank][0][1]
        explanation = f"{top_player} wins with {HandRank(top_rank).name} - higher hand rank than all others"
        explanations.append(explanation)
        return explanations
    
    # For each rank group with multiple players, explain tie breakers
    for rank in sorted_ranks:
        players_in_group = rank_groups[rank]
        
        # Skip groups with only one player
        if len(players_in_group) < 2:
            continue
        
        # Get kicker keys for comparison
        players_with_keys = []
        for idx, name, best_cards, description in players_in_group:
            key = HandEvaluator._get_kicker_key(best_cards, rank)
            players_with_keys.append((idx, name, key))
        
        # Sort players by kicker key (best first)
        players_with_keys.sort(key=lambda x: x[2], reverse=True)
        
        # Generate explanation based on hand type
        hand_type = HandRank(rank)
        
        if hand_type == HandRank.ROYAL_FLUSH:
            # All royal flushes are equal
            names = [p[1] for p in players_with_keys]
            explanations.append(f"Players with Royal Flush tie: {', '.join(names)}")
            
        elif hand_type == HandRank.STRAIGHT_FLUSH:
            best_key = players_with_keys[0][2]
            best_players = [p for p in players_with_keys if p[2] == best_key]
            
            if len(best_players) > 1:
                # Tied straight flushes
                names = [p[1] for p in best_players]
                high_card = rank_value_to_name(best_key[0])
                explanations.append(f"Players tie with {high_card}-high Straight Flush: {', '.join(names)}")
            else:
                # Compare straight flush by high card
                winner = best_players[0][1]
                high_card = rank_value_to_name(best_key[0])
                others = [p[1] for p in players_with_keys if p[1] != winner]
                explanations.append(f"{winner} wins with {high_card}-high Straight Flush vs {', '.join(others)}")
                
        elif hand_type == HandRank.FOUR_OF_A_KIND:
            # Compare by quads rank, then kicker
            for i in range(len(players_with_keys) - 1):
                p1 = players_with_keys[i]
                p2 = players_with_keys[i + 1]
                
                if p1[2][0] != p2[2][0]:
                    # Different quad ranks
                    quad_rank1 = rank_value_to_name(p1[2][0])
                    quad_rank2 = rank_value_to_name(p2[2][0])
                    explanations.append(f"{p1[1]} beats {p2[1]} with four {quad_rank1}s vs four {quad_rank2}s")
                else:
                    # Same quads, different kicker
                    kicker1 = rank_value_to_name(p1[2][1])
                    kicker2 = rank_value_to_name(p2[2][1])
                    explanations.append(f"{p1[1]} beats {p2[1]} with {kicker1} kicker vs {kicker2} kicker (both have four {rank_value_to_name(p1[2][0])}s)")
        
        elif hand_type == HandRank.FULL_HOUSE:
            # Compare by trips rank, then pair rank
            for i in range(len(players_with_keys) - 1):
                p1 = players_with_keys[i]
                p2 = players_with_keys[i + 1]
                
                if p1[2][0] != p2[2][0]:
                    # Different trip ranks
                    trips1 = rank_value_to_name(p1[2][0])
                    trips2 = rank_value_to_name(p2[2][0])
                    explanations.append(f"{p1[1]} beats {p2[1]} with {trips1}s full vs {trips2}s full")
                else:
                    # Same trips, different pairs
                    trips = rank_value_to_name(p1[2][0])
                    pair1 = rank_value_to_name(p1[2][1])
                    pair2 = rank_value_to_name(p2[2][1])
                    explanations.append(f"{p1[1]} beats {p2[1]} with {trips}s full of {pair1}s vs {trips}s full of {pair2}s")
        
        elif hand_type == HandRank.FLUSH:
            # Compare by highest card, then next highest, etc.
            for i in range(len(players_with_keys) - 1):
                p1 = players_with_keys[i]
                p2 = players_with_keys[i + 1]
                
                # Find the first differing card
                for j in range(5):
                    if p1[2][j] != p2[2][j]:
                        card1 = rank_value_to_name(p1[2][j])
                        card2 = rank_value_to_name(p2[2][j])
                        explanations.append(f"{p1[1]} beats {p2[1]} with {card1}-high flush vs {card2}-high flush")
                        break
        
        elif hand_type == HandRank.STRAIGHT:
            # Compare by highest card
            best_key = players_with_keys[0][2]
            best_players = [p for p in players_with_keys if p[2] == best_key]
            
            if len(best_players) > 1:
                # Tied straights
                names = [p[1] for p in best_players]
                high_card = rank_value_to_name(best_key[0])
                explanations.append(f"Players tie with {high_card}-high Straight: {', '.join(names)}")
            else:
                # Different high cards
                winner = best_players[0][1]
                high_card = rank_value_to_name(best_key[0])
                others = [p[1] for p in players_with_keys if p[1] != winner]
                explanations.append(f"{winner} wins with {high_card}-high Straight vs {', '.join(others)}")
        
        elif hand_type == HandRank.THREE_OF_A_KIND:
            # Compare by trips rank, then kickers
            for i in range(len(players_with_keys) - 1):
                p1 = players_with_keys[i]
                p2 = players_with_keys[i + 1]
                
                if p1[2][0] != p2[2][0]:
                    # Different trip ranks
                    trips1 = rank_value_to_name(p1[2][0])
                    trips2 = rank_value_to_name(p2[2][0])
                    explanations.append(f"{p1[1]} beats {p2[1]} with three {trips1}s vs three {trips2}s")
                else:
                    # Same trips, compare kickers
                    trips = rank_value_to_name(p1[2][0])
                    # Find first differing kicker
                    for j in range(1, 3):
                        if p1[2][j] != p2[2][j]:
                            kicker1 = rank_value_to_name(p1[2][j])
                            kicker2 = rank_value_to_name(p2[2][j])
                            explanations.append(f"{p1[1]} beats {p2[1]} with three {trips}s, {kicker1} kicker vs {kicker2} kicker")
                            break
        
        elif hand_type == HandRank.TWO_PAIR:
            # Compare by high pair, low pair, then kicker
            for i in range(len(players_with_keys) - 1):
                p1 = players_with_keys[i]
                p2 = players_with_keys[i + 1]
                
                if p1[2][0] != p2[2][0]:
                    # Different high pair
                    pair1 = rank_value_to_name(p1[2][0])
                    pair2 = rank_value_to_name(p2[2][0])
                    explanations.append(f"{p1[1]} beats {p2[1]} with {pair1}s and {rank_value_to_name(p1[2][1])}s vs {pair2}s and {rank_value_to_name(p2[2][1])}s")
                elif p1[2][1] != p2[2][1]:
                    # Same high pair, different low pair
                    high = rank_value_to_name(p1[2][0])
                    low1 = rank_value_to_name(p1[2][1])
                    low2 = rank_value_to_name(p2[2][1])
                    explanations.append(f"{p1[1]} beats {p2[1]} with {high}s and {low1}s vs {high}s and {low2}s")
                else:
                    # Same pairs, different kicker
                    high = rank_value_to_name(p1[2][0])
                    low = rank_value_to_name(p1[2][1])
                    kicker1 = rank_value_to_name(p1[2][2])
                    kicker2 = rank_value_to_name(p2[2][2])
                    explanations.append(f"{p1[1]} beats {p2[1]} with {high}s and {low}s, {kicker1} kicker vs {kicker2} kicker")
        
        elif hand_type == HandRank.PAIR:
            # Compare by pair rank, then kickers
            for i in range(len(players_with_keys) - 1):
                p1 = players_with_keys[i]
                p2 = players_with_keys[i + 1]
                
                if p1[2][0] != p2[2][0]:
                    # Different pair rank
                    pair1 = rank_value_to_name(p1[2][0])
                    pair2 = rank_value_to_name(p2[2][0])
                    explanations.append(f"{p1[1]} beats {p2[1]} with pair of {pair1}s vs pair of {pair2}s")
                else:
                    # Same pair, find first differing kicker
                    pair = rank_value_to_name(p1[2][0])
                    for j in range(1, 4):
                        if p1[2][j] != p2[2][j]:
                            kicker1 = rank_value_to_name(p1[2][j])
                            kicker2 = rank_value_to_name(p2[2][j])
                            explanations.append(f"{p1[1]} beats {p2[1]} with pair of {pair}s, {kicker1} kicker vs {kicker2} kicker")
                            break
        
        elif hand_type == HandRank.HIGH_CARD:
            # Compare by highest card, then next highest, etc.
            for i in range(len(players_with_keys) - 1):
                p1 = players_with_keys[i]
                p2 = players_with_keys[i + 1]
                
                # Find the first differing card
                for j in range(5):
                    if p1[2][j] != p2[2][j]:
                        card1 = rank_value_to_name(p1[2][j])
                        card2 = rank_value_to_name(p2[2][j])
                        explanations.append(f"{p1[1]} beats {p2[1]} with {card1} high vs {card2} high")
                        break
    
    return explanations

def determine_winners(players_hands):
    """
    Determine the winner(s) among multiple players.
    Returns list of indices of winning players.
    """
    # If no players, no winners
    if not players_hands:
        return []
    
    best_rank = HandRank.HIGH_CARD
    best_key = None
    winners = []
    
    # First pass: find the highest hand rank
    for i, (_, hand_rank, _, _) in enumerate(players_hands):
        if hand_rank > best_rank:
            best_rank = hand_rank
    
    # Second pass: find players with the highest rank
    candidates = [i for i, (_, hand_rank, _, _) in enumerate(players_hands) if hand_rank == best_rank]
    
    # If only one player has the best rank, they win
    if len(candidates) == 1:
        return candidates
    
    # Third pass: compare kickers for tied players
    for i in candidates:
        best_cards = players_hands[i][2]
        key = HandEvaluator._get_kicker_key(best_cards, best_rank)
        
        if best_key is None or key > best_key:
            best_key = key
            winners = [i]
        elif key == best_key:
            # True tie
            winners.append(i)
    
    return winners

def main():
    """Run the multi-player hand comparison test."""
    print("🃏 Detailed Poker Hand Comparison Tool 🃏")
    print("Enter cards in format like: Ah Kd Qc Js 10h")
    print("Use 'A' for Ace, 'K' for King, 'Q' for Queen, 'J' for Jack")
    print("Use 'c' for Clubs, 'd' for Diamonds, 'h' for Hearts, 's' for Spades")
    print("You can also use actual suit symbols: ♣ ♦ ♥ ♠")
    print("Example: A♥ K♦ Q♣ J♠ 10♥")
    print("Enter 'q' to exit, 'r' to reset and start a new hand")
    print()
    
    while True:
        # Get community cards
        community_input = input("Enter 5 community cards ('q' to quit): ")
        if community_input.lower() == 'q':
            print("Goodbye!")
            return
        
        try:
            community_cards = parse_cards(community_input)
            if len(community_cards) != 5:
                print("Please enter exactly 5 community cards!")
                continue
        except Exception as e:
            print(f"Error: {e}")
            continue
        
        print(f"Community cards: {' '.join(str(card) for card in community_cards)}")
        print("\nNow enter each player's hole cards (2 cards per player)")
        print("Enter 'r' to reset or 'q' to quit when done adding players")
        
        players = []  # List of (name, cards) tuples
        player_num = 1
        done_adding = False
        
        # Get players' hole cards
        while not done_adding:
            if len(players) >= 9:
                print("Maximum 9 players reached!")
                break
                
            player_name = input(f"\nEnter Player {player_num}'s name ('r' to reset, 'q' to finish): ")
            if player_name.lower() == 'q':
                # Done adding players, proceed to evaluation
                done_adding = True
                continue
                
            if player_name.lower() == 'r':
                print("\nResetting hand...\n")
                players = []
                player_num = 1
                break
                
            hole_cards_input = input(f"Enter {player_name}'s 2 hole cards: ")
            
            if hole_cards_input.lower() == 'q':
                # Done adding players, proceed to evaluation
                done_adding = True
                continue
                
            if hole_cards_input.lower() == 'r':
                print("\nResetting hand...\n")
                players = []
                player_num = 1
                break
            
            try:
                hole_cards = parse_cards(hole_cards_input)
                if len(hole_cards) != 2:
                    print("Please enter exactly 2 hole cards!")
                    continue
                
                players.append((player_name, hole_cards))
                player_num += 1
            except Exception as e:
                print(f"Error: {e}")
        
        # If we need to reset, continue to next iteration
        if player_name.lower() == 'r' or (hole_cards_input and hole_cards_input.lower() == 'r'):
            continue
            
        # If no players were added, continue
        if not players:
            print("No players added. Please try again.")
            continue
        
        # Evaluate each player's hand
        players_hands = []  # List of (name, hand_rank, best_cards, description)
        
        for name, hole_cards in players:
            # Combine hole cards with community cards
            all_cards = hole_cards + community_cards
            
            # Evaluate the hand
            hand_rank, best_cards, description = HandEvaluator.evaluate(all_cards)
            
            players_hands.append((name, hand_rank, best_cards, description))
        
        # Determine winner(s)
        winner_indices = determine_winners(players_hands)
        
        # Get detailed comparison explanations
        comparison_explanations = get_comparison_explanation(players_hands)
        
        # Display results
        print("\n🏆 RESULTS 🏆")
        print(f"Community cards: {' '.join(str(card) for card in community_cards)}")
        print("\nPlayer hands (ranked from best to worst):")
        
        # Sort players by hand strength
        ranked_players = []
        for i, (name, hand_rank, best_cards, description) in enumerate(players_hands):
            key = HandEvaluator._get_kicker_key(best_cards, hand_rank)
            ranked_players.append((i, name, hand_rank, best_cards, description, key))
        
        # Sort by hand rank, then kicker key
        ranked_players.sort(key=lambda x: (x[2], x[5]), reverse=True)
        
        # Display players in order
        for rank, (i, name, hand_rank, best_cards, description, key) in enumerate(ranked_players, 1):
            player_cards = players[i][1]
            is_winner = i in winner_indices
            
            winner_marker = "🏆 WINNER 🏆" if is_winner else ""
            print(f"#{rank}: {name}: {' '.join(str(card) for card in player_cards)} - {description} {winner_marker}")
            print(f"  Best 5 cards: {' '.join(str(card) for card in best_cards)}")
            print(f"  Hand rank: {hand_rank.name} ({hand_rank.value})")
            print(f"  Kicker values: {key}")
            print()
        
        # Display winner(s)
        winners = [players_hands[i][0] for i in winner_indices]
        if len(winners) == 1:
            print(f"Winner: {winners[0]}")
        else:
            print(f"Tie between: {', '.join(winners)}")
        
        # Display comparison explanations
        if comparison_explanations:
            print("\nDetailed Comparisons:")
            for explanation in comparison_explanations:
                print(f"• {explanation}")
        
        print("=" * 60)
        print("Enter a new set of community cards to continue, or 'q' to quit")
        print()

if __name__ == "__main__":
    main()