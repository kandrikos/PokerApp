// Game page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Get player information from localStorage
    const playerId = localStorage.getItem('player_id');
    const playerName = localStorage.getItem('player_name');
    
    if (!playerId || !playerName) {
        alert('Player information not found. Redirecting to home page.');
        window.location.href = '/';
        return;
    }
    
    // Display player name
    document.getElementById('player-name').textContent = playerName;
    
    // Game state
    let gameState = {
        status: 'WAITING',
        betting_round: 'PREFLOP',
        pot: 0,
        current_bet: 0,
        community_cards: [],
        players: [],
        current_player_idx: -1,
        available_actions: {}
    };
    
    // Card rendering
    function renderCard(card) {
        if (card === 'XX' || card === '??') {
            return `<div class="playing-card card-back"></div>`;
        }
        
        // Parse card value and suit
        const value = card.slice(0, -1);
        const suit = card.slice(-1);
        
        // Determine card color (red for hearts/diamonds, black for clubs/spades)
        const color = (suit === '♥' || suit === '♦') ? 'red' : 'black';
        
        return `
            <div class="playing-card">
                <div class="card-value ${color}">${value}</div>
                <div class="card-suit ${color}">${suit}</div>
            </div>
        `;
    }
    
    // Get initials from name for avatar
    function getInitials(name) {
        if (!name) return '?';
        return name.split(' ').map(n => n[0]).join('').toUpperCase();
    }
    
    // Render community cards
    function renderCommunityCards() {
        const container = document.getElementById('community-cards');
        
        if (gameState.community_cards.length === 0) {
            // Show placeholders for community cards
            container.innerHTML = `
                <div class="playing-card card-back"></div>
                <div class="playing-card card-back"></div>
                <div class="playing-card card-back"></div>
                <div class="playing-card card-back"></div>
                <div class="playing-card card-back"></div>
            `;
            return;
        }
        
        // Render actual community cards
        container.innerHTML = gameState.community_cards.map(card => renderCard(card)).join('');
        
        // Add placeholders for missing cards
        const placeholders = 5 - gameState.community_cards.length;
        for (let i = 0; i < placeholders; i++) {
            container.innerHTML += `<div class="playing-card card-back"></div>`;
        }
    }
    
    // Render player position on the table
    function renderPlayerPosition(player, position) {
        if (!player) return '';
        
        // Status indicator
        let statusClass = '';
        if (player.status === 'FOLDED') statusClass = 'folded';
        else if (player.status === 'ACTIVE' || player.status === 'ALL_IN') statusClass = 'active';
        
        // Current player indicator
        const isCurrent = gameState.current_player_idx === position ? 'current' : '';
        
        // Dealer, SB, BB indicators - using a cleaner approach with position markers
        let positionIndicators = '';
        
        if (player.is_dealer) {
            positionIndicators += `<div class="dealer-button dealer" style="bottom: -10px; right: 50%; transform: translateX(50%);">D</div>`;
        }
        if (player.is_small_blind) {
            positionIndicators += `<div class="dealer-button small-blind" style="bottom: -10px; left: 30%;">S</div>`;
        }
        if (player.is_big_blind) {
            positionIndicators += `<div class="dealer-button big-blind" style="bottom: -10px; right: 30%;">B</div>`;
        }
        
        // Player bet as chip pile
        const chipDisplay = player.current_bet > 0 ? 
            `<div class="chip-pile" style="top: -15px; left: 50%; transform: translateX(-50%);">${player.current_bet}</div>` : '';
        
        // Player cards - compact mini display
        const cards = player.cards ? 
            `<div class="player-cards-mini">${player.cards.map(card => renderCard(card)).join('')}</div>` : '';
        
        const isMe = player.id === playerId ? '(You)' : '';
        
        return `
            <div class="player-position position-${position} ${statusClass} ${isCurrent}" id="player-${position}">
                <div class="player-avatar">${getInitials(player.name)}</div>
                <div class="player-name">${player.name} ${isMe}</div>
                <div class="player-chips">$${player.chips}</div>
                ${cards}
                ${chipDisplay}
                ${positionIndicators}
            </div>
        `;
    }
    
    // Render table with players
    function renderTable() {
        const table = document.getElementById('table');
        let html = '';
        
        // Render each player position
        for (let i = 0; i < 8; i++) {
            // Find player at this position
            const player = gameState.players ? gameState.players[i] : null;
            html += renderPlayerPosition(player, i);
        }
        
        table.innerHTML = html;
    }
    
    // Render player's cards
    function renderPlayerCards() {
        const container = document.getElementById('player-cards');
        
        // Find current player
        const player = gameState.players ? gameState.players.find(p => p && p.id === playerId) : null;
        
        if (!player || !player.cards) {
            container.innerHTML = '';
            return;
        }
        
        container.innerHTML = player.cards.map(card => renderCard(card)).join('');
    }
    
    // Update player info
    function updatePlayerInfo() {
        // Find current player
        const player = gameState.players ? gameState.players.find(p => p && p.id === playerId) : null;
        
        if (!player) return;
        
        // Update chips and bet
        document.getElementById('chips').textContent = player.chips;
        document.getElementById('bet').textContent = player.current_bet;
    }
    
    // Update pot display
    function updatePotDisplay() {
        document.getElementById('pot').textContent = gameState.pot;
    }
    
    // Update available actions
    function updateAvailableActions() {
        // Default: hide all action buttons
        document.getElementById('fold-btn').classList.add('hidden');
        document.getElementById('check-btn').classList.add('hidden');
        document.getElementById('call-btn').classList.add('hidden');
        document.getElementById('bet-btn').classList.add('hidden');
        document.getElementById('raise-btn').classList.add('hidden');
        document.getElementById('all-in-btn').classList.add('hidden');
        document.getElementById('bet-raise-container').classList.add('hidden');
        
        // Hide player actions section if not in BETTING state
        if (gameState.status !== 'BETTING') {
            document.getElementById('player-actions').classList.add('hidden');
            return;
        }
        
        // Find current player
        const currentPosition = gameState.current_player_idx;
        const currentPlayer = gameState.players ? gameState.players[currentPosition] : null;
        
        // Show player actions only if it's the player's turn
        if (currentPlayer && currentPlayer.id === playerId) {
            document.getElementById('player-actions').classList.remove('hidden');
            
            // Show available actions
            const actions = gameState.available_actions || {};
            
            if ('FOLD' in actions) {
                document.getElementById('fold-btn').classList.remove('hidden');
            }
            
            if ('CHECK' in actions) {
                document.getElementById('check-btn').classList.remove('hidden');
            }
            
            if ('CALL' in actions) {
                const callBtn = document.getElementById('call-btn');
                callBtn.classList.remove('hidden');
                callBtn.textContent = `Call $${actions.CALL}`;
            }
            
            if ('BET' in actions) {
                document.getElementById('bet-btn').classList.remove('hidden');
                document.getElementById('bet-raise-container').classList.remove('hidden');
                
                // Update slider
                const slider = document.getElementById('bet-slider');
                const player = gameState.players.find(p => p && p.id === playerId);
                
                if (player) {
                    // Minimum bet should be big blind or minimum allowed bet
                    // Default to big blind (usually 10)
                    const bigBlind = gameState.blinds?.big_blind || 10;
                    const minBet = Math.max(bigBlind, actions.BET || 10);
                    // Start with a reasonable default bet (2x big blind)
                    const defaultBet = Math.min(minBet * 2, player.chips);
                    const maxBet = player.chips;
                    
                    // Configure the slider
                    slider.min = minBet;
                    slider.max = maxBet;
                    slider.value = defaultBet;
                    slider.step = 5; // Allow increments of 5
                    
                    // Force slider to update visually
                    slider.style.backgroundSize = ((defaultBet - minBet) * 100) / (maxBet - minBet) + '% 100%';
                    
                    // Update the bet amount text
                    document.getElementById('bet-amount').textContent = `$${defaultBet}`;
                    
                    // Ensure the slider is enabled
                    slider.disabled = false;
                }
            }
            
            if ('RAISE' in actions) {
                document.getElementById('raise-btn').classList.remove('hidden');
                document.getElementById('bet-raise-container').classList.remove('hidden');
                
                // Update slider
                const slider = document.getElementById('bet-slider');
                const player = gameState.players.find(p => p && p.id === playerId);
                
                if (player) {
                    // Min raise is usually current bet plus the previous raise amount
                    const minRaise = Math.max(actions.RAISE, 1);
                    // Default to 2x the minimum raise
                    const defaultRaise = Math.min(minRaise * 2, player.chips);
                    const maxRaise = player.chips;
                    
                    // Configure the slider
                    slider.min = minRaise;
                    slider.max = maxRaise;
                    slider.value = defaultRaise;
                    slider.step = 5; // Allow increments of 5
                    
                    // Force slider to update visually
                    slider.style.backgroundSize = ((defaultRaise - minRaise) * 100) / (maxRaise - minRaise) + '% 100%';
                    
                    // Update the bet amount text
                    document.getElementById('bet-amount').textContent = `$${defaultRaise}`;
                    
                    // Ensure the slider is enabled
                    slider.disabled = false;
                }
            }
            
            if ('ALL_IN' in actions) {
                document.getElementById('all-in-btn').classList.remove('hidden');
            }
        } else {
            document.getElementById('player-actions').classList.add('hidden');
        }
    }
    
    // Update game status
    function updateGameStatus() {
        document.getElementById('status').textContent = gameState.status;
        updatePotDisplay();
        
        // Show/hide start button
        if (gameState.status === 'WAITING') {
            document.getElementById('start-game-btn').classList.remove('hidden');
        } else {
            document.getElementById('start-game-btn').classList.add('hidden');
        }
        
        // Update blinds if available
        if (gameState.blinds) {
            document.getElementById('small-blind').textContent = gameState.blinds.small_blind;
            document.getElementById('big-blind').textContent = gameState.blinds.big_blind;
        }
    }
    
    // Add log entry
    function addLogEntry(message) {
        const logEntries = document.getElementById('log-entries');
        const now = new Date();
        const timeStr = now.toLocaleTimeString();
        
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `
            <span class="log-time">[${timeStr}]</span> 
            <span class="log-message">${message}</span>
        `;
        
        logEntries.appendChild(entry);
        logEntries.scrollTop = logEntries.scrollHeight;
    }
    
    // Update the entire game UI
    function updateGameUI() {
        renderCommunityCards();
        renderTable();
        renderPlayerCards();
        updatePlayerInfo();
        updatePotDisplay();
        updateAvailableActions();
        updateGameStatus();
    }
    
    // WebSocket connection
    let socket;
    
    function connectWebSocket() {
        socket = new WebSocket(`ws://${window.location.host}/ws/${GAME_ID}/${playerId}`);
        
        // Connection opened
        socket.addEventListener('open', function(event) {
            addLogEntry('Connected to the game server');
        });
        
        // Listen for messages
        socket.addEventListener('message', function(event) {
            const message = JSON.parse(event.data);
            
            if (message.type === 'game_state') {
                gameState = message.state;
                updateGameUI();
                
                // Log major game events
                if (gameState.status === 'BETTING' && gameState.betting_round === 'PREFLOP') {
                    addLogEntry('New hand started');
                } else if (gameState.betting_round === 'FLOP' && gameState.community_cards.length === 3) {
                    addLogEntry('Flop dealt');
                } else if (gameState.betting_round === 'TURN' && gameState.community_cards.length === 4) {
                    addLogEntry('Turn dealt');
                } else if (gameState.betting_round === 'RIVER' && gameState.community_cards.length === 5) {
                    addLogEntry('River dealt');
                } else if (gameState.status === 'SHOWDOWN') {
                    addLogEntry('Showdown');
                }
            }
        });
        
        // Connection closed
        socket.addEventListener('close', function(event) {
            addLogEntry('Disconnected from the game server');
            
            // Try to reconnect after a delay
            setTimeout(connectWebSocket, 3000);
        });
        
        // Connection error
        socket.addEventListener('error', function(event) {
            console.error('WebSocket error:', event);
            addLogEntry('Connection error');
        });
    }
    
    // Initialize the connection
    connectWebSocket();
    
    // Event listeners for action buttons
    document.getElementById('fold-btn').addEventListener('click', function() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'action',
                action: 'FOLD'
            }));
        }
    });
    
    document.getElementById('check-btn').addEventListener('click', function() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'action',
                action: 'CHECK'
            }));
        }
    });
    
    document.getElementById('call-btn').addEventListener('click', function() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'action',
                action: 'CALL'
            }));
        }
    });
    
    document.getElementById('bet-btn').addEventListener('click', function() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            // Get the selected bet amount from the slider
            const amount = parseInt(document.getElementById('bet-slider').value);
            
            // Make sure we're sending a valid bet amount
            if (amount > 0) {
                console.log(`Sending BET action with amount: ${amount}`);
                socket.send(JSON.stringify({
                    type: 'action',
                    action: 'BET',
                    amount: amount
                }));
            } else {
                console.error("Invalid bet amount");
            }
        }
    });
    
    document.getElementById('raise-btn').addEventListener('click', function() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            // Get the selected raise amount from the slider
            const amount = parseInt(document.getElementById('bet-slider').value);
            
            // Make sure we're sending a valid raise amount
            if (amount > 0) {
                console.log(`Sending RAISE action with amount: ${amount}`);
                socket.send(JSON.stringify({
                    type: 'action',
                    action: 'RAISE',
                    amount: amount
                }));
            } else {
                console.error("Invalid raise amount");
            }
        }
    });
    
    document.getElementById('all-in-btn').addEventListener('click', function() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'action',
                action: 'ALL_IN'
            }));
        }
    });
    
    // Bet slider
    document.getElementById('bet-slider').addEventListener('input', function() {
        document.getElementById('bet-amount').textContent = `$${this.value}`;
    });
    
    // Start game button
    document.getElementById('start-game-btn').addEventListener('click', function() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'start_game'
            }));
        }
    });
});