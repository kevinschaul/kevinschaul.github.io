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
