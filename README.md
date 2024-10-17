Nějaký nápady co se mi líbí co mi vyhodilo gpt:

### 1. **Real-Time Chat Application**
   - **Description**: Create a chat application where users can create accounts, join rooms, and message each other in real time. Redis can be used for managing user sessions and WebSocket connections for real-time communication, while MongoDB stores chat histories and user profiles.
   - **Key Features**:
     - Real-time messaging (Redis for Pub/Sub or message queue)
     - MongoDB for chat history and user accounts
     - Authentication and user sessions

### 2. **Collaborative Document Editor**
   - **Description**: A web-based real-time collaborative document editing tool. MongoDB stores document revisions and user data, while Redis is used for real-time collaboration and syncing changes between users.
   - **Key Features**:
     - MongoDB for storing documents and versioning history
     - Redis for real-time data syncing between multiple users
     - Flask backend with WebSocket for real-time collaboration

### 3. **Social Media Platform**
   - **Description**: Create a simple social media platform where users can post updates, like, comment, and follow others. Use MongoDB for storing posts, user profiles, and interactions, while Redis can handle caching frequently accessed data (like popular posts) and managing user sessions.
   - **Key Features**:
     - MongoDB for user data, posts, comments, likes, and followers
     - Redis for session management and caching hot content (e.g., trending posts)
     - Real-time notifications using Redis (e.g., new likes or comments)
     - Basic newsfeed algorithm to show users the latest or trending posts

### 4. **Real-Time Multiplayer Quiz Game**
   - **Description**: Develop a real-time multiplayer quiz game where players can join rooms and compete by answering questions. Use Redis for handling real-time gameplay and syncing player answers, while MongoDB stores user profiles, game history, and leaderboard data.
   - **Key Features**:
     - Redis for syncing game state and managing player actions in real-time
     - MongoDB for storing user profiles, questions, and game results
     - Leaderboard to display top players or winners
     - Live chat functionality for players in the same game room

### 5. **E-Shop (jakýhokoliv druhu)**

### 6. **Aplikace se sportovnímy výsledky**
   - **Description**: inspirace: www.vysledky.com
