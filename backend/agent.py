# backend/agent.py
from llm import get_llm
from tools.ecommerce import handle_ecommerce
from tools.scraper import scrape_and_summarize
import re


def classify(query: str) -> str:
    """Route query to the correct handler."""
    q = query.lower()

    # ── E-commerce / price comparison ────────────────────────────
    # Single strong keywords
    ecommerce_single = [
        'buy', 'purchase', 'cheapest', 'lowest price', 'best deal',
        'price on amazon', 'price on flipkart', 'price on myntra',
        'shop for', 'check price', 'find price', 'discount on',
        'order online', 'add to cart', 'best buy', 'where to buy',
        'how much does', 'how much is', 'cost of', 'price of',
    ]
    if any(kw in q for kw in ecommerce_single):
        return "ecommerce"

    # Combo: any price word + any platform/comparison word
    price_words   = {'price','prices','cost','costs','rate','rates','cheap','cheaper',
                     'cheapest','affordable','deal','deals','offer','offers','discount',
                     'discounts','worth','expensive','inexpensive','budget'}
    platform_words= {'amazon','flipkart','myntra','croma','reliance','tatacliq','meesho',
                     'nykaa','platform','platforms','site','sites','store','stores',
                     'online','website','websites','shopping','ecommerce','market',
                     'marketplace','app','apps'}
    compare_words = {'compare','comparison','versus','vs','difference','check','find',
                     'show','list','search','best','top','which','where','across',
                     'multiple','various','different','all'}
    product_words = {'laptop','laptops','phone','mobile','mobiles','phones','tablet',
                     'tablets','watch','watches','camera','cameras','headphone',
                     'headphones','earphone','earphones','speaker','speakers',
                     'keyboard','mouse','monitor','tv','television','refrigerator',
                     'washing','machine','ac','cooler','fan','mixer','grinder',
                     'juicer','oven','microwave','iron','trimmer','shaver',
                     'printer','scanner','router','modem','purifier','heater',
                     'product','item','gadget','device','appliance','electronic'}

    q_words       = set(q.split())
    has_price     = bool(q_words & price_words)
    has_platform  = bool(q_words & platform_words)
    has_compare   = bool(q_words & compare_words)
    has_product   = bool(q_words & product_words)

    if has_price and has_platform:              return "ecommerce"
    if has_price and has_compare:               return "ecommerce"
    if has_product and has_platform:            return "ecommerce"
    if has_product and has_compare and has_price: return "ecommerce"
    if re.search(r'https?://', q) and has_price: return "ecommerce"

    # ── Scraper ───────────────────────────────────────────────────
    if any(w in q for w in ['scrape','extract','fetch data','get content from']):
        return "scraper"

    # ── Email ─────────────────────────────────────────────────────
    if any(w in q for w in ['email','send mail','compose email','latest mail']):
        return "mail"

    # ── Simple factual ────────────────────────────────────────────
    simple_kw = ['what is','who is','when is','where is','capital of',
                 'define ','explain ','tell me about','how many','what are']
    if any(kw in q for kw in simple_kw) and len(query.split()) < 15:
        return "simple"

    return "general"


def extract_url(query: str):
    m = re.search(r'https?://[^\s]+', query)
    return m.group(0) if m else None


