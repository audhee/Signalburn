#!/bin/bash

# Arohan All-in-One Startup Script for macOS
# This script automates Docker, Backend, Ngrok (with auto-.env update), and Frontend.

# Colors for better visibility
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}        Arohan Project Startup Manager           ${NC}"
echo -e "${BLUE}=================================================${NC}"

# 1. Start Docker Containers
echo -e "${YELLOW}[1/6] Checking Docker containers...${NC}"
if ! docker ps | grep -q "local-redis"; then
    echo "Starting Redis..."
    docker start local-redis 2>/dev/null || docker run -d -p 6379:6379 --name local-redis redis
fi

if ! docker ps | grep -q "local-postgres"; then
    echo "Starting PostgreSQL..."
    docker start local-postgres 2>/dev/null || docker run -d --name local-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=arohan_db -p 5433:5432 postgres
fi

# 2. Start Backend API
echo -e "${YELLOW}[2/6] Starting Backend API...${NC}"
if lsof -i :8000 > /dev/null; then
    echo "Port 8000 is already in use. Assuming backend is running."
else
    # Start in background and log to a file
    osascript -e 'tell application "Terminal" to do script "cd '"$(pwd)"'/backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"'
    echo "Backend launched in a new terminal window."
fi

# 3. Start Ngrok
echo -e "${YELLOW}[3/6] Starting Ngrok...${NC}"
if pgrep -x "ngrok" > /dev/null; then
    echo "Ngrok is already running."
else
    osascript -e 'tell application "Terminal" to do script "ngrok http 8000"'
    echo "Ngrok launched in a new terminal window."
fi

# 4. Wait for Ngrok and update .env
echo -e "${YELLOW}[4/6] Waiting for Ngrok to generate URL...${NC}"

# FIRST: Check if user manually put a https link in .env and respect it
if [ -f ".env" ] && grep -q "EXPO_PUBLIC_API_URL=https://" .env; then
    echo -e "${GREEN}Detected manual HTTPS URL in .env, keeping it.${NC}"
    grep "EXPO_PUBLIC_API_URL" .env
    NGROK_URL=$(grep "EXPO_PUBLIC_API_URL=" .env | cut -d'=' -f2)
else
    MAX_RETRIES=15
    RETRY_COUNT=0
    NGROK_URL=""

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        # Support both ngrok-free.app and ngrok-free.dev
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -oE 'https://[^"]*ngrok-free\.(app|dev)' | head -n 1)
        if [ -n "$NGROK_URL" ]; then
            break
        fi
        echo -n "."
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    echo ""

    if [ -z "$NGROK_URL" ]; then
        echo -e "${RED}Error: Could not fetch Ngrok URL automatically.${NC}"
        echo -e "${YELLOW}Please make sure Ngrok is running and update .env manually if needed.${NC}"
        # Fallback to local IP if possible
        LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1)
        if [ -n "$LOCAL_IP" ]; then
            echo -e "${YELLOW}Falling back to local IP: http://$LOCAL_IP:8000${NC}"
            NGROK_URL="http://$LOCAL_IP:8000"
        fi
    fi

    if [ -n "$NGROK_URL" ]; then
        echo -e "${GREEN}Using API URL: $NGROK_URL${NC}"
        # Update or create .env file
        if [ -f ".env" ]; then
            # Replace existing EXPO_PUBLIC_API_URL or add if missing
            if grep -q "EXPO_PUBLIC_API_URL=" .env; then
                sed -i '' "s|EXPO_PUBLIC_API_URL=.*|EXPO_PUBLIC_API_URL=$NGROK_URL|" .env
            else
                echo "EXPO_PUBLIC_API_URL=$NGROK_URL" >> .env
            fi
        else
            echo "EXPO_PUBLIC_API_URL=$NGROK_URL" > .env
        fi
        echo -e "${GREEN}.env file updated successfully!${NC}"
    fi
fi

# 5. Fix Asset Issues
echo -e "${YELLOW}[5/6] Checking assets...${NC}"
if [ ! -f "assets/icon.png" ] && [ -f "assets/images/icon.png" ]; then
    cp assets/images/icon.png assets/icon.png
    echo "Fixed missing assets/icon.png"
fi

# 6. Start Frontend (Expo)
echo -e "${YELLOW}[6/6] Starting Expo Frontend...${NC}"
echo -e "${GREEN}Login Credentials: 9999999999 / 123456${NC}"
npx expo start
