#!/bin/bash

# ADHDQuest Frontend Bootstrapping Script (Run from packages/frontend)

echo "=========================================="
echo "🌟 Starting ADHDQuest Frontend Dev Server..."
echo "=========================================="

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# 1. Install dependencies and link workspaces if not done
if [ ! -d "../../node_modules" ] || [ ! -d "node_modules" ]; then
  echo "📦 Installing workspace dependencies from root..."
  (cd ../.. && pnpm install)
fi

# 2. Start the Vite development server
echo ""
echo "🚀 Booting Vite dev server..."
echo "📍 Access the app at: http://localhost:5173"
echo "💡 Use the Developer Sandbox buttons on the login page to easily test Parent Upload, Game Frame, and Doctor Dashboard views without active keys."
echo "=========================================="

pnpm run dev