def handle_query(query: str, mcts_variant: str = "basic-mcts", simulations: int = 5):
    """
    Main query handler.
    Ecommerce queries → real-time scraper (no LLM prices ever).
    General queries   → MCTS planning + LLM answer (INR context injected).
    """
    task_type = classify(query)

    # ── Simple ────────────────────────────────────────────────────
    if task_type == "simple":
        llm    = get_llm()
        answer = llm.invoke(f"Answer concisely and accurately: {query}")
        return {"mode":"Local LLM","task_type":task_type,
                "plan":["Direct LLM Response"],"answer":answer,
                "mcts_variant":None}

    # ── E-commerce → 3-tier real-time scraper (ZERO LLM prices) ──
    if task_type == "ecommerce":
        result = handle_ecommerce(query)
        return {"mode":"Real-Time Scraper (Amazon→Flipkart→Myntra→Official)",
                "task_type":task_type,
                "plan":["Direct: Amazon.in",
                        "Direct: Flipkart.com",
                        "Direct: Myntra.com",
                        "Fallback: Bing snippets if blocked"],
                "answer":result,
                "mcts_variant":"web-scraping-mcts"}

    # ── Web scraper ───────────────────────────────────────────────
    if task_type == "scraper":
        url = extract_url(query)
        if url:
            result = scrape_and_summarize(url)
            return {"mode":"MCTS Web Scraper","task_type":task_type,
                    "plan":["MCTS-driven web scraping"],
                    "answer":result,"mcts_variant":"web-scraping-mcts"}
        return {"mode":"Error","task_type":task_type,"plan":["Error"],
                "answer":"❌ Please provide a valid URL. Example: scrape https://example.com",
                "mcts_variant":None}

    # ── Email ─────────────────────────────────────────────────────
    if task_type == "mail":
        return {"mode":"Email Tool","task_type":task_type,
                "plan":["Email Tool"],
                "answer":"Please use the Email section in the extension.",
                "mcts_variant":None}

    # ── General: MCTS planning → LLM execution ───────────────────
    from mcts.variants import VARIANT_RUNNERS

    variant_key = (mcts_variant or "basic-mcts").lower()
    if variant_key not in VARIANT_RUNNERS:
        variant_key = "basic-mcts"

    # Speed caps — prevent long waits
    if   variant_key == "wm-mcts":  simulations = min(simulations, 3)
    elif variant_key == "rag-mcts": simulations = min(simulations, 4)
    else:                           simulations = min(simulations, 5)

    runner      = VARIANT_RUNNERS[variant_key]
    mcts_result = runner(query, simulations=simulations)
    plan_steps  = mcts_result.get("plan", [])

    llm = get_llm()
    final_answer = llm.invoke(f"""You are a helpful AI assistant.
Context: India. Use ₹ INR for any currency values.

Task: {query}

Execution Plan ({mcts_result['variant']}):
{chr(10).join(f'  {i+1}. {s}' for i,s in enumerate(plan_steps))}

Provide a clear, practical answer. Do not invent specific prices — if pricing
information is needed, direct the user to Amazon.in, Flipkart, or Smartprix.""")

    return {
        "mode":         f"LLM + {mcts_result['variant']}",
        "task_type":    task_type,
        "plan":         plan_steps,
        "answer":       final_answer,
        "mcts_variant": mcts_result["variant"],
        "mcts_score":   mcts_result.get("score"),
        "mcts_time_ms": mcts_result.get("time_ms"),
    }
# # #########################################################################################

# # backend/agent.py
# from llm import get_llm
# from tools.ecommerce import handle_ecommerce
# from tools.scraper import scrape_and_summarize
# import re


# def classify(query: str) -> str:
#     """Route query to the correct handler."""
#     q = query.lower()

#     # ── E-commerce / price comparison ────────────────────────────
#     # Single strong keywords
#     ecommerce_single = [
#         'buy', 'purchase', 'cheapest', 'lowest price', 'best deal',
#         'price on amazon', 'price on flipkart', 'price on myntra',
#         'shop for', 'check price', 'find price', 'discount on',
#         'order online', 'add to cart', 'best buy', 'where to buy',
#         'how much does', 'how much is', 'cost of', 'price of',
#     ]
#     if any(kw in q for kw in ecommerce_single):
#         return "ecommerce"

#     # Combo: any price word + any platform/comparison word
#     price_words   = {'price','prices','cost','costs','rate','rates','cheap','cheaper',
#                      'cheapest','affordable','deal','deals','offer','offers','discount',
#                      'discounts','worth','expensive','inexpensive','budget'}
#     platform_words= {'amazon','flipkart','myntra','croma','reliance','tatacliq','meesho',
#                      'nykaa','platform','platforms','site','sites','store','stores',
#                      'online','website','websites','shopping','ecommerce','market',
#                      'marketplace','app','apps'}
#     compare_words = {'compare','comparison','versus','vs','difference','check','find',
#                      'show','list','search','best','top','which','where','across',
#                      'multiple','various','different','all'}
#     product_words = {'laptop','laptops','phone','mobile','mobiles','phones','tablet',
#                      'tablets','watch','watches','camera','cameras','headphone',
#                      'headphones','earphone','earphones','speaker','speakers',
#                      'keyboard','mouse','monitor','tv','television','refrigerator',
#                      'washing','machine','ac','cooler','fan','mixer','grinder',
#                      'juicer','oven','microwave','iron','trimmer','shaver',
#                      'printer','scanner','router','modem','purifier','heater',
#                      'product','item','gadget','device','appliance','electronic'}

#     q_words       = set(q.split())
#     has_price     = bool(q_words & price_words)
#     has_platform  = bool(q_words & platform_words)
#     has_compare   = bool(q_words & compare_words)
#     has_product   = bool(q_words & product_words)

