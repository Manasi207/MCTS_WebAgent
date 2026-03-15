# #backend/tools/ecommerce.py
# import requests
# from bs4 import BeautifulSoup
# import re
# from config import REQUEST_TIMEOUT, PRICE_RANGE_MIN, PRICE_RANGE_MAX, MCTS_SIMULATIONS
# from mcts.web_scraping_mcts import run_mcts_scraping

# def handle_ecommerce(query):
#     """MCTS with 10 simulations for e-commerce"""
#     try:
#         product_name = extract_product_name(query)
        
#         output = f"🔍 MCTS Price Comparison: {product_name.title()}\n{'='*70}\n\n"
#         output += f"🤖 Running {MCTS_SIMULATIONS} MCTS simulations...\n\n"
        
#         platforms = [
#             {'name': 'Amazon India', 'base_url': 'https://www.amazon.in', 'search_path': '/s?k=', 'priority': 1},
#             {'name': 'Flipkart', 'base_url': 'https://www.flipkart.com', 'search_path': '/search?q=', 'priority': 2},
#             {'name': 'Myntra', 'base_url': 'https://www.myntra.com', 'search_path': '/search?q=', 'priority': 3}
#         ]
        
#         output += f"🌳 Building MCTS tree...\n"
#         results, visited = run_mcts_scraping(platforms, product_name, MCTS_SIMULATIONS)
        
#         output += f"✅ Completed {MCTS_SIMULATIONS} simulations\n"
#         output += f"📊 Visited: {' → '.join(visited)}\n"
#         output += f"💰 Scraped: {len(results)}/{len(platforms)}\n\n{'='*70}\n\n"
        
#         if results:
#             return format_results(output, results)
#         return format_no_results(output, product_name)
#     except Exception as e:
#         return f"❌ Error: {str(e)}"

# def extract_product_name(query):
#     remove = ['compare', 'buy', 'find', 'search', 'best', 'price', 'cost', 'on', 'different', 'platforms', 'sites', 'check', 'over', 'across', 'various']
#     words = [w for w in query.lower().split() if w not in remove and len(w) > 2]
#     return ' '.join(words)

# def scrape_platform_real_time(platform, product_name):
#     """Scrape platform for price"""
#     search_query = product_name.replace(' ', '+')
#     url = platform['base_url'] + platform['search_path'] + search_query
    
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
#     try:
#         response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.text, 'html.parser')
#             return extract_price(soup, url)
#         return None
#     except:
#         return None

# def extract_price(soup, url):
#     """Extract price from page"""
#     text = soup.get_text()
#     patterns = [r'₹\s*([0-9,]+)', r'Rs\.?\s*([0-9,]+)']
    
#     for pattern in patterns:
#         for match in re.findall(pattern, text):
#             try:
#                 price = float(match.replace(',', ''))
#                 if PRICE_RANGE_MIN <= price <= PRICE_RANGE_MAX:
#                     return {'price': price, 'rating': 'N/A', 'url': url, 'currency': 'INR'}
#             except:
#                 continue
#     return None

# def format_results(output, results):
#     """Format successful results"""
#     output += f"💰 PRICES FOUND:\n{'-'*70}\n\n"
#     sorted_results = sorted(results.items(), key=lambda x: x[1]['price'])
    
#     for platform, data in sorted_results:
#         output += f"🛒 {platform}: ₹{data['price']:.0f}\n"
    
#     best = sorted_results[0]
#     output += f"\n{'='*70}\n✅ BEST DEAL: {best[0]} at ₹{best[1]['price']:.0f}\n"
#     return output

# def format_no_results(output, product_name):
#     """Format failure message"""
#     output += "❌ SCRAPING FAILED\n\n"
#     output += "Visit platforms:\n"
#     output += "  - Amazon: https://www.amazon.in\n"
#     output += "  - Flipkart: https://www.flipkart.com\n"
#     output += "  - Myntra: https://www.myntra.com\n"
#     return output
########################################################################################3

# backend/tools/ecommerce.py
import requests
from bs4 import BeautifulSoup
import re
from config import REQUEST_TIMEOUT, PRICE_RANGE_MIN, PRICE_RANGE_MAX, MCTS_SIMULATIONS
from mcts.web_scraping_mcts import run_mcts_scraping


def handle_ecommerce(query):
    """MCTS with simulations for e-commerce price comparison"""
    try:
        product_name = extract_product_name(query)

        output = f"🔍 MCTS Price Comparison: {product_name.title()}\n{'='*70}\n\n"
        output += f"🤖 Running {MCTS_SIMULATIONS} MCTS simulations...\n\n"

        platforms = [
            {'name': 'Amazon India', 'base_url': 'https://www.amazon.in',  'search_path': '/s?k=',      'priority': 1},
            {'name': 'Flipkart',     'base_url': 'https://www.flipkart.com','search_path': '/search?q=', 'priority': 2},
            {'name': 'Myntra',       'base_url': 'https://www.myntra.com',  'search_path': '/search?q=', 'priority': 3},
        ]

        output += "🌳 Building MCTS tree...\n"
        results, visited = run_mcts_scraping(platforms, product_name, MCTS_SIMULATIONS)

        output += f"✅ Completed {MCTS_SIMULATIONS} simulations\n"
        output += f"📊 Visited: {' → '.join(visited)}\n"
        output += f"💰 Scraped: {len(results)}/{len(platforms)}\n\n{'='*70}\n\n"

        if results:
            return format_results(output, results)
        return format_no_results(output, product_name)

    except Exception as e:
        return f"❌ Error: {str(e)}"


def extract_product_name(query):
    remove = [
        'compare', 'buy', 'find', 'search', 'best', 'price', 'cost',
        'on', 'different', 'platforms', 'sites', 'check', 'over', 'across', 'various',
    ]
    words = [w for w in query.lower().split() if w not in remove and len(w) > 2]
    return ' '.join(words)


def scrape_platform_real_time(platform, product_name):
    """Scrape a single platform for product price"""
    search_query = product_name.replace(' ', '+')
    url = platform['base_url'] + platform['search_path'] + search_query

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return extract_price(soup, url)
        return None
    except Exception:
        return None


def extract_price(soup, url):
    """Extract the first valid price from page text"""
    text = soup.get_text()
    patterns = [r'₹\s*([0-9,]+)', r'Rs\.?\s*([0-9,]+)']

    for pattern in patterns:
        for match in re.findall(pattern, text):
            try:
                price = float(match.replace(',', ''))
                if PRICE_RANGE_MIN <= price <= PRICE_RANGE_MAX:
                    return {'price': price, 'rating': 'N/A', 'url': url, 'currency': 'INR'}
            except Exception:
                continue
    return None


def format_results(output, results):
    """Format price comparison results sorted by price"""
    output += f"💰 PRICES FOUND:\n{'-'*70}\n\n"
    sorted_results = sorted(results.items(), key=lambda x: x[1]['price'])

    for platform, data in sorted_results:
        output += f"🛒 {platform}: ₹{data['price']:.0f}\n"

    best = sorted_results[0]
    output += f"\n{'='*70}\n✅ BEST DEAL: {best[0]} at ₹{best[1]['price']:.0f}\n"
    return output


def format_no_results(output, product_name):
    """Format failure/no-results message"""
    output += "❌ SCRAPING FAILED — No prices found\n\n"
    output += "Visit platforms manually:\n"
    output += "  • Amazon:   https://www.amazon.in\n"
    output += "  • Flipkart: https://www.flipkart.com\n"
    output += "  • Myntra:   https://www.myntra.com\n"
    return output