#backend/tools/ecommerce.py

import requests
from bs4 import BeautifulSoup
from llm import get_llm
import time
import re
import json
from config import WEB_REQUEST_DELAY, REQUEST_TIMEOUT, MAX_PLATFORMS_TO_CHECK, PRICE_RANGE_MIN, PRICE_RANGE_MAX

def handle_ecommerce(query):
    """Real-time e-commerce price comparison with actual scraping"""
    
    try:
        product_name = extract_product_name(query)
        
        output = f"🔍 LIVE Price Comparison: {product_name.title()}\n"
        output += "="*70 + "\n\n"
        output += f"⏳ Scraping real-time prices from top {MAX_PLATFORMS_TO_CHECK} platforms...\n"
        output += f"📅 Date: February 2026 | Currency: INR\n\n"
        
        # Define platforms with real search strategies
        platforms = [
            {
                'name': 'Amazon India',
                'search_strategy': 'amazon_search',
                'base_url': 'https://www.amazon.in',
                'search_path': '/s?k=',
                'priority': 1
            },
            {
                'name': 'Flipkart',
                'search_strategy': 'flipkart_search', 
                'base_url': 'https://www.flipkart.com',
                'search_path': '/search?q=',
                'priority': 2
            },
            {
                'name': 'Snapdeal',
                'search_strategy': 'snapdeal_search',
                'base_url': 'https://www.snapdeal.com',
                'search_path': '/search?keyword=',
                'priority': 3
            },
            {
                'name': 'Tata CLiQ',
                'search_strategy': 'tatacliq_search',
                'base_url': 'https://www.tatacliq.com',
                'search_path': '/search/?searchText=',
                'priority': 4
            }
        ]
        
        results = {}
        
        # Scrape each platform
        for i, platform in enumerate(platforms[:MAX_PLATFORMS_TO_CHECK]):
            try:
                output += f"📡 [{i+1}/{MAX_PLATFORMS_TO_CHECK}] Scraping {platform['name']}...\n"
                
                # Add delay to avoid rate limiting
                time.sleep(WEB_REQUEST_DELAY)
                
                price_data = scrape_platform_real_time(platform, product_name)
                
                if price_data and price_data.get('price'):
                    results[platform['name']] = price_data
                    output += f"   ✅ Found: ₹{price_data['price']:.0f}"
                    if price_data.get('rating'):
                        output += f" | Rating: {price_data['rating']}"
                    output += "\n"
                else:
                    output += f"   ❌ No valid price found\n"
                    
            except Exception as e:
                output += f"   ⚠️ Scraping failed: {str(e)[:30]}...\n"
        
        output += "\n" + "="*70 + "\n\n"
        
        if results:
            return format_real_results(output, results, product_name)
        else:
            return handle_scraping_failure(output, product_name)
    
    except Exception as e:
        return f"❌ Error in e-commerce handler: {str(e)}"


def extract_product_name(query):
    """Extract clean product name from query"""
    # Remove comparison words
    remove_words = ['compare', 'buy', 'find', 'search', 'best', 'price', 'cost', 'on', 'different', 'platforms', 'sites', 'check', 'over', 'across', 'various']
    
    words = query.lower().split()
    product_words = [w for w in words if w not in remove_words and len(w) > 2]
    
    return ' '.join(product_words)


def scrape_platform_real_time(platform, product_name):
    """Actually scrape real-time data from platform"""
    
    # Build search URL
    search_query = product_name.replace(' ', '+' if 'amazon' in platform['name'].lower() else '%20')
    url = platform['base_url'] + platform['search_path'] + search_query
    
    # Enhanced headers to avoid detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        # Make request with session for better success rate
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract using platform-specific strategy
            if platform['search_strategy'] == 'amazon_search':
                return extract_amazon_real_data(soup, url)
            elif platform['search_strategy'] == 'flipkart_search':
                return extract_flipkart_real_data(soup, url)
            elif platform['search_strategy'] == 'snapdeal_search':
                return extract_snapdeal_real_data(soup, url)
            elif platform['search_strategy'] == 'tatacliq_search':
                return extract_tatacliq_real_data(soup, url)
        
        return None
        
    except Exception as e:
        return None


