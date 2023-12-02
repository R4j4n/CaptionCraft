#!/bin/bash

# Target directory where fonts will be installed
TARGET_DIR="$HOME/.local/share/fonts"

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Copy all .ttf and .otf fonts from the current directory to the target directory
echo "Copying fonts..."
cp *.ttf *.otf "$TARGET_DIR"

# Update the font cache
echo "Updating font cache..."
fc-cache -fv

echo "Font installation complete."
