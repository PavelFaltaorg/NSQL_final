# user-client/Dockerfile
FROM node:18-bullseye

# Install dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    xauth \
    libx11-6 \
    libxcomposite1 \
    libxrender1 \
    libxtst6 \
    libnss3 \
    libgtk-3-0 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy all other files to the container
COPY . .

# Expose a port if you have a web server running (not necessary for local Electron apps)
EXPOSE 3000

# Start the Electron app using xvfb-run to create a virtual display
CMD ["xvfb-run", "npm", "start"]
