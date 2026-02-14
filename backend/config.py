#backend/config.py

# LLM Configuration
OLLAMA_MODEL = "phi3"
OLLAMA_BASE_URL = "http://localhost:11434"

# MCTS Configuration
MAX_MCTS_DEPTH = 3
MCTS_SIMULATIONS = 8  # Increased for better e-commerce planning

# Rate Limiting Configuration
LLM_RATE_LIMIT_DELAY = 0.3  # 300ms between LLM calls
WEB_REQUEST_DELAY = 1.0      # 1 second between web requests (avoid rate limiting)
REQUEST_TIMEOUT = 12         # 12 seconds timeout for web requests

# Search Configuration
MAX_SEARCH_RESULTS = 8       # Limit search results for faster processing
MAX_SCRAPE_CONTENT = 3000    # Max characters for scraped content

# E-commerce Configuration
MAX_PLATFORMS_TO_CHECK = 4   # Check top 4 platforms for real prices
PRICE_RANGE_MIN = 50         # Minimum valid price in INR
PRICE_RANGE_MAX = 500000     # Maximum valid price in INR
