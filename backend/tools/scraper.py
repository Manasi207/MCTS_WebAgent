# backend/tools/scraper.py

import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, MAX_SCRAPE_CONTENT

def scrape_and_summarize(url):
    """Scrape actual web content and format it dynamically"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            element.decompose()
        
        # Build structured output dynamically
        result = f"📄 Scraped Content from: {url}\n{'='*60}\n\n"
        
        # Extract title
        title = soup.find('title')
        if title:
            result += f"📌 Title: {title.get_text().strip()}\n\n"
        
        # Extract main heading
        h1 = soup.find('h1')
        if h1:
            result += f"🔖 Main Heading: {h1.get_text().strip()}\n\n"
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            result += f"📝 Description: {meta_desc.get('content').strip()}\n\n"
        
        result += "📄 Content:\n" + "-"*60 + "\n\n"
        
        # Extract structured content with headings
        content_found = False
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
            heading_text = heading.get_text().strip()
            if not heading_text or len(heading_text) < 3:
                continue
                
            content_found = True
            level = heading.name
            
            # Format heading based on level
            if level == 'h1':
                result += f"\n{'#'*60}\n## {heading_text}\n{'#'*60}\n"
            elif level == 'h2':
                result += f"\n### {heading_text}\n{'-'*40}\n"
            elif level == 'h3':
                result += f"\n#### {heading_text}\n"
            else:
                result += f"\n##### {heading_text}\n"
            
            # Get content after heading
            next_elem = heading.find_next_sibling()
            para_count = 0
            while next_elem and para_count < 3:
                if next_elem.name == 'p':
                    para_text = next_elem.get_text().strip()
                    if para_text and len(para_text) > 20:
                        result += f"\n{para_text}\n"
                        para_count += 1
                elif next_elem.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                    break
                elif next_elem.name in ['ul', 'ol']:
                    items = next_elem.find_all('li')[:5]
                    for item in items:
                        text = item.get_text().strip()
                        if text:
                            result += f"  • {text}\n"
                    para_count += 1
                next_elem = next_elem.find_next_sibling()
        
        # If no structured content, get paragraphs
        if not content_found:
            result += "\n📝 Main Content:\n\n"
            paragraphs = soup.find_all('p')
            for i, p in enumerate(paragraphs[:20]):
                text = p.get_text().strip()
                if text and len(text) > 30:
                    result += f"{text}\n\n"
        
        # Extract lists
        lists = soup.find_all(['ul', 'ol'])
        if lists:
            result += f"\n\n📋 Lists Found ({len(lists)} total):\n{'-'*40}\n"
            for idx, lst in enumerate(lists[:3], 1):
                result += f"\nList {idx}:\n"
                items = lst.find_all('li')
                for item in items[:10]:
                    text = item.get_text().strip()
                    if text:
                        result += f"  • {text}\n"
        
        # Extract links
        links = soup.find_all('a', href=True)
        valid_links = []
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            if href and text and len(text) > 3 and len(text) < 100:
                if href.startswith('http') or href.startswith('/'):
                    valid_links.append((text, href))
        
        if valid_links:
            result += f"\n\n🔗 Links Found ({len(valid_links)} total):\n{'-'*40}\n"
            for i, (text, href) in enumerate(valid_links[:15], 1):
                result += f"{i}. {text}\n   URL: {href}\n"
        
        # Extract tables if any
        tables = soup.find_all('table')
        if tables:
            result += f"\n\n📊 Tables Found: {len(tables)}\n"
        
        # Limit total length
        if len(result) > MAX_SCRAPE_CONTENT:
            result = result[:MAX_SCRAPE_CONTENT] + f"\n\n... (content truncated at {MAX_SCRAPE_CONTENT} characters)"
        
        return result
    
    except requests.exceptions.Timeout:
        return f"❌ Timeout: Could not fetch {url} within {REQUEST_TIMEOUT} seconds"
    except requests.exceptions.ConnectionError:
        return f"❌ Connection Error: Could not connect to {url}"
    except requests.exceptions.HTTPError as e:
        return f"❌ HTTP Error {e.response.status_code}: {url}"
    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching {url}: {str(e)}"
    except Exception as e:
        return f"❌ Error processing content from {url}: {str(e)}"
