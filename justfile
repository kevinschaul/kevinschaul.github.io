help:
    @just --list

# Start tailwind, hugo server
dev:
    #!/usr/bin/env bash
    echo "This will run Tailwind CSS watching and Hugo serve in parallel"
    trap 'kill 0' EXIT
    npm run dev:tailwind &
    hugo serve &
    wait

# Install dependencies
install:
    npm install
    go install github.com/gohugoio/hugo@v0.111.3

# Build the site (only needed for testing)
build:
    npm run build:tailwind
    hugo --minify

# Clean build artifacts
clean:
    rm -rf public/
    rm -f static/css/main.css

# Build tailwind css
css:
    npm run build:tailwind

# Format and lint Python code
check:
    uv run ruff check scripts/ tests/
    uv run ruff format scripts/ tests/ --check

# Fix linting and formatting of Python code
fix:
    uv run ruff check scripts/ tests/ --fix
    uv run ruff format scripts/ tests/

# Run tests
test:
    uv run pytest tests/

# Create a new post
post:
    #!/usr/bin/env bash
    # Get post title
    read -p "Enter post title: " title

    # Generate and confirm slug
    slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g' | sed 's/[^a-z0-9-]//g')
    read -p "Slug [$slug]: " slug_input
    slug=${slug_input:-$slug}

    # Generate and confirm date
    date=$(date +%Y-%m-%d)
    read -p "Date [$date]: " date_input
    date=${date_input:-$date}

    # Create directory and file
    dir="content/post/${date}-${slug}"
    mkdir -p "$dir"
    cat > "$dir/index.md" <<EOF
    ---
    title: $title
    date: '$date'
    slug: $slug
    tags: []
    show_on_homepage: yes
    blurb: ''
    tease: false
    ---

    EOF
    echo "Created new post: $dir/index.md"
    echo "Opening in editor..."
    ${EDITOR:-vim} "$dir/index.md"
