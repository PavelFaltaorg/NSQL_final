document.getElementById('login-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginError = document.getElementById('login-error');

    // Simulate login verification (replace with real authentication logic)
    if (username === 'player' && password === 'pwd') {
        loginError.style.display = 'none';
        document.getElementById('login-section').style.display = 'none';
        document.querySelector('.app-container').style.justifyContent = 'flex-start'; // Adjust for full-width game menu
        document.getElementById('game-menu').style.display = 'flex';
    } else {
        loginError.textContent = 'Invalid username or password. Please try again.';
        loginError.style.display = 'block';
    }
});
