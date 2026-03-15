#backend/mcts/web_scraping_mcts.py
"""True MCTS implementation with 10 simulations for web scraping"""

import random
import time
from mcts.nodes import MonteCarloTreeSearchNode
from mcts.search import MonteCarloTreeSearch
from config import WEB_REQUEST_DELAY

class WebScrapingState:
    """State for MCTS web scraping"""
    
    def __init__(self, platforms, product_name, scraped_results=None, visited=None, depth=0):
        self.platforms = platforms
        self.product_name = product_name
        self.scraped_results = scraped_results or {}
        self.visited = visited or []
        self.depth = depth
        self.max_depth = len(platforms)
    
    def get_possible_actions(self):
        """Get unvisited platforms"""
        return [p for p in self.platforms if p['name'] not in self.visited]
    
    def execute_action(self, platform):
        """Execute scraping and return new state"""
        from tools.ecommerce import scrape_platform_real_time
        
        time.sleep(WEB_REQUEST_DELAY)
        new_results = self.scraped_results.copy()
        
        try:
            price_data = scrape_platform_real_time(platform, self.product_name)
            if price_data and price_data.get('price'):
                new_results[platform['name']] = price_data
        except:
            pass
        
        return WebScrapingState(
            self.platforms,
            self.product_name,
            new_results,
            self.visited + [platform['name']],
            self.depth + 1
        )
    
    def is_terminal(self):
        return len(self.visited) >= len(self.platforms)
    
    def evaluate(self):
        """Evaluate scraping quality"""
        score = len(self.scraped_results) * 5.0
        
        if len(self.scraped_results) == len(self.platforms):
            score += 10.0
        
        if len(self.scraped_results) >= 2:
            score += 5.0
        
        failed = len(self.visited) - len(self.scraped_results)
        score -= failed * 1.0
        
        return max(score, 0.1)


class WebScrapingNode(MonteCarloTreeSearchNode):
    """MCTS node for web scraping"""
    
    def untried_actions(self):
        tried = [child.state.visited[-1] for child in self.children if child.state.visited]
        available = self.state.get_possible_actions()
        return [p for p in available if p['name'] not in tried]
    
    def expand(self):
        untried = self.untried_actions()
        if not untried:
            return self
        
        platform = min(untried, key=lambda p: p.get('priority', 999))
        next_state = self.state.execute_action(platform)
        child = WebScrapingNode(next_state, parent=self)
        self.children.append(child)
        return child
    
    def is_terminal_node(self):
        return self.state.is_terminal()
    
    def rollout(self):
        current_state = self.state
        
        while not current_state.is_terminal():
            possible = current_state.get_possible_actions()
            if not possible:
                break
            action = min(possible, key=lambda p: p.get('priority', 999))
            current_state = current_state.execute_action(action)
        
        return current_state.evaluate()


# def run_mcts_scraping(platforms, product_name, simulations=5):
#     """Run MCTS and execute full scraping on all platforms"""
    
#     # Run MCTS simulations to find best strategy
#     initial_state = WebScrapingState(platforms, product_name)
#     root_node = WebScrapingNode(initial_state)
#     mcts = MonteCarloTreeSearch(root_node)
    
#     # Run simulations
#     best_node = mcts.best_action(simulations)
    
#     # Now execute actual scraping on ALL platforms in priority order
#     # (MCTS helped us determine the best order)
#     final_results = {}
#     visited_order = []
    
#     # Sort platforms by priority (MCTS-informed decision)
#     sorted_platforms = sorted(platforms, key=lambda p: p.get('priority', 999))
    
#     from tools.ecommerce import scrape_platform_real_time
#     import time
#     from config import WEB_REQUEST_DELAY
    
#     for platform in sorted_platforms:
#         visited_order.append(platform['name'])
#         time.sleep(WEB_REQUEST_DELAY)
        
#         try:
#             price_data = scrape_platform_real_time(platform, product_name)
#             if price_data and price_data.get('price'):
#                 final_results[platform['name']] = price_data
#         except:
#             pass
    
#     return final_results, visited_order
def run_mcts_scraping(platforms, product_name, simulations=5):

    initial_state = WebScrapingState(platforms, product_name)

    root_node = WebScrapingNode(initial_state)

    mcts = MonteCarloTreeSearch(root_node)

    best_node = mcts.best_action(simulations)

    final_results = {}
    visited_order = []

    sorted_platforms = sorted(platforms, key=lambda p: p.get('priority', 999))

    from tools.ecommerce import scrape_platform_real_time
    import time
    from config import WEB_REQUEST_DELAY

    for platform in sorted_platforms:

        visited_order.append(platform['name'])

        time.sleep(WEB_REQUEST_DELAY)

        try:

            price_data = scrape_platform_real_time(platform, product_name)

            if price_data and price_data.get('price'):

                final_results[platform['name']] = price_data

        except:
            pass

    return final_results, visited_order