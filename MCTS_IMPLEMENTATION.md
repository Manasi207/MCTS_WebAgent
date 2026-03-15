# MCTS Implementation in Web AI Agent

## Architecture Overview

This project uses TRUE MCTS (Monte Carlo Tree Search) with 10 simulations for web-based scraping tasks.

## MCTS Usage Strategy

### ✅ MCTS IS USED FOR:

1. **E-commerce Price Comparison** (10 MCTS Simulations)
   - Builds MCTS tree with 10 simulations
   - Explores different platform visiting orders
   - Evaluates scraping success for each path
   - Selects optimal scraping strategy
   - Real-time price extraction from Amazon, Flipkart, Myntra

2. **Web Scraping (URL-based)** (2 Retry Attempts)
   - MCTS-driven retry logic for content extraction
   - Intelligent retry on failures
   - Structured content extraction

### ❌ MCTS IS NOT USED FOR:

- **Simple Queries**: Direct LLM response (fast)
- **General Reasoning**: Direct LLM response (no planning overhead)
- **Email Operations**: Direct tool execution

## Implementation Details

### E-commerce Flow (TRUE MCTS with 10 Simulations)
```
User Query → Classify as "ecommerce" → handle_ecommerce()
  ↓
Initialize MCTS State (3 platforms, product name)
  ↓
Run 10 MCTS Simulations:
  For each simulation:
    - Selection: Choose best node using UCB1
    - Expansion: Try new platform
    - Simulation: Rollout to terminal state
    - Backpropagation: Update node values
  ↓
Select Best Path (highest value)
  ↓
Execute Scraping on Best Path
  ↓
Compare Results → Return best price
```

### Web Scraping Flow (MCTS Retry Logic)
```
User Query → Extract URL → scrape_and_summarize()
  ↓
MCTS Retry Logic:
  - Attempt 1: Scrape URL
  - If fail → Attempt 2: Retry with delay
  - If fail → Return error
  ↓
Extract structured content → Return formatted data
```

### General Query Flow (Direct LLM)
```
User Query → Classify as "simple" or "general" → Direct LLM
  ↓
LLM Response → Return answer
```

## Configuration

```python
# config.py
MCTS_SIMULATIONS = 10              # TRUE MCTS simulations for e-commerce
MCTS_WEB_SCRAPING_RETRIES = 2      # Retry attempts for web scraping
WEB_REQUEST_DELAY = 0.5            # 500ms between requests
REQUEST_TIMEOUT = 10               # 10 seconds timeout
```

## MCTS Algorithm Details

**Selection**: Uses UCB1 (Upper Confidence Bound) formula:
```
UCB1 = (Q/N) + c * sqrt(2 * ln(parent_N) / N)
```

**Evaluation Function**:
- +5.0 points per successful scrape
- +10.0 bonus for scraping all platforms
- +5.0 bonus for at least 2 platforms (comparison possible)
- -1.0 penalty per failed attempt

**Simulation Strategy**:
- Prioritizes platforms by priority value (1=highest)
- Explores different visiting orders
- Evaluates each path's success rate

## Key Benefits

1. **Intelligent Path Selection**: MCTS finds optimal platform visiting order
2. **Robust Scraping**: 10 simulations ensure best strategy
3. **Real Data Only**: No AI estimates, only scraped data
4. **Offline Operation**: Works with local Ollama LLM (llama3.2)
5. **Adaptive**: Learns from simulation results

## Task Classification

| Task Type | MCTS Used? | Simulations | Example Query |
|-----------|------------|-------------|---------------|
| E-commerce | ✅ Yes | 10 | "compare price of Dell laptop" |
| Web Scraping | ✅ Yes | 2 retries | "scrape https://example.com" |
| Simple Query | ❌ No | 0 | "what is the capital of France?" |
| General Query | ❌ No | 0 | "list top 3 shopping websites" |
| Email | ❌ No | 0 | "send email to..." |

## Running the Project

```bash
cd backend
python main.py
```

Server starts at: http://localhost:8000

## Example Output

```
🔍 MCTS Price Comparison: Dell Laptop
======================================================================

🤖 Running 10 MCTS simulations for optimal scraping...

🌳 Building MCTS tree with 10 simulations...

✅ MCTS completed 10 simulations
📊 Visited platforms: Amazon India → Flipkart → Myntra
💰 Successfully scraped: 2/3 platforms

======================================================================

💰 LIVE PRICES FOUND (2 platforms):
----------------------------------------------------------------------

🛒 Amazon India:
   💵 Price: ₹45,990

🛒 Flipkart:
   💵 Price: ₹44,990

======================================================================
✅ BEST DEAL:
   🏆 Platform: Flipkart
   💰 Price: ₹44,990
```
