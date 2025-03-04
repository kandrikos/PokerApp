"""Unit tests for the Table module."""
import unittest
from core.table import Table
from core.player import Player, PlayerStatus


class TestTable(unittest.TestCase):
    def setUp(self):
        """Set up a table with some players for testing."""
        self.table = Table("test_table", "Test Table", max_seats=6)
        
        # Create some players
        self.players = [
            Player(f"player{i}", name=f"Player {i}", chips=1000)
            for i in range(4)
        ]
        
        # Add players to table
        for i, player in enumerate(self.players):
            self.table.add_player(player, position=i)
            # Set all players as ACTIVE instead of default SITTING_OUT
            player.status = PlayerStatus.ACTIVE
    
    def test_table_creation(self):
        """Test that tables can be created with proper attributes."""
        table = Table("t1", "Table 1", max_seats=9)
        self.assertEqual(table.id, "t1")
        self.assertEqual(table.name, "Table 1")
        self.assertEqual(table.max_seats, 9)
        self.assertEqual(len(table.seats), 9)
        self.assertEqual(table.dealer_position, -1)
    
    def test_add_player(self):
        """Test adding a player to the table."""
        # Add player to specific position
        new_player = Player("new1", name="New Player 1", chips=1000)
        result = self.table.add_player(new_player, position=4)
        
        self.assertTrue(result)
        self.assertEqual(self.table.seats[4], new_player)
        self.assertEqual(new_player.position, 4)
        
        # Add player to first available position
        new_player2 = Player("new2", name="New Player 2", chips=1000)
        result = self.table.add_player(new_player2)
        
        self.assertTrue(result)
        self.assertEqual(self.table.seats[5], new_player2)
        self.assertEqual(new_player2.position, 5)
        
        # Try to add player when table is full
        new_player3 = Player("new3", name="New Player 3", chips=1000)
        result = self.table.add_player(new_player3)
        
        self.assertFalse(result)
    
    def test_remove_player(self):
        """Test removing a player from the table."""
        player = self.players[0]
        result = self.table.remove_player(player)
        
        self.assertTrue(result)
        self.assertIsNone(self.table.seats[0])
        self.assertEqual(player.position, -1)
        
        # Try to remove player that's not at the table
        new_player = Player("new", name="New Player", chips=1000)
        result = self.table.remove_player(new_player)
        
        self.assertFalse(result)
    
    def test_get_player_at_position(self):
        """Test getting a player at a specific position."""
        # Valid position
        player = self.table.get_player_at_position(1)
        self.assertEqual(player, self.players[1])
        
        # Invalid position (negative)
        player = self.table.get_player_at_position(-1)
        self.assertIsNone(player)
        
        # Invalid position (too large)
        player = self.table.get_player_at_position(10)
        self.assertIsNone(player)
    
    def test_get_player_positions(self):
        """Test getting a mapping of player IDs to positions."""
        positions = self.table.get_player_positions()
        
        for i, player in enumerate(self.players):
            self.assertEqual(positions[player.id], i)
    
    def test_get_empty_seats(self):
        """Test getting a list of empty seat positions."""
        # Initially positions 4 and 5 are empty
        empty_seats = self.table.get_empty_seats()
        self.assertEqual(set(empty_seats), {4, 5})
        
        # Add player to position 4
        new_player = Player("new", name="New Player", chips=1000)
        self.table.add_player(new_player, position=4)
        
        # Now only position 5 should be empty
        empty_seats = self.table.get_empty_seats()
        self.assertEqual(empty_seats, [5])
    
    def test_is_full_and_empty(self):
        """Test checking if the table is full or empty."""
        # Table with 4 players should not be full or empty
        self.assertFalse(self.table.is_full())
        self.assertFalse(self.table.is_empty())
        
        # Remove all players
        for player in list(self.players):
            self.table.remove_player(player)
        
        # Table should now be empty
        self.assertTrue(self.table.is_empty())
        self.assertFalse(self.table.is_full())
        
        # Add players to all seats
        for i in range(self.table.max_seats):
            player = Player(f"full{i}", name=f"Full {i}", chips=1000)
            self.table.add_player(player, position=i)
        
        # Table should now be full
        self.assertTrue(self.table.is_full())
        self.assertFalse(self.table.is_empty())
    
    def test_player_counts(self):
        """Test getting player counts."""
        # 4 total players
        self.assertEqual(self.table.player_count(), 4)
        
        # Mark one player as eliminated
        self.players[0].status = PlayerStatus.ELIMINATED
        
        # Active player count should be 3
        self.assertEqual(self.table.active_player_count(), 3)
    
    def test_advance_dealer_button(self):
        """Test advancing the dealer button."""
        # Set initial dealer position
        self.table.dealer_position = 0
        
        # Advance dealer button
        new_pos = self.table.advance_dealer_button()
        
        # Dealer should move to next occupied seat
        self.assertEqual(new_pos, 1)
        self.assertEqual(self.table.dealer_position, 1)
        
        # Remove player 2
        self.table.remove_player(self.players[1])
        
        # Advance dealer button
        new_pos = self.table.advance_dealer_button()
        
        # Dealer should skip empty seat and move to next occupied seat
        self.assertEqual(new_pos, 2)
        self.assertEqual(self.table.dealer_position, 2)
    
    def test_get_blinds_positions(self):
        """Test getting blind positions."""
        # Set dealer position
        self.table.dealer_position = 1
        
        # Get blind positions
        sb_pos, bb_pos = self.table.get_blinds_positions()
        
        # Small blind should be left of dealer, big blind left of small blind
        self.assertEqual(sb_pos, 2)
        self.assertEqual(bb_pos, 3)
        
        # Test with only 2 players (heads-up)
        self.table.seats = [None] * self.table.max_seats
        self.table.add_player(self.players[0], position=0)
        self.table.add_player(self.players[1], position=2)
        self.table.dealer_position = 0
        
        # In heads-up, dealer is SB and other player is BB
        sb_pos, bb_pos = self.table.get_blinds_positions()
        self.assertEqual(sb_pos, 0)
        self.assertEqual(bb_pos, 2)
    
    def test_get_active_players(self):
        """Test getting a list of active players."""
        # Set all players as active
        for player in self.players:
            player.status = PlayerStatus.ACTIVE
        
        # Mark player 1 as folded
        self.players[1].status = PlayerStatus.FOLDED
        
        # Get active players
        active_players = self.table.get_active_players()
        
        # Should be players 0, 2, and 3
        self.assertEqual(len(active_players), 3)
        self.assertIn(self.players[0], active_players)
        self.assertIn(self.players[2], active_players)
        self.assertIn(self.players[3], active_players)
        self.assertNotIn(self.players[1], active_players)
    
    def test_get_next_to_act(self):
        """Test getting the next player to act."""
        # Set up some state
        for player in self.players:
            player.status = PlayerStatus.ACTIVE
            player.has_acted = False
        
        # Set dealer position
        self.table.dealer_position = 0
        
        # Get active players list
        self.table.update_active_players()
        
        # Get next to act (should be player 1)
        next_player = self.table.get_next_to_act()
        self.assertEqual(next_player, self.players[1])
        
        # Mark player 1 as acted
        self.players[1].has_acted = True
        
        # Get next to act (should be player 2)
        next_player = self.table.get_next_to_act()
        self.assertEqual(next_player, self.players[2])


if __name__ == "__main__":
    unittest.main()