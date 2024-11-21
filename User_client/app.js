document.getElementById('login-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginError = document.getElementById('login-error');

    try {
        // Send the login request to the authentication server
        const response = await fetch('http://127.0.0.1:8002/login', {
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
            loginError.textContent = data.message || 'Invalid username or password. Please try again.';
            loginError.style.display = 'block';
        }
    } catch (error) {
        console.error('Error during login:', error);
        loginError.textContent = 'An error occurred while trying to log in. Please try again later.';
        loginError.style.display = 'block';
    }
});