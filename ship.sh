#!/bin/bash

# V3X ZULFIQAR-GIDEON: The Sovereign Ship Script
# This script automates the versioning, building, and deployment of the engine.

# Exit on any error
set -e

echo "⚔️ V3X ZULFIQAR-GIDEON: Preparing to Ship..."

# 1. Ask for version
current_version=$(grep -oP "version=\"\K[^\"]+" setup.py)
echo "Current version: $current_version"
read -p "Enter new version (e.g., 1.0.1): " new_version

if [ -z "$new_version" ]; then
    echo "❌ Version cannot be empty."
    exit 1
fi

# 2. Update setup.py
# Using sed to replace the version line
sed -i "s/version=\"$current_version\"/version=\"$new_version\"/" setup.py
echo "✅ setup.py updated to $new_version"

# 3. Clean and Build
echo "🧹 Cleaning old builds..."
rm -rf dist/ build/ *.egg-info/

echo "🏗️ Building distribution artifacts..."
source .venv/bin/activate
python3 setup.py sdist bdist_wheel
twine check dist/*

# 4. Git Push
echo "🐙 Syncing with GitHub..."
git add setup.py
git commit -m "build: Release version $new_version"
git tag -a "v$new_version" -m "Release $new_version"
git push origin master --tags

# 5. PyPI Upload
echo "📦 Uploading to PyPI..."
twine upload dist/*

echo "✨ V3X ZULFIQAR-GIDEON v$new_version is LIVE!"
echo "View at: https://pypi.org/project/v3x-zulfiqar-gideon/$new_version/"
