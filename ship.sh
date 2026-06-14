#!/bin/bash

# V3X ZULFIQAR-GIDEON: The Sovereign Ship Script
# This script automates the versioning, building, and deployment of the engine.

# Exit on any error
set -e

echo "⚔️ V3X ZULFIQAR-GIDEON: Preparing to Ship..."

# 1. Ask for version
current_version=$(grep -oP 'version = "\K[^"]+' pyproject.toml)
echo "Current version: $current_version"
read -p "Enter new version (e.g., 1.1.1): " new_version

if [ -z "$new_version" ]; then
    echo "❌ Version cannot be empty."
    exit 1
fi

# 2. Update pyproject.toml
sed -i "s/version = \"$current_version\"/version = \"$new_version\"/" pyproject.toml
echo "✅ pyproject.toml updated to $new_version"

# 3. Clean and Build
echo "🧹 Cleaning old builds..."
rm -rf dist/ build/ *.egg-info/ v3x_zulfiqar_gideon.egg-info/

echo "🏗️ Building distribution artifacts..."
source .venv/bin/activate
python -m build
twine check dist/*

# 4. Git Push
echo "🐙 Syncing with GitHub..."
git add pyproject.toml
git commit -m "build: Release version $new_version"
git tag -a "v$new_version" -m "Release $new_version"
git push origin master --tags

# 5. PyPI Upload
echo "📦 Uploading to PyPI..."
twine upload dist/*

echo "✨ V3X ZULFIQAR-GIDEON v$new_version is LIVE!"
echo "View at: https://pypi.org/project/v3x-zulfiqar-gideon/$new_version/"
