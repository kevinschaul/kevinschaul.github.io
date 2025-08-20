.PHONY: help dev install build clean css

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Start tailwind, hugo server
	@echo "This will run Tailwind CSS watching and Hugo serve in parallel"
	@trap 'kill 0' EXIT; \
	npm run dev:tailwind & \
	hugo serve & \
	wait

install: ## Install dependencies
	npm install
	go install github.com/gohugoio/hugo@v0.111.3

build: ## Build the site (only needed for testing)
	npm run build:tailwind
	hugo --minify

clean: ## Clean build artifacts
	rm -rf public/
	rm -f static/css/main.css

css: ## Build tailwind css
	npm run build:tailwind

