#!/bin/bash

# Check if the title argument is provided
if [ -z "$1" ]; then
    echo "Error: Please provide a title for the blog post."
    exit 1
fi

# Get the title argument and current date
title="$1"
current_date=$(date +%Y-%m-%d)

# Slugify the title
slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr '_' '-' | tr -d '()')

# Create the directory
dir_name="$current_date-$slug"
dir_path="$HOME/dev/kevinschaul.github.io/content/til/$dir_name"
mkdir -p "$dir_path"

# Create the index.md file
index_file="$dir_path/index.md"
cat << EOF > "$index_file"
---
title: $title
date: $current_date
slug: $slug
tags: []
---
EOF

echo "New blog post directory created: $dir_path"

# Open the index.md file with the default editor
if [ -n "$EDITOR" ]; then
    "$EDITOR" "$index_file"
else
    echo "Warning: \$EDITOR environment variable not set."
fi

# Ask user if they want to commit and push changes
read -p "Do you want to commit and push changes? (y/n) " confirm

if [[ "$confirm" =~ ^[Yy]$ ]]; then
    repo_path="$HOME/dev/kevinschaul.github.io"
    (
        cd "$repo_path" || exit 1
        git pull origin main
        git add .
        git commit -m "New blog post: $title"
        git push origin main
    )
    echo "Changes committed and pushed to the repository."
else
    echo "Changes not committed or pushed."
fi
