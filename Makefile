# Makefile for Kevin Schaul's Hugo site with Tailwind CSS v4

.PHONY: dev build clean install

# Development command - runs Tailwind watching and Hugo serve in parallel
dev:
	@echo "Starting development server..."
	@echo "This will run Tailwind CSS watching and Hugo serve in parallel"
	@trap 'kill 0' EXIT; \
	npm run dev:tailwind & \
	hugo serve & \
	wait

# Build the site with Tailwind CSS
build:
	@echo "Building site with Tailwind CSS..."
	npm run build:tailwind
	hugo --minify

# Clean build artifacts
clean:
	rm -rf public/
	rm -f static/css/main.css

# Install dependencies
install:
	npm install

# Build Tailwind CSS only
css:
	npm run build:tailwind

install-hugo:
	go install github.com/gohugoio/hugo@v0.111.3

# Help command
help:
	@echo "Available commands:"
	@echo "  make dev     - Start development server (Tailwind + Hugo)"
	@echo "  make build   - Build the site with Tailwind CSS"
	@echo "  make clean   - Clean build artifacts"
	@echo "  make install - Install npm dependencies"
	@echo "  make css     - Build Tailwind CSS only"
	@echo "  make help    - Show this help message"