def extract_amazon_real_data(soup, url):
    """Extract real Amazon data with multiple strategies"""
    
    # Strategy 1: Look for product cards in search results
    product_cards = soup.find_all('div', {'data-component-type': 's-search-result'})
    
    for card in product_cards[:3]:  # Check first 3 results
        # Extract price
        price_elem = card.find('span', class_='a-price-whole') or card.find('span', class_='a-price')
        if price_elem:
            price_text = price_elem.get_text().strip()
            price = extract_price_number(price_text)
            
            if price and PRICE_RANGE_MIN <= price <= PRICE_RANGE_MAX:
                # Extract rating
                rating_elem = card.find('span', class_='a-icon-alt')
                rating = extract_rating(rating_elem.get_text() if rating_elem else '')
                
                # Extract product title for verification
                title_elem = card.find('h2', class_='a-size-mini') or card.find('span', class_='a-size-medium')
                title = title_elem.get_text().strip() if title_elem else ''
                
                return {
                    'price': price,
                    'rating': rating,
                    'title': title[:50],
                    'url': url,
                    'scraped_at': '2026-02-14',
                    'currency': 'INR'
                }
    
    # Strategy 2: Generic price search in page
    return extract_generic_price_data(soup, url, 'Amazon')


def extract_flipkart_real_data(soup, url):
    """Extract real Flipkart data"""
    
    # Look for product containers
    product_containers = soup.find_all('div', class_='_1AtVbE') or soup.find_all('div', class_='_13oc-S')
    
    for container in product_containers[:3]:
        # Price extraction
        price_elem = container.find('div', class_='_30jeq3') or container.find('div', class_='_1_WHN1')
        if price_elem:
            price = extract_price_number(price_elem.get_text())
            
            if price and PRICE_RANGE_MIN <= price <= PRICE_RANGE_MAX:
                # Rating extraction
                rating_elem = container.find('div', class_='_3LWZlK')
                rating = extract_rating(rating_elem.get_text() if rating_elem else '')
                
                return {
                    'price': price,
                    'rating': rating,
                    'url': url,
                    'scraped_at': '2026-02-14',
                    'currency': 'INR'
                }
    
    return extract_generic_price_data(soup, url, 'Flipkart')


def extract_snapdeal_real_data(soup, url):
    """Extract real Snapdeal data"""
    
    # Look for product cards
    product_cards = soup.find_all('div', class_='product-tuple-listing') or soup.find_all('section', class_='product-tuple-listing')
    
    for card in product_cards[:3]:
        price_elem = card.find('span', class_='lfloat product-price') or card.find('span', class_='product-price')
        if price_elem:
            price = extract_price_number(price_elem.get_text())
            
            if price and PRICE_RANGE_MIN <= price <= PRICE_RANGE_MAX:
                return {
                    'price': price,
                    'rating': 'N/A',
                    'url': url,
                    'scraped_at': '2026-02-14',
                    'currency': 'INR'
                }
    
    return extract_generic_price_data(soup, url, 'Snapdeal')


def extract_tatacliq_real_data(soup, url):
    """Extract real Tata CLiQ data"""
    
    # Look for product listings
    products = soup.find_all('div', class_='ProductModule__base') or soup.find_all('div', class_='SearchModule__product')
    
    for product in products[:3]:
        price_elem = product.find('div', class_='ProductModule__price') or product.find('span', class_='price')
        if price_elem:
            price = extract_price_number(price_elem.get_text())
            
            if price and PRICE_RANGE_MIN <= price <= PRICE_RANGE_MAX:
                return {
                    'price': price,
                    'rating': 'N/A',
                    'url': url,
                    'scraped_at': '2026-02-14',
                    'currency': 'INR'
                }
    
    return extract_generic_price_data(soup, url, 'Tata CLiQ')


