"""
Game module for Texas Hold'em Poker.
Implements the main game logic for a poker hand.
"""
from __future__ import annotations
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple, Set, Any
import uuid
import logging
from dataclasses import dataclass, field

from core.card import Card, Deck, create_deck
from core.hand import HandEvaluator, HandRank
from core.player import Player, PlayerStatus
from core.table import Table


class BettingRound(Enum):
    """Represents the betting rounds in a poker hand."""
    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()


class GameAction(Enum):
    """Possible actions a player can take."""
    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    BET = auto()
    RAISE = auto()
    ALL_IN = auto()


class GameStatus(Enum):
    """Current status of the game."""
    WAITING = auto()  # Waiting for players
    STARTING = auto()  # Game is about to start
    DEALING = auto()  # Cards are being dealt
    BETTING = auto()  # Players are betting
    SHOWDOWN = auto()  # Determining winner
    FINISHED = auto()  # Hand is complete


@dataclass
class GameConfig:
    """Configuration for a poker game."""
    small_blind: int = 5
    big_blind: int = 10
    ante: int = 0
    min_players: int = 2
    max_players: int = 9
    starting_chips: int = 1000


@dataclass
class ActionInfo:
    """Information about an action taken by a player."""
    player_id: str
    action: GameAction
    amount: int = 0
    timestamp: float = 0.0


@dataclass
class GameState:
    """Represents the current state of a poker game."""
    game_id: str
    status: GameStatus = GameStatus.WAITING
    table: Optional[Table] = None
    deck: Optional[Deck] = None
    community_cards: List[Card] = field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    min_raise: int = 0
    betting_round: BettingRound = BettingRound.PREFLOP
    action_history: List[ActionInfo] = field(default_factory=list)
    pots: List[Dict[str, Any]] = field(default_factory=list)
    main_pot: int = 0
    side_pots: List[Dict[str, Any]] = field(default_factory=list)
    current_player_idx: int = -1
    hand_number: int = 0
    config: GameConfig = field(default_factory=GameConfig)
    

