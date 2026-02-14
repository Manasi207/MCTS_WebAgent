#backend/agent.py
from llm import get_llm
from config import MCTS_SIMULATIONS
from mcts.planner import PlanningState, PlanningNode
from mcts.search import MonteCarloTreeSearch
from tools.ecommerce import handle_ecommerce
from tools.scraper import scrape_and_summarize
from tools.mail import send_email, fetch_unread_emails
import re

def classify(query: str):
    """Dynamically classify query type using keywords"""
    query_lower = query.lower()
    
    # E-commerce tasks (uses MCTS)
    if any(word in query_lower for word in ['buy', 'purchase', 'shop', 'compare', 'product', 'price']):
        return "ecommerce"
    
    # Web scraping tasks (no MCTS - direct)
    if any(word in query_lower for word in ['scrape', 'extract', 'fetch data', 'get content from']):
        return "scraper"
    
    # Email tasks (no MCTS - direct)
    if any(word in query_lower for word in ['email', 'send mail', 'compose email', 'latest mail']):
        return "mail"
    
    # Simple factual questions (no MCTS - direct)
    simple_keywords = ['what', 'who', 'when', 'where', 'capital', 'define', 'explain', 'tell me', 'how many']
    if any(keyword in query_lower for keyword in simple_keywords) and len(query.split()) < 15:
        return "simple"
    
    # General complex tasks (uses MCTS)
    return "general"

def extract_url(query: str):
    """Extract URL from query"""
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, query)
    return match.group(0) if match else None

def run_mcts(query):
    """Run MCTS planning with rate limiting"""
    root_state = PlanningState(query)
    root_node = PlanningNode(root_state)
    mcts = MonteCarloTreeSearch(root_node)
    best_node = mcts.best_action(MCTS_SIMULATIONS)
    return best_node.state.steps

def handle_query(query: str):
    """Main query handler - routes to appropriate task handler"""
    
    task_type = classify(query)

    # Simple queries: Direct LLM (no MCTS)
    if task_type == "simple":
        llm = get_llm()
        final_answer = llm.invoke(f"Answer this question concisely and accurately: {query}")
        return {
            "mode": "Local LLM (Phi-3 via Ollama)",
            "task_type": task_type,
            "plan": ["Direct Answer"],
            "answer": final_answer
        }

    # E-commerce: MCTS planning + web search + LLM analysis
    if task_type == "ecommerce":
        plan = run_mcts(query)
        result = handle_ecommerce(query)
        return {
            "mode": "Local LLM (Phi-3 via Ollama)",
            "task_type": task_type,
            "plan": plan,
            "answer": result
        }

    # Web scraping: Direct scraping (no MCTS, no LLM summary)
    if task_type == "scraper":
        url = extract_url(query)
        if url:
            result = scrape_and_summarize(url)
            return {
                "mode": "Local LLM (Phi-3 via Ollama)",
                "task_type": task_type,
                "plan": ["Extract URL", "Fetch Content", "Format Data"],
                "answer": result
            }
        else:
            return {
                "mode": "Local LLM (Phi-3 via Ollama)",
                "task_type": task_type,
                "plan": ["Error"],
                "answer": "❌ Please provide a valid URL to scrape. Example: 'scrape https://example.com'"
            }

    # Email: Direct operation (no MCTS)
    if task_type == "mail":
        return {
            "mode": "Local LLM (Phi-3 via Ollama)",
            "task_type": task_type,
            "plan": ["Email Tool"],
            "answer": "Please use the Email section in the extension to send or fetch emails."
        }

    # General complex tasks: MCTS planning + LLM execution
    plan = run_mcts(query)
    llm = get_llm()

    final_answer = llm.invoke(f"""You are an autonomous AI agent.

Task: {query}
Plan: {plan}

Execute this task following the plan. Provide a detailed, accurate response based on your knowledge.
Be specific and practical in your answer.""")

    return {
        "mode": "Local LLM (Phi-3 via Ollama)",
        "task_type": task_type,
        "plan": plan,
        "answer": final_answer
    }
