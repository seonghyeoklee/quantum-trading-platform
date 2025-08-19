#!/bin/bash

# Install Git Hooks for Quantum Trading Service

echo "🔧 Installing Git hooks..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Git hooks directory
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ Error: Not a git repository or .git directory not found"
    exit 1
fi

# Copy hooks
echo "📋 Copying hooks to .git/hooks/"

if [ -f "$SCRIPT_DIR/pre-commit" ]; then
    cp "$SCRIPT_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
    chmod +x "$GIT_HOOKS_DIR/pre-commit"
    echo "✅ pre-commit hook installed"
else
    echo "⚠️  pre-commit hook not found"
fi

# Set up git config for hooks
echo "⚙️  Configuring Git..."

# Configure git to use the hooks directory
git config core.hooksPath .githooks

echo "🎉 Git hooks installation complete!"
echo ""
echo "📝 Available hooks:"
echo "  - pre-commit: Runs code quality checks before commits"
echo ""
echo "💡 To bypass hooks temporarily, use: git commit --no-verify"
echo "🔧 To uninstall hooks, run: git config --unset core.hooksPath"