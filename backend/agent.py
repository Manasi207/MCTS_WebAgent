
#########################################################################################

# backend/agent.py
from llm import get_llm
from tools.ecommerce import handle_ecommerce
from tools.scraper import scrape_and_summarize
from tools.mail import send_email, fetch_unread_emails
import re


def classify(query: str):
    """Classify query type using keywords"""
    query_lower = query.lower()

    ecommerce_keywords = ['buy', 'purchase', 'compare price', 'product price', 'best price', 'cheapest']
    if any(keyword in query_lower for keyword in ecommerce_keywords):
        return "ecommerce"

    if any(word in query_lower for word in ['scrape', 'extract', 'fetch data', 'get content from']):
        return "scraper"

    if any(word in query_lower for word in ['email', 'send mail', 'compose email', 'latest mail']):
        return "mail"

    simple_keywords = ['what', 'who', 'when', 'where', 'capital', 'define', 'explain', 'tell me', 'how many']
    if any(keyword in query_lower for keyword in simple_keywords) and len(query.split()) < 15:
        return "simple"

    return "general"


def extract_url(query: str):
    """Extract URL from query"""
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, query)
    return match.group(0) if match else None


def handle_query(query: str, mcts_variant: str = "basic-mcts", simulations: int = 5):
    """
    Main query handler — routes to appropriate task handler.
    mcts_variant: "basic-mcts" | "r-mcts" | "wm-mcts" | "rag-mcts"
    simulations:  number of MCTS simulations (passed from QueryRequest)
    """

    task_type = classify(query)

    # ------------------------------------------------------------------
    # Simple queries: Direct LLM (no MCTS)
    # ------------------------------------------------------------------
    if task_type == "simple":
        llm = get_llm()
        final_answer = llm.invoke(f"Answer this question concisely and accurately: {query}")
        return {
            "mode":         "Local LLM (Llama3.2 via Ollama)",
            "task_type":    task_type,
            "plan":         ["Direct LLM Response"],
            "answer":       final_answer,
            "mcts_variant": None,
        }

    # ------------------------------------------------------------------
    # E-commerce: MCTS-based scraping (MCTS is inside the tool)
    # ------------------------------------------------------------------
    if task_type == "ecommerce":
        result = handle_ecommerce(query)
        return {
            "mode":         "Local LLM (Llama3.2 via Ollama) + MCTS Web Scraping",
            "task_type":    task_type,
            "plan":         ["MCTS-driven web scraping across platforms"],
            "answer":       result,
            "mcts_variant": "web-scraping-mcts",
        }

    # ------------------------------------------------------------------
    # Web scraping: MCTS-driven scraping with retry logic
    # ------------------------------------------------------------------
    if task_type == "scraper":
        url = extract_url(query)
        if url:
            result = scrape_and_summarize(url)
            return {
                "mode":         "Local LLM (Llama3.2 via Ollama) + MCTS Web Scraping",
                "task_type":    task_type,
                "plan":         ["MCTS-driven web scraping with retries"],
                "answer":       result,
                "mcts_variant": "web-scraping-mcts",
            }
        else:
            return {
                "mode":         "Local LLM (Llama3.2 via Ollama)",
                "task_type":    task_type,
                "plan":         ["Error"],
                "answer":       "❌ Please provide a valid URL to scrape. Example: 'scrape https://example.com'",
                "mcts_variant": None,
            }

    # ------------------------------------------------------------------
    # Email: Direct operation
    # ------------------------------------------------------------------
    if task_type == "mail":
        return {
            "mode":         "Local LLM (Llama3.2 via Ollama)",
            "task_type":    task_type,
            "plan":         ["Email Tool"],
            "answer":       "Please use the Email section in the extension to send or fetch emails.",
            "mcts_variant": None,
        }

    # ------------------------------------------------------------------
    # General queries: use selected MCTS variant for planning, then LLM
    # ------------------------------------------------------------------
    from mcts.variants import VARIANT_RUNNERS

    variant_key = mcts_variant.lower() if mcts_variant else "basic-mcts"
    if variant_key not in VARIANT_RUNNERS:
        variant_key = "basic-mcts"

    runner      = VARIANT_RUNNERS[variant_key]
    mcts_result = runner(query, simulations=simulations)
    plan_steps  = mcts_result.get("plan", [])

    llm = get_llm()
    final_answer = llm.invoke(f"""You are an autonomous AI agent.

Task: {query}

Execution Plan (generated by {mcts_result['variant']}):
{chr(10).join(f'  {i+1}. {step}' for i, step in enumerate(plan_steps))}

Execute this plan. Provide a detailed, accurate response based on your knowledge.
Be specific and practical in your answer.""")

    return {
        "mode":         f"Local LLM (Llama3.2 via Ollama) + {mcts_result['variant']}",
        "task_type":    task_type,
        "plan":         plan_steps,
        "answer":       final_answer,
        "mcts_variant": mcts_result["variant"],
        "mcts_score":   mcts_result.get("score"),
        "mcts_time_ms": mcts_result.get("time_ms"),
    }