#     if has_price and has_platform:              return "ecommerce"
#     if has_price and has_compare:               return "ecommerce"
#     if has_product and has_platform:            return "ecommerce"
#     if has_product and has_compare and has_price: return "ecommerce"
#     if re.search(r'https?://', q) and has_price: return "ecommerce"

#     # ── Scraper ───────────────────────────────────────────────────
#     if any(w in q for w in ['scrape','extract','fetch data','get content from']):
#         return "scraper"

#     # ── Email ─────────────────────────────────────────────────────
#     if any(w in q for w in ['email','send mail','compose email','latest mail']):
#         return "mail"

#     # ── Simple factual ────────────────────────────────────────────
#     simple_kw = ['what is','who is','when is','where is','capital of',
#                  'define ','explain ','tell me about','how many','what are']
#     if any(kw in q for kw in simple_kw) and len(query.split()) < 15:
#         return "simple"

#     return "general"


# def extract_url(query: str):
#     m = re.search(r'https?://[^\s]+', query)
#     return m.group(0) if m else None


# def handle_query(query: str, mcts_variant: str = "basic-mcts", simulations: int = 5):
#     """
#     Main query handler.
#     Ecommerce queries → real-time scraper (no LLM prices ever).
#     General queries   → MCTS planning + LLM answer (INR context injected).
#     """
#     task_type = classify(query)

#     # ── Simple ────────────────────────────────────────────────────
#     if task_type == "simple":
#         llm    = get_llm()
#         answer = llm.invoke(f"Answer concisely and accurately: {query}")
#         return {"mode":"Local LLM","task_type":task_type,
#                 "plan":["Direct LLM Response"],"answer":answer,
#                 "mcts_variant":None}

#     # ── E-commerce → 3-tier real-time scraper (ZERO LLM prices) ──
#     if task_type == "ecommerce":
#         result = handle_ecommerce(query)
#         return {"mode":"3-Tier Real-Time Scraper (Smartprix→Direct→Bing)",
#                 "task_type":task_type,
#                 "plan":["Tier1: Price comparison sites",
#                         "Tier2: MCTS direct scraping",
#                         "Tier3: Search engine snippets"],
#                 "answer":result,
#                 "mcts_variant":"web-scraping-mcts"}

#     # ── Web scraper ───────────────────────────────────────────────
#     if task_type == "scraper":
#         url = extract_url(query)
#         if url:
#             result = scrape_and_summarize(url)
#             return {"mode":"MCTS Web Scraper","task_type":task_type,
#                     "plan":["MCTS-driven web scraping"],
#                     "answer":result,"mcts_variant":"web-scraping-mcts"}
#         return {"mode":"Error","task_type":task_type,"plan":["Error"],
#                 "answer":"❌ Please provide a valid URL. Example: scrape https://example.com",
#                 "mcts_variant":None}

#     # ── Email ─────────────────────────────────────────────────────
#     if task_type == "mail":
#         return {"mode":"Email Tool","task_type":task_type,
#                 "plan":["Email Tool"],
#                 "answer":"Please use the Email section in the extension.",
#                 "mcts_variant":None}

#     # ── General: MCTS planning → LLM execution ───────────────────
#     from mcts.variants import VARIANT_RUNNERS

#     variant_key = (mcts_variant or "basic-mcts").lower()
#     if variant_key not in VARIANT_RUNNERS:
#         variant_key = "basic-mcts"

#     # Speed caps — prevent long waits
#     if   variant_key == "wm-mcts":  simulations = min(simulations, 3)
#     elif variant_key == "rag-mcts": simulations = min(simulations, 4)
#     else:                           simulations = min(simulations, 5)

#     runner      = VARIANT_RUNNERS[variant_key]
#     mcts_result = runner(query, simulations=simulations)
#     plan_steps  = mcts_result.get("plan", [])

#     llm = get_llm()
#     final_answer = llm.invoke(f"""You are a helpful AI assistant.
# Context: India. Use ₹ INR for any currency values.

# Task: {query}

# Execution Plan ({mcts_result['variant']}):
# {chr(10).join(f'  {i+1}. {s}' for i,s in enumerate(plan_steps))}

# Provide a clear, practical answer. Do not invent specific prices — if pricing
# information is needed, direct the user to Amazon.in, Flipkart, or Smartprix.""")

#     return {
#         "mode":         f"LLM + {mcts_result['variant']}",
#         "task_type":    task_type,
#         "plan":         plan_steps,
#         "answer":       final_answer,
#         "mcts_variant": mcts_result["variant"],
#         "mcts_score":   mcts_result.get("score"),
#         "mcts_time_ms": mcts_result.get("time_ms"),
#     }