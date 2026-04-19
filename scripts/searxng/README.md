# SearXNG — self-hosted search for agentic-ai-cookbook-lab recipes

Runs a local SearXNG instance with the JSON API enabled, so our research-assistant recipe can query the web without any paid search API (Exa, Tavily, Brave, OpenAI web_search).

## Start

```bash
# First time only
cp .env.example .env
echo "SEARXNG_SECRET=$(openssl rand -hex 32)" > .env

# Start
docker compose up -d

# Verify
curl -s "http://localhost:8888/search?q=hello&format=json" | jq '.results | length'
# → should print a number > 0
```

## Stop

```bash
docker compose down
```

## Used by

- `recipes/by-use-case/research-assistant/` — when `SEARCH_PROVIDER=searxng` (default).
- Any future recipe that needs web search.

Runs on both macOS (Docker Desktop) and Linux (Docker Engine). No GPU needed.
