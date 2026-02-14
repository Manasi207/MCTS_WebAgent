#backend/mcts/planner.py
import random
import time
from config import MAX_MCTS_DEPTH, LLM_RATE_LIMIT_DELAY
from mcts.nodes import MonteCarloTreeSearchNode

# Rate limiting for operations
_last_operation = 0

def rate_limited_delay():
    """Apply rate limiting delay between operations"""
    global _last_operation
    
    elapsed = time.time() - _last_operation
    if elapsed < LLM_RATE_LIMIT_DELAY:
        time.sleep(LLM_RATE_LIMIT_DELAY - elapsed)
    
    _last_operation = time.time()

class PlanningState:

    def __init__(self, query, steps=None, depth=0):
        self.query = query
        self.steps = steps or []
        self.depth = depth

    def get_possible_actions(self):
        """Dynamic action selection based on query type and current context"""
        query_lower = self.query.lower()
        
        # E-commerce specific actions with more granular steps
        if any(word in query_lower for word in ['buy', 'purchase', 'shop', 'compare', 'product', 'price']):
            base_actions = ["Search Primary Platform", "Search Secondary Platform", "Extract Product Details", "Compare Prices"]
            
            # Add context-aware actions based on current steps
            if not self.steps:
                return ["Search Primary Platform", "Identify Product Category", "Plan Search Strategy"]
            elif "Search Primary Platform" in self.steps:
                return ["Search Secondary Platform", "Extract Product Details", "Verify Product Match"]
            elif len([s for s in self.steps if "Search" in s]) >= 2:
                return ["Extract Product Details", "Compare Prices", "Analyze Reviews", "Finalize Recommendation"]
            else:
                return ["Compare Prices", "Analyze Customer Reviews", "Check Availability", "Finalize Recommendation"]
        
        # Planning/booking specific actions
        elif any(word in query_lower for word in ['plan', 'book', 'schedule', 'trip', 'itinerary']):
            return ["Research Destinations", "Check Availability", "Compare Options", "Create Itinerary", "Finalize Plan"]
        
        # Data/analysis specific actions
        elif any(word in query_lower for word in ['analyze', 'data', 'research', 'study', 'compare']):
            return ["Gather Information", "Analyze Data", "Compare Alternatives", "Draw Conclusions", "Provide Recommendations"]
        
        # General actions for complex tasks
        return ["Research Topic", "Gather Information", "Analyze Options", "Organize Results", "Provide Recommendations"]

    def move(self, action):
        """Create new state with action"""
        # Apply rate limiting
        rate_limited_delay()
        
        return PlanningState(
            self.query,
            self.steps + [action],
            self.depth + 1
        )

    def is_terminal(self):
        """Check if planning should stop"""
        return self.depth >= MAX_MCTS_DEPTH

    def evaluate_with_llm(self):
        """Evaluate plan quality using enhanced heuristics"""
        score = 5.0  # Base score
        query_lower = self.query.lower()
        
        # Enhanced scoring for e-commerce queries
        if any(word in query_lower for word in ['buy', 'purchase', 'shop', 'compare']):
            for action in self.steps:
                if action in ["Search Primary Platform", "Search Secondary Platform"]:
                    score += 2.0  # High value for platform searches
                elif action in ["Extract Product Details", "Compare Prices"]:
                    score += 2.5  # Very high value for price comparison
                elif action in ["Analyze Reviews", "Analyze Customer Reviews"]:
                    score += 1.5  # Good value for review analysis
                elif action in ["Finalize Recommendation"]:
                    score += 2.0  # High value for final recommendation
            
            # Bonus for logical e-commerce flow
            if len(self.steps) >= 2:
                if "Search" in self.steps[0] and ("Compare" in str(self.steps) or "Extract" in str(self.steps)):
                    score += 2.0
            
            # Bonus for comprehensive comparison (multiple platforms)
            search_actions = [s for s in self.steps if "Search" in s]
            if len(search_actions) >= 2:
                score += 3.0  # Bonus for multi-platform search
        
        # Enhanced scoring for planning queries
        elif any(word in query_lower for word in ['plan', 'trip', 'schedule']):
            for action in self.steps:
                if action in ["Research Destinations", "Research Options"]:
                    score += 1.8
                elif action in ["Compare Options", "Create Itinerary"]:
                    score += 2.0
                elif action in ["Check Availability", "Finalize Plan"]:
                    score += 1.5
        
        # General scoring
        else:
            for action in self.steps:
                if action in ["Research Topic", "Gather Information"]:
                    score += 1.5
                elif action in ["Analyze Options", "Compare Alternatives"]:
                    score += 1.8
                elif action in ["Provide Recommendations"]:
                    score += 2.0
        
        # Penalty for redundant steps
        if len(self.steps) != len(set(self.steps)):
            score -= 3.0
        
        # Penalty for too many steps
        if len(self.steps) > 5:
            score -= 1.5
        
        # Bonus for logical flow patterns
        if self.steps:
            # Good starting actions
            if self.steps[0] in ["Search Primary Platform", "Research Topic", "Identify Product Category"]:
                score += 1.5
            
            # Good ending actions
            if self.steps[-1] in ["Finalize Recommendation", "Provide Recommendations", "Finalize Plan"]:
                score += 2.5
            
            # Good middle actions for e-commerce
            if len(self.steps) >= 3 and any("Compare" in step for step in self.steps[1:-1]):
                score += 1.5
        
        # Ensure score is in valid range
        return min(max(score, 1.0), 10.0)


class PlanningNode(MonteCarloTreeSearchNode):

    def untried_actions(self):
        """Get actions not yet tried"""
        tried = [child.state.steps[-1] for child in self.children if child.state.steps]
        available_actions = self.state.get_possible_actions()
        return [a for a in available_actions if a not in tried]

    def expand(self):
        """Expand node with new action"""
        untried = self.untried_actions()
        if not untried:
            return self
        
        # For e-commerce, prioritize search actions early
        if any(word in self.state.query.lower() for word in ['buy', 'compare', 'price']):
            search_actions = [a for a in untried if "Search" in a]
            if search_actions and self.state.depth < 2:
                action = random.choice(search_actions)
            else:
                action = random.choice(untried)
        else:
            action = random.choice(untried)
        
        next_state = self.state.move(action)
        child = PlanningNode(next_state, parent=self)
        self.children.append(child)
        return child

    def is_terminal_node(self):
        """Check if node is terminal"""
        return self.state.is_terminal()

    def rollout(self):
        """Simulate to terminal state and evaluate"""
        current_state = self.state

        while not current_state.is_terminal():
            possible_actions = current_state.get_possible_actions()
            
            # Smart action selection during rollout
            if any(word in current_state.query.lower() for word in ['buy', 'compare', 'price']):
                # For e-commerce, prefer search and compare actions
                preferred_actions = [a for a in possible_actions if any(word in a for word in ['Search', 'Compare', 'Extract', 'Analyze'])]
                if preferred_actions:
                    action = random.choice(preferred_actions)
                else:
                    action = random.choice(possible_actions)
            else:
                action = random.choice(possible_actions)
            
            current_state = current_state.move(action)

        return current_state.evaluate_with_llm()
