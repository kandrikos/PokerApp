// Home page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Create game form handling
    const createGameForm = document.getElementById('create-game-form');
    if (createGameForm) {
        createGameForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            try {
                const response = await fetch('/api/create_game', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (data.error) {
                    alert(`Error: ${data.error}`);
                    return;
                }
                
                // Prompt for player name
                const playerName = prompt('Enter your name:');
                if (!playerName) return;
                
                // Join the game
                const joinResponse = await fetch(`/api/join_game/${data.game_id}?player_name=${encodeURIComponent(playerName)}`, {
                    method: 'POST'
                });
                
                const joinData = await joinResponse.json();
                
                if (joinData.error) {
                    alert(`Error: ${joinData.error}`);
                    return;
                }
                
                // Store player info in localStorage
                localStorage.setItem('player_id', joinData.player_id);
                localStorage.setItem('player_name', playerName);
                
                // Redirect to the game page
                window.location.href = `/game/${data.game_id}`;
                
            } catch (error) {
                console.error('Error creating game:', error);
                alert('Failed to create game. Please try again.');
            }
        });
    }
    
    // Join game form handling
    const joinGameForm = document.getElementById('join-game-form');
    if (joinGameForm) {
        joinGameForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const gameId = document.getElementById('game-id').value.trim();
            const playerName = document.getElementById('player-name').value.trim();
            
            if (!gameId || !playerName) {
                alert('Please enter both game ID and your name.');
                return;
            }
            
            try {
                const response = await fetch(`/api/join_game/${gameId}?player_name=${encodeURIComponent(playerName)}`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.error) {
                    alert(`Error: ${data.error}`);
                    return;
                }
                
                // Store player info in localStorage
                localStorage.setItem('player_id', data.player_id);
                localStorage.setItem('player_name', playerName);
                
                // Redirect to the game page
                window.location.href = `/game/${gameId}`;
                
            } catch (error) {
                console.error('Error joining game:', error);
                alert('Failed to join game. Please check the game ID and try again.');
            }
        });
    }
});