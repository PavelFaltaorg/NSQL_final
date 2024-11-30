document.getElementById('login-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginError = document.getElementById('login-error');

    try {
        // Send the login request to the backend server
        const response = await fetch('http://127.0.0.1:8001/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        // Process the response from the server
        const data = await response.json();

        if (response.ok) {
            // Login successful: hide login section and show game menu
            loginError.style.display = 'none';
            document.getElementById('login-section').style.display = 'none';
            document.querySelector('.app-container').style.justifyContent = 'flex-start'; // Adjust layout for game menu
            document.getElementById('game-menu').style.display = 'flex';

            // Optionally store session ID for future requests
            localStorage.setItem('session_id', data.session_id);

        } else {
            // Login failed: display error message
            loginError.textContent = data.message || 'Something went wrong. Please try again.';
            loginError.style.display = 'block';
        }
    } catch (error) {
        console.error('Error during login:', error);
        loginError.textContent = 'An error occurred while trying to log in. Please try again later.';
        loginError.style.display = 'block';
    }

    document.getElementById('login-form').reset();
});

document.getElementById('btn-logout').addEventListener('click', async function() {
    try {
        document.getElementById('game-menu').style.display = 'none';
        document.getElementById('login-section').style.display = 'block';
        document.querySelector('.app-container').style.justifyContent = 'center'; // Restore layout for login

    } catch (error) {
        console.error('Error during logout:', error);
    }
});

// Play Button functionality
document.getElementById('btn-play').addEventListener('click', function() {
    // Send a message to the main process to start the game
    window.electronAPI.startGame(localStorage.getItem('session_id'));




});

// Settings Button functionality
document.getElementById('btn-settings').addEventListener('click', function() {
    document.getElementById('game-menu').style.display = 'none';  // Hide the game menu
    document.getElementById('settings-section').style.display = 'block';  // Show the settings section
});

// Back to menu from settings Button functionality
document.getElementById('btn-back-to-menu-settings').addEventListener('click', function() {
    document.getElementById('settings-section').style.display = 'none';  // Hide settings section
    document.getElementById('game-menu').style.display = 'flex';  // Show the game menu again
});

// Customize Button functionality
document.getElementById('btn-customize').addEventListener('click', function() {
    document.getElementById('game-menu').style.display = 'none';  // Hide the game menu
    document.getElementById('customize-section').style.display = 'block';  // Show the customize section
});

// Back to menu from customize Button functionality
document.getElementById('btn-back-to-menu-customize').addEventListener('click', function() {
    document.getElementById('customize-section').style.display = 'none';  // Hide customize section
    document.getElementById('game-menu').style.display = 'flex';  // Show the game menu again
});

// Utility function to convert hex to RGB
function hexToRgb(hex) {
    // Remove the "#" if present
    hex = hex.replace(/^#/, '');

    // Parse the hex color string
    if (hex.length === 6) {
        const bigint = parseInt(hex, 16);
        return {
            r: (bigint >> 16) & 255,
            g: (bigint >> 8) & 255,
            b: bigint & 255,
        };
    } else {
        return null; // Invalid format
    }
}

// Color Change functionality
document.getElementById('confirm-color-change').addEventListener('click', async function(event) {
    const hexColor = document.getElementById('player-color').value;

    // Convert hex to RGB
    const rgbColor = hexToRgb(hexColor);
    if (!rgbColor) {
        console.error('Invalid color format');
        return;
    }
    window.electronAPI.sendMessage(`Changing player color to RGB(${rgbColor.r}, ${rgbColor.g}, ${rgbColor.b})`);
    // Send the RGB values to the backend
    try {
        const response = await fetch('http://127.0.0.1:8001/changeplayercolor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: localStorage.getItem('session_id'),
                red: rgbColor.r,
                green: rgbColor.g,
                blue: rgbColor.b,
            }),
        });

        // Debugging
        window.electronAPI.sendMessage(JSON.stringify({
            session_id: localStorage.getItem('session_id'),
            red: rgbColor.r,
            green: rgbColor.g,
            blue: rgbColor.b,
        }));

        if (response.ok) {
            window.electronAPI.sendMessage("Color changed successfully!");
        }


    } catch (error) {
        window.electronAPI.sendMessage("An error occurred while trying to change the color. Please try again later.");
        window.electronAPI.sendMessage(error);
    }
});

// Name Change functionality
document.getElementById('confirm-name-change').addEventListener('click', async function(event) {
    const newName = document.getElementById('player-name').value;

    // Send the new name to the backend
    try {
        const response = await fetch('http://127.0.0.1:8001/changeplayername', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: localStorage.getItem('session_id'),
                name: newName,
            }),
        });

        if (response.ok) {
            window.electronAPI.sendMessage("Name changed successfully!");
        }

    } catch (error) {
        window.electronAPI.sendMessage("An error occurred while trying to change the name. Please try again later.");
        window.electronAPI.sendMessage(error);
    }
});