#!/bin/bash
# Quick start script for Lumens Mobile App

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Lumens Mobile App${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/${NC}"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}❌ Node.js version 18+ is required. Current version: $(node -v)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js $(node -v) found${NC}"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found. Please run this script from apps/mobile directory${NC}"
    exit 1
fi

# Set API base URL if not already set
if [ -z "$API_BASE" ]; then
    export API_BASE="https://lumens-api-4qubw3p5lq-uc.a.run.app"
    echo -e "${YELLOW}📡 API_BASE not set, using default: $API_BASE${NC}"
else
    echo -e "${GREEN}📡 Using API_BASE: $API_BASE${NC}"
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm install
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Check if Expo CLI is available
if ! command -v expo &> /dev/null && ! command -v npx &> /dev/null; then
    echo -e "${RED}❌ Expo CLI not found. Please install Expo CLI or use npx${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Starting Expo development server...${NC}"
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "   - Press 'a' to open Android emulator"
echo -e "   - Press 'i' to open iOS simulator (macOS only)"
echo -e "   - Press 'w' to open in web browser"
echo -e "   - Scan QR code with Expo Go app on your phone"
echo -e "   - Press 'r' to reload the app"
echo -e "   - Press 'm' to toggle menu"
echo ""

# Start Expo
npx expo start