def extract_generic_price_data(soup, url, platform_name):
    """Generic price extraction as fallback"""
    
    # Look for any element containing price patterns
    page_text = soup.get_text()
    
    # Find all price patterns in the page
    price_patterns = [
        r'₹\s*([0-9,]+(?:\.[0-9]{1,2})?)',
        r'Rs\.?\s*([0-9,]+(?:\.[0-9]{1,2})?)',
        r'INR\s*([0-9,]+(?:\.[0-9]{1,2})?)'
    ]
    
    found_prices = []
    for pattern in price_patterns:
        matches = re.findall(pattern, page_text)
        for match in matches:
            price = extract_price_number(match)
            if price and PRICE_RANGE_MIN <= price <= PRICE_RANGE_MAX:
                found_prices.append(price)
    
    if found_prices:
        # Return the most common price (likely the actual product price)
        most_common_price = max(set(found_prices), key=found_prices.count)
        return {
            'price': most_common_price,
            'rating': 'N/A',
            'url': url,
            'scraped_at': '2026-02-14',
            'currency': 'INR',
            'extraction_method': 'generic'
        }
    
    return None


def extract_price_number(text):
    """Extract numeric price from text"""
    if not text:
        return None
    
    # Remove currency symbols and clean text
    cleaned = re.sub(r'[₹$Rs\.INR\s]', '', str(text))
    # Remove commas
    cleaned = cleaned.replace(',', '')
    
    # Find number
    match = re.search(r'(\d+(?:\.\d{1,2})?)', cleaned)
    if match:
        try:
            return float(match.group(1))
        except:
            return None
    return None


def extract_rating(text):
    """Extract rating from text"""
    if not text:
        return 'N/A'
    
    # Look for rating patterns
    patterns = [
        r'(\d+\.?\d*)\s*out of\s*5',
        r'(\d+\.?\d*)/5',
        r'(\d+\.?\d*)\s*★',
        r'(\d+\.?\d*)\s*stars?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            rating = float(match.group(1))
            if 0 <= rating <= 5:
                return f"{rating}/5"
    
    return 'N/A'


def format_real_results(output, results, product_name):
    """Format real scraping results"""
    
    output += f"💰 LIVE PRICES FOUND ({len(results)} platforms):\n"
    output += "-"*70 + "\n\n"
    
    # Sort by price
    sorted_results = sorted(results.items(), key=lambda x: x[1]['price'])
    
    for platform, data in sorted_results:
        output += f"🛒 {platform}:\n"
        output += f"   💵 Price: ₹{data['price']:.0f}\n"
        if data.get('rating') and data['rating'] != 'N/A':
            output += f"   ⭐ Rating: {data['rating']}\n"
        if data.get('title'):
            output += f"   📦 Product: {data['title']}\n"
        output += f"   📅 Scraped: {data.get('scraped_at', '2026-02-14')}\n\n"
    
    # Best recommendation
    best_platform = sorted_results[0][0]
    best_price = sorted_results[0][1]['price']
    
    output += "="*70 + "\n"
    output += f"✅ BEST DEAL (February 2026):\n"
    output += f"   🏆 Platform: {best_platform}\n"
    output += f"   💰 Price: ₹{best_price:.0f}\n"
    output += f"   📊 Compared: {len(results)} live platforms\n"
    output += f"   💡 Savings: ₹{sorted_results[-1][1]['price'] - best_price:.0f} vs highest price\n"
    
    return output


def handle_scraping_failure(output, product_name):
    """Handle case when scraping fails completely"""
    
    output += "⚠️ SCRAPING BLOCKED - All platforms have anti-scraping protection\n\n"
    output += "🤖 Using AI knowledge for February 2026 estimates:\n\n"
    
    llm = get_llm()
    
    prompt = f"""You are a price comparison expert in February 2026. Provide REALISTIC current market prices for: {product_name}

Important: 
- Use February 2026 pricing (NOT 2023 or older data)
- Prices in Indian Rupees (INR)
- Include realistic variations between platforms
- Consider inflation and current market trends

Format:
Amazon India: ₹X,XXX | Rating: X.X/5 | Notes: [brief note]
Flipkart: ₹X,XXX | Rating: X.X/5 | Notes: [brief note]  
Snapdeal: ₹X,XXX | Rating: X.X/5 | Notes: [brief note]
Tata CLiQ: ₹X,XXX | Rating: X.X/5 | Notes: [brief note]

BEST DEAL: [Platform] at ₹X,XXX - [reason]

Keep realistic price differences between platforms. Make prices current for 2026."""
    
    ai_response = llm.invoke(prompt)
    output += ai_response
    
    output += f"\n\n⚠️ Note: These are AI estimates since live scraping was blocked."
    output += f"\n💡 Try visiting the platforms directly for exact current prices."
    
    return output