class Game:
    """
    Manages a Texas Hold'em poker game.
    """
    def __init__(self, game_id: str = None, table: Table = None, config: GameConfig = None):
        """
        Initialize a new poker game.
        
        Args:
            game_id: Unique identifier for the game (auto-generated if None)
            table: Table object for the game
            config: Game configuration settings
        """
        self.game_id = game_id or str(uuid.uuid4())
        self.table = table or Table(str(uuid.uuid4()), "Default Table")
        self.config = config or GameConfig()
        
        self.state = GameState(
            game_id=self.game_id,
            status=GameStatus.WAITING,
            table=self.table,
            deck=None,
            betting_round=BettingRound.PREFLOP,
            config=self.config
        )
        
        self.logger = logging.getLogger(f"poker.game.{self.game_id}")
    
    def reset_game(self) -> None:
        """Reset the game state to prepare for a new hand."""
        self.state.status = GameStatus.WAITING
        self.state.community_cards = []
        self.state.pot = 0
        self.state.main_pot = 0
        self.state.side_pots = []
        self.state.current_bet = 0
        self.state.min_raise = self.config.big_blind
        
        # Reset all player states
        self.table.reset_player_states()
        
        # Remove eliminated players with zero chips from the table
        for position, player in enumerate(self.table.seats):
            if player is not None and (player.status == PlayerStatus.ELIMINATED or player.chips == 0):
                player.status = PlayerStatus.ELIMINATED
                # We don't physically remove them from the table here to maintain the output display
                # In a real implementation, you might want to actually remove them
        
        self.logger.info("Game reset and ready for new hand")
    
    def start_hand(self) -> bool:
        """
        Start a new hand of poker.
        
        Returns:
            True if the hand started successfully, False otherwise
        """
        # Auto-reset if game is in FINISHED state
        if self.state.status == GameStatus.FINISHED:
            self.reset_game()
            
        if self.state.status != GameStatus.WAITING:
            self.logger.warning("Cannot start hand: game is not in WAITING state")
            return False
        
        # Check if we have enough players
        active_count = sum(1 for p in self.table.seats if p is not None and p.chips > 0)
        if active_count < self.config.min_players:
            self.logger.warning(f"Cannot start hand: need at least {self.config.min_players} players")
            return False
        
        self.state.hand_number += 1
        self.logger.info(f"Starting hand #{self.state.hand_number}")
        
        # Reset the game state
        self.state.status = GameStatus.STARTING
        self.state.deck = create_deck()
        self.state.community_cards = []
        self.state.pot = 0
        self.state.main_pot = 0
        self.state.side_pots = []
        self.state.current_bet = 0
        self.state.min_raise = self.config.big_blind
        self.state.betting_round = BettingRound.PREFLOP
        self.state.action_history = []
        self.state.pots = []
        
        # Reset player states
        self.table.reset_player_states()
        
        # Advance the dealer button
        old_dealer = self.table.dealer_position
        new_dealer = self.table.advance_dealer_button()
        self.logger.info(f"Dealer button moved from position {old_dealer} to {new_dealer}")
        
        # Assign dealer and blinds
        if self.table.dealer_position != -1:
            dealer = self.table.get_player_at_position(self.table.dealer_position)
            if dealer:
                dealer.is_dealer = True
        
        # Post blinds
        sb_pos, bb_pos = self.table.get_blinds_positions()
        if sb_pos != -1 and bb_pos != -1:
            sb_player = self.table.get_player_at_position(sb_pos)
            bb_player = self.table.get_player_at_position(bb_pos)
            
            if sb_player and bb_player:
                sb_player.is_small_blind = True
                bb_player.is_big_blind = True
                
                # Post small blind (will be limited by available chips)
                sb_amount = sb_player.place_bet(self.config.small_blind)
                self.state.pot += sb_amount
                self.logger.info(f"Player {sb_player.name} posts small blind: {sb_amount}")
                
                self.state.action_history.append(ActionInfo(
                    player_id=sb_player.id,
                    action=GameAction.BET if sb_amount > 0 else GameAction.CHECK,
                    amount=sb_amount
                ))
                
                # Post big blind (will be limited by available chips)
                bb_amount = bb_player.place_bet(self.config.big_blind)
                self.state.pot += bb_amount
                self.state.current_bet = bb_amount  # Set the current bet to the BB amount (could be less if all-in)
                self.logger.info(f"Player {bb_player.name} posts big blind: {bb_amount}")
                
                self.state.action_history.append(ActionInfo(
                    player_id=bb_player.id,
                    action=GameAction.BET if bb_amount > 0 else GameAction.CHECK,
                    amount=bb_amount
                ))
                
                # If any blind player went all-in, adjust the min_raise accordingly
                if sb_player.status == PlayerStatus.ALL_IN or bb_player.status == PlayerStatus.ALL_IN:
                    self.state.min_raise = max(self.config.big_blind, bb_amount)

        # Post antes if configured
        if self.config.ante > 0:
            for player in self.table.seats:
                if player is not None and player.status == PlayerStatus.ACTIVE:
                    ante_amount = player.place_bet(self.config.ante)
                    self.state.pot += ante_amount
                    self.logger.info(f"Player {player.name} posts ante: {ante_amount}")
                    
        # Calculate initial pots after blinds and antes
        self._update_pots()

        # Deal hole cards
        self.state.status = GameStatus.DEALING
        self._deal_hole_cards()
        
        # Update active players and start betting
        self.table.update_active_players()
        self.state.status = GameStatus.BETTING
        
        # In standard play, first to act preflop is left of big blind
        if bb_pos != -1:
            self.state.current_player_idx = (bb_pos + 1) % self.table.max_seats
            # Ensure we find an actual player
            while (self.state.current_player_idx != bb_pos and 
                  (self.table.get_player_at_position(self.state.current_player_idx) is None or
                   self.table.get_player_at_position(self.state.current_player_idx).status != PlayerStatus.ACTIVE)):
                self.state.current_player_idx = (self.state.current_player_idx + 1) % self.table.max_seats
        
        self.logger.info(f"Hand #{self.state.hand_number} started successfully")
        return True
    
    def _deal_hole_cards(self) -> None:
        """Deal two hole cards to each active player."""
        # Deal first card to each player
        for player in self.table.seats:
            if player is not None and player.status == PlayerStatus.ACTIVE:
                card = self.state.deck.deal()
                if card:
                    player.receive_card(card)
        
        # Deal second card to each player
        for player in self.table.seats:
            if player is not None and player.status == PlayerStatus.ACTIVE:
                card = self.state.deck.deal()
                if card:
                    player.receive_card(card)
    
    def _deal_community_cards(self, count: int) -> List[Card]:
        """
        Deal community cards.
        
        Args:
            count: Number of cards to deal
            
        Returns:
            List of dealt cards
        """
        if not self.state.deck:
            self.logger.error("No deck available to deal community cards")
            return []
        
        # Burn a card first
        self.state.deck.burn()
        
        # Deal the specified number of cards
        new_cards = []
        for _ in range(count):
            card = self.state.deck.deal()
            if card:
                self.state.community_cards.append(card)
                new_cards.append(card)
        return new_cards
    
    def _update_pots(self) -> None:
        """
        Calculate and update main pot and side pots based on current bets.
        This is called after each betting action to maintain current pot values.
        """
        # Get all players who have bet in this hand
        all_players = [p for p in self.table.seats if p is not None and p.total_bet > 0]
        
        # No players with bets, no pots to calculate
        if not all_players:
            self.state.main_pot = 0
            self.state.side_pots = []
            return
        
        # Sort players by their total bet (ascending)
        all_players.sort(key=lambda p: p.total_bet)
        
        # Initialize pot tracking
        remaining_bets = {p.id: p.total_bet for p in all_players}
        pots = []
        
        # Process each potential side pot
        prev_bet = 0
        for player in all_players:
            if player.total_bet <= prev_bet:
                continue  # Skip players with identical bets
            
            current_bet = player.total_bet
            pot_size = 0
            eligible_players = []
            
            # Calculate this pot level
            for p_id, bet in list(remaining_bets.items()):
                amount = min(bet, current_bet - prev_bet)
                pot_size += amount
                remaining_bets[p_id] -= amount
                
                # Player is eligible for this pot if they contributed
                p = next((p for p in all_players if p.id == p_id), None)
                if p and amount > 0:
                    eligible_players.append(p_id)
            
            if pot_size > 0:
                pots.append({
                    "amount": pot_size,
                    "eligible_players": eligible_players
                })
            
            prev_bet = current_bet
        
        # Update game state
        if pots:
            # First pot is the main pot (everyone is eligible)
            self.state.main_pot = pots[0]["amount"]
            # Any additional pots are side pots
            self.state.side_pots = pots[1:] if len(pots) > 1 else []
        else:
            self.state.main_pot = 0
            self.state.side_pots = []
        
        # Also update the total pot for backward compatibility
        self.state.pot = sum(pot["amount"] for pot in pots)

    def handle_player_action(self, player_id: str, action: GameAction, amount: int = 0) -> bool:
        """
        Process a player's action during their turn.
        
        Args:
            player_id: ID of the player taking the action
            action: The action being taken
            amount: Amount to bet or raise (if applicable)
            
        Returns:
            True if the action was successful, False otherwise
        """
        if self.state.status != GameStatus.BETTING:
            self.logger.warning("Cannot handle action: game is not in BETTING state")
            return False
        
        # Find the player
        player = None
        for p in self.table.seats:
            if p is not None and p.id == player_id:
                player = p
                break
        
        if player is None:
            self.logger.warning(f"Player {player_id} not found")
            return False
        
        # Check if it's the player's turn
        current_player = self.table.get_player_at_position(self.state.current_player_idx)
        if current_player is None or current_player.id != player_id:
            self.logger.warning(f"Not {player.name}'s turn to act")
            return False
        
        # Process the action
        action_successful = False
        action_info = ActionInfo(player_id=player_id, action=action, amount=amount)
        
        if action == GameAction.FOLD:
            # Can only fold if there's a bet to call
            if self.state.current_bet <= player.current_bet:
                self.logger.warning(f"Player {player.name} cannot fold, must check")
                return False
                
            player.fold()
            self.logger.info(f"Player {player.name} folds")
            action_successful = True
        
        elif action == GameAction.CHECK:
            # Can only check if current bet is 0 or player has already matched it
            if self.state.current_bet <= player.current_bet:
                self.logger.info(f"Player {player.name} checks")
                action_successful = True
            else:
                self.logger.warning(f"Player {player.name} cannot check")
                return False
        
        elif action == GameAction.CALL:
            # Calculate call amount
            call_amount = self.state.current_bet - player.current_bet
            if call_amount <= 0:
                # Player has already matched the current bet, treat as check
                self.logger.info(f"Player {player.name} checks (no need to call)")
                action_info.action = GameAction.CHECK
                action_successful = True
            else:
                # Place the call
                actual_amount = player.place_bet(call_amount)
                self.state.pot += actual_amount
                action_info.amount = actual_amount
                
                if actual_amount < call_amount and player.chips == 0:
                    # Player couldn't match the full bet - they're all in
                    self.logger.info(f"Player {player.name} calls {actual_amount} and is all-in")
                    action_info.action = GameAction.ALL_IN
                else:
                    self.logger.info(f"Player {player.name} calls {actual_amount}")
                
                action_successful = True
        
        elif action == GameAction.BET:
            # Can only bet if no previous bet in this round
            if self.state.current_bet > 0:
                self.logger.warning(f"Player {player.name} cannot bet, must raise")
                return False
            
            # Ensure minimum bet
            if amount < self.config.big_blind:
                amount = self.config.big_blind
            
            # Place the bet
            actual_amount = player.place_bet(amount)
            self.state.pot += actual_amount
            self.state.current_bet = actual_amount
            self.state.min_raise = actual_amount
            action_info.amount = actual_amount
            
            # Mark all players as needing to act again (except this player and folded players)
            for p in self.table.seats:
                if p is not None and p.id != player.id and p.status == PlayerStatus.ACTIVE:
                    p.has_acted = False
            
            if player.chips == 0:
                self.logger.info(f"Player {player.name} bets {actual_amount} and is all-in")
                action_info.action = GameAction.ALL_IN
            else:
                self.logger.info(f"Player {player.name} bets {actual_amount}")
            
            action_successful = True
        
        elif action == GameAction.RAISE:
            # Ensure minimum raise
            min_amount = self.state.current_bet + self.state.min_raise
            if amount < min_amount:
                amount = min_amount
            
            # Calculate total to match current bet plus raise
            total_to_call = self.state.current_bet - player.current_bet
            total_amount = total_to_call + (amount - self.state.current_bet)
            
            # Place the raise
            actual_amount = player.place_bet(total_amount)
            self.state.pot += actual_amount
            
            new_bet = player.current_bet
            if new_bet > self.state.current_bet:
                # Calculate the raise amount for min_raise tracking
                raise_amount = new_bet - self.state.current_bet
                self.state.current_bet = new_bet
                self.state.min_raise = raise_amount
                
                # Mark all players as needing to act again (except this player and folded players)
                for p in self.table.seats:
                    if p is not None and p.id != player.id and p.status == PlayerStatus.ACTIVE:
                        p.has_acted = False
                
                action_info.amount = actual_amount
                
                if player.chips == 0:
                    self.logger.info(f"Player {player.name} raises to {new_bet} and is all-in")
                    action_info.action = GameAction.ALL_IN
                else:
                    self.logger.info(f"Player {player.name} raises to {new_bet}")
                
                action_successful = True
            else:
                # Player couldn't raise enough, treat as call/all-in
                if player.chips == 0:
                    self.logger.info(f"Player {player.name} calls {actual_amount} and is all-in")
                    action_info.action = GameAction.ALL_IN
                else:
                    self.logger.info(f"Player {player.name} calls {actual_amount}")
                    action_info.action = GameAction.CALL
                
                action_successful = True
        
        elif action == GameAction.ALL_IN:
            # Player is going all-in
            if player.chips == 0:
                self.logger.warning(f"Player {player.name} is already all-in")
                return False
            
            actual_amount = player.place_bet(player.chips)  # Bet everything
            self.state.pot += actual_amount
            action_info.amount = actual_amount
            
            new_bet = player.current_bet
            if new_bet > self.state.current_bet:
                # This all-in is a raise
                raise_amount = new_bet - self.state.current_bet
                
                if raise_amount >= self.state.min_raise:
                    # Valid raise
                    self.state.current_bet = new_bet
                    self.state.min_raise = raise_amount
                    
                    # Mark all players as needing to act again (except this player and folded players)
                    for p in self.table.seats:
                        if p is not None and p.id != player.id and p.status == PlayerStatus.ACTIVE:
                            p.has_acted = False
                
                self.logger.info(f"Player {player.name} raises to {new_bet} (all-in)")
            else:
                # This all-in is a call or less than a call
                self.logger.info(f"Player {player.name} calls {actual_amount} (all-in)")
            
            action_successful = True
        
        # Record the action if successful
        if action_successful:
            player.has_acted = True
            self.state.action_history.append(action_info)
            
            # Update pots after successful action
            self._update_pots()
            
            # Advance to next player
            self._advance_to_next_player()
            return True
        
        return False
    
    def _advance_to_next_player(self) -> None:
        """Advance to the next player who can act."""
        # Check if the betting round is over
        if self._is_betting_round_complete():
            self._advance_betting_round()
            return
        
        # Find the next player who can act
        found = False
        start_pos = self.state.current_player_idx
        current_pos = (start_pos + 1) % self.table.max_seats
        
        while current_pos != start_pos:
            player = self.table.get_player_at_position(current_pos)
            if player is not None and player.status == PlayerStatus.ACTIVE and not player.has_acted:
                self.state.current_player_idx = current_pos
                found = True
                break
            
            current_pos = (current_pos + 1) % self.table.max_seats
        
        if not found:
            # No more players to act, end the betting round
            self._advance_betting_round()
    
    def _is_betting_round_complete(self) -> bool:
        """
        Check if the current betting round is complete.
        
        Returns:
            True if all players have acted and bets are matched, False otherwise
        """
        active_count = 0
        acted_count = 0
        bet_matched_count = 0
        
        for player in self.table.seats:
            if player is None or player.status not in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN):
                continue
            
            active_count += 1
            
            # A player is considered to have acted if:
            # 1. They have acted AND matched the current bet, or
            # 2. They are all-in
            if (player.has_acted and player.current_bet == self.state.current_bet) or player.status == PlayerStatus.ALL_IN:
                acted_count += 1
            
            if player.current_bet == self.state.current_bet or player.status == PlayerStatus.ALL_IN:
                bet_matched_count += 1
        
        # All players have acted and all bets are matched
        return active_count > 0 and acted_count == active_count and bet_matched_count == active_count
    
    def _advance_betting_round(self) -> None:
        """Advance to the next betting round or showdown."""
        # Reset player acted flags and bet amounts for the new round
        for player in self.table.seats:
            if player is not None:
                player.reset_for_new_betting_round()
        
        # Check if only one player remains
        active_players = [p for p in self.table.seats if p is not None and 
                         p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN)]
        
        if len(active_players) <= 1 or sum(1 for p in active_players if p.status == PlayerStatus.ACTIVE) == 0:
            # Only one player left or all remaining players are all-in
            self._deal_remaining_community_cards()
            self._go_to_showdown()
            return
        
        if self.state.betting_round == BettingRound.PREFLOP:
            # Flop
            self.state.betting_round = BettingRound.FLOP
            self.state.current_bet = 0
            self.state.min_raise = self.config.big_blind
            self._deal_community_cards(3)  # Deal the flop
            self.logger.info("Betting round: FLOP")
            
            # First to act is first active player after dealer
            self._set_next_player_to_act()
        
        elif self.state.betting_round == BettingRound.FLOP:
            # Turn
            self.state.betting_round = BettingRound.TURN
            self.state.current_bet = 0
            self.state.min_raise = self.config.big_blind
            self._deal_community_cards(1)  # Deal the turn
            self.logger.info("Betting round: TURN")
            
            # First to act is first active player after dealer
            self._set_next_player_to_act()
        
        elif self.state.betting_round == BettingRound.TURN:
            # River
            self.state.betting_round = BettingRound.RIVER
            self.state.current_bet = 0
            self.state.min_raise = self.config.big_blind
            self._deal_community_cards(1)  # Deal the river
            self.logger.info("Betting round: RIVER")
            
            # First to act is first active player after dealer
            self._set_next_player_to_act()
        
        elif self.state.betting_round == BettingRound.RIVER:
            # End of hand, go to showdown
            self._go_to_showdown()
    
    def _set_next_player_to_act(self) -> None:
        """Set the next player to act in a new betting round."""
        if self.table.dealer_position == -1:
            # No dealer, start with first active player
            for i, player in enumerate(self.table.seats):
                if player is not None and player.status == PlayerStatus.ACTIVE:
                    self.state.current_player_idx = i
                    return
        else:
            # Start with first active player after dealer
            current_pos = (self.table.dealer_position + 1) % self.table.max_seats
            start_pos = current_pos
            
            while True:
                player = self.table.get_player_at_position(current_pos)
                if player is not None and player.status == PlayerStatus.ACTIVE:
                    self.state.current_player_idx = current_pos
                    return
                
                current_pos = (current_pos + 1) % self.table.max_seats
                if current_pos == start_pos:
                    # We've gone full circle and found no active players
                    break
        
        # If we get here, no active players were found
        self.state.current_player_idx = -1
    
    def _deal_remaining_community_cards(self) -> None:
        """Deal any remaining community cards needed for showdown."""
        # Deal remaining community cards if needed
        if len(self.state.community_cards) == 0:
            self._deal_community_cards(3)  # Flop
            self._deal_community_cards(1)  # Turn
            self._deal_community_cards(1)  # River
        elif len(self.state.community_cards) == 3:
            self._deal_community_cards(1)  # Turn
            self._deal_community_cards(1)  # River
        elif len(self.state.community_cards) == 4:
            self._deal_community_cards(1)  # River
    
    def _go_to_showdown(self) -> None:
        """Process the showdown and determine winner(s)."""
        self.state.status = GameStatus.SHOWDOWN
        self.state.betting_round = BettingRound.SHOWDOWN
        self.logger.info("Going to showdown")
        
        # Get all active players
        active_players = [p for p in self.table.seats if p is not None and 
                         p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN)]
        
        # If only one active player, they win automatically
        if len(active_players) == 1:
            winner = active_players[0]
            winner.add_chips(self.state.pot)
            self.logger.info(f"Player {winner.name} wins {self.state.pot} (uncontested)")
            
            self.state.status = GameStatus.FINISHED
            self.state.pot = 0
            return
        
        # Evaluate hands and determine winners
        player_hands = {}
        for player in active_players:
            # Combine hole cards and community cards
            all_cards = player.hand.cards + self.state.community_cards
            
            # Evaluate the best hand
            hand_rank, best_cards, description = HandEvaluator.evaluate(all_cards)
            
            player_hands[player.id] = {
                "player": player,
                "hand_rank": hand_rank,
                "best_cards": best_cards,
                "description": description
            }
            
            self.logger.info(f"Player {player.name}: {description}")
        
        # Determine winners using side pots if needed
        self._calculate_and_award_pots(player_hands)
        
        # Hand is finished
        self.state.status = GameStatus.FINISHED
        self.state.pot = 0
    
    def _calculate_and_award_pots(self, player_hands: Dict[str, Dict[str, Any]]) -> None:
        """
        Calculate and award main pot and side pots.
        
        Args:
            player_hands: Dictionary mapping player IDs to their evaluated hands
        """
        # Get all players who were involved in the hand
        all_players = [p for p in self.table.seats if p is not None and 
                    (p.total_bet > 0 or p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN))]
        
        if not all_players:
            self.logger.warning("No players found for pot calculation")
            return
        
        # Sort players by their total bet (ascending)
        all_players.sort(key=lambda p: p.total_bet)
        
        # Calculate pots
        remaining_bets = {p.id: p.total_bet for p in all_players}
        remaining_pot = self.state.pot
        pots = []
        
        # Process each potential side pot
        prev_bet = 0
        for player in all_players:
            if player.total_bet <= prev_bet:
                continue  # Skip players with identical bets
            
            current_bet = player.total_bet
            pot_size = 0
            eligible_players = []
            
            # Calculate this pot level
            for p_id, bet in list(remaining_bets.items()):
                amount = min(bet, current_bet - prev_bet)
                pot_size += amount
                remaining_bets[p_id] -= amount
                
                # Player is eligible for this pot if they contributed and are in showdown
                # or they are the only active player
                p = next((p for p in all_players if p.id == p_id), None)
                if p and amount > 0 and (p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN) or
                                        sum(1 for pl in all_players if pl.status == PlayerStatus.ACTIVE) == 1):
                    eligible_players.append(p_id)
            
            if pot_size > 0:
                pots.append({
                    "amount": pot_size,
                    "eligible_players": eligible_players
                })
            
            prev_bet = current_bet
        
        # Award each pot to winner(s)
        for i, pot in enumerate(pots):
            pot_amount = pot["amount"]
            if pot_amount == 0:
                continue
            
            eligible_ids = pot["eligible_players"]
            eligible_players = [player_hands[p_id] for p_id in eligible_ids if p_id in player_hands]
            
            if not eligible_players:
                self.logger.warning(f"No eligible players found for pot {i+1}")
                continue
            
            # Find the best hand(s)
            best_rank = max(p["hand_rank"] for p in eligible_players)
            best_players = [p for p in eligible_players if p["hand_rank"] == best_rank]
            
            # If tie, compare kickers
            if len(best_players) > 1:
                # Use HandEvaluator._get_kicker_key to compare hands
                best_key = None
                true_best_players = []
                
                for player_hand in best_players:
                    player = player_hand["player"]
                    best_cards = player_hand["best_cards"]
                    hand_rank = player_hand["hand_rank"]
                    
                    # Get kicker key for this hand
                    key = HandEvaluator._get_kicker_key(best_cards, hand_rank)
                    
                    # If this is the first player or this hand is better
                    if best_key is None or key > best_key:
                        best_key = key
                        true_best_players = [player_hand]
                    elif key == best_key:
                        # True tie
                        true_best_players.append(player_hand)
                
                winners = true_best_players
            else:
                winners = best_players
            
            # Award pot to winner(s)
            amount_per_winner = pot_amount // len(winners)
            remainder = pot_amount % len(winners)
            
            for i, winner in enumerate(winners):
                player = winner["player"]
                win_amount = amount_per_winner + (1 if i < remainder else 0)
                player.add_chips(win_amount)
                
                # Update player statistics
                player.update_statistics(True, win_amount, winner["description"])
                
                self.logger.info(f"Player {player.name} wins {win_amount} with {winner['description']}")
        
        # Update statistics for non-winners
        for player in all_players:
            if player.id not in [w["player"].id for pot in pots for w in [player_hands[p_id] for p_id in pot["eligible_players"] if p_id in player_hands]]:
                if player.id in player_hands:
                    player.update_statistics(False, 0, player_hands[player.id]["description"])
                else:
                    player.update_statistics(False, 0, None)
    
    def get_available_actions(self, player_id: str) -> Dict[GameAction, int]:
        """
        Get the available actions for a player.
        
        Args:
            player_id: ID of the player
            
        Returns:
            Dictionary mapping available actions to minimum amounts
        """
        actions = {}
        
        # Find the player
        player = None
        for p in self.table.seats:
            if p is not None and p.id == player_id:
                player = p
                break
        
        if player is None or self.state.status != GameStatus.BETTING:
            return actions
        
        # Check if it's the player's turn
        current_player = self.table.get_player_at_position(self.state.current_player_idx)
        if current_player is None or current_player.id != player_id:
            return actions
        
        # Calculate if player needs to call anything
        call_amount = self.state.current_bet - player.current_bet
        
        # CHECK is available if no bet to call
        if call_amount <= 0:
            actions[GameAction.CHECK] = 0
            # When check is available, fold is not a logical option
        else:
            # FOLD is only available if there's a bet to call
            actions[GameAction.FOLD] = 0
            
            # CALL is available if there's a bet to call and player has chips
            if player.chips > 0:
                actions[GameAction.CALL] = min(call_amount, player.chips)
        
        # BET is available if no current bet and player has chips
        if self.state.current_bet == 0 and player.chips > 0:
            actions[GameAction.BET] = min(self.config.big_blind, player.chips)
        
        # RAISE is available if there's a current bet and player has enough chips
        min_raise_to = self.state.current_bet + self.state.min_raise
        if self.state.current_bet > 0 and player.chips > call_amount:
            actions[GameAction.RAISE] = min(min_raise_to, player.chips)
        
        # ALL_IN is always available if player has chips
        if player.chips > 0:
            actions[GameAction.ALL_IN] = player.chips
        
        return actions
    
    def get_game_state_for_player(self, player_id: str) -> Dict[str, Any]:
        """
        Get the visible game state for a specific player.
        
        Args:
            player_id: ID of the player
            
        Returns:
            Dictionary with visible game state
        """
        # Find the player
        target_player = None
        for p in self.table.seats:
            if p is not None and p.id == player_id:
                target_player = p
                break
        
        # Basic game state info
        state = {
            "game_id": self.game_id,
            "status": self.state.status.name,
            "betting_round": self.state.betting_round.name,
            "pot": self.state.pot,
            "main_pot": self.state.main_pot,
            "side_pots": self.state.side_pots,
            "current_bet": self.state.current_bet,
            "hand_number": self.state.hand_number,
            "community_cards": [str(card) for card in self.state.community_cards],
            "players": [],
            "current_player_idx": self.state.current_player_idx,
            "available_actions": {} if target_player else {},
            "blinds": {
                "small_blind": self.config.small_blind,
                "big_blind": self.config.big_blind,
                "ante": self.config.ante
            }
        }
        
        # Add player information
        for i, player in enumerate(self.table.seats):
            if player is None:
                state["players"].append(None)
                continue
            
            player_info = {
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "chips": player.chips,
                "current_bet": player.current_bet,
                "total_bet": player.total_bet,
                "status": player.status.name,
                "is_dealer": player.is_dealer,
                "is_small_blind": player.is_small_blind,
                "is_big_blind": player.is_big_blind,
                "has_acted": player.has_acted,
                "avatar": player.avatar
            }
            
            # Only show hole cards to their owner or at showdown
            if player.id == player_id or self.state.status == GameStatus.SHOWDOWN:
                player_info["cards"] = [str(card) for card in player.hand.cards]
            else:
                player_info["cards"] = ["??"] * len(player.hand.cards)
            
            state["players"].append(player_info)
        
        # Add available actions if it's the player's turn
        if target_player:
            state["available_actions"] = self.get_available_actions(player_id)
        
        return state