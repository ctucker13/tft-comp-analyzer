## Convenience targets for the Reflex UI

.PHONY: ui ui-prod ui-port ui-clean

ui:
	uv sync
	uv run reflex run --loglevel info

ui-prod:
	uv sync
	uv run reflex run --env prod

# Usage: make ui-port PORT=3002
ui-port:
	uv sync
	uv run reflex run --port $(PORT)

ui-clean:
	rm -rf .web .next .reflex_cache || true
	@echo "Cleaned Reflex build artifacts"

