"""
Agent Manager - Intelligent Query Router
Decides which model/tool to use based on query intent
"""

import logging
import re
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """Query intent classification"""
    KNOWLEDGE_SEARCH = "knowledge_search"  # RAG needed
    SIMPLE_GREETING = "simple_greeting"    # No model needed
    IMAGE_ANALYSIS = "image_analysis"      # Vision model
    SUMMARIZATION = "summarization"        # LLM only
    CONVERSATION = "conversation"          # LLM with history
    CALCULATION = "calculation"            # Can use Python eval
    UNKNOWN = "unknown"

class AgentManager:
    """
    Intelligent agent that routes queries to appropriate tools/models
    """
    
    def __init__(self):
        """Initialize the agent with routing rules"""
        self.intent_patterns = {
            QueryIntent.SIMPLE_GREETING: [
                r'^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))',
                r'^(thank you|thanks|thx)',
                r'^(bye|goodbye|see you)',
            ],
            QueryIntent.KNOWLEDGE_SEARCH: [
                r'(what is|what are|explain|describe|tell me about)',
                r'(how does|how to|how can)',
                r'(why is|why does|why do)',
                r'(define|definition of)',
                r'(benefits of|advantages of|disadvantages of)',
                r'(compare|difference between|vs)',
            ],
            QueryIntent.SUMMARIZATION: [
                r'(summarize|summary|recap|overview)',
                r'(in short|briefly|tldr)',
            ],
            QueryIntent.CALCULATION: [
                r'(calculate|compute|solve)',
                r'(\d+[\+\-\*/]\d+)',  # Math expressions
            ],
        }
        
        logger.info("Agent Manager initialized")
    
    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify the user's query intent
        
        Args:
            query: User's question/command
            
        Returns:
            QueryIntent enum
        """
        query_lower = query.lower().strip()
        
        # Check each pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    logger.info(f"Classified intent: {intent.value}")
                    return intent
        
        # Default to knowledge search for questions
        if '?' in query or len(query.split()) > 2:
            return QueryIntent.KNOWLEDGE_SEARCH
        
        return QueryIntent.UNKNOWN
    
    def should_use_rag(self, query: str, intent: Optional[QueryIntent] = None) -> bool:
        """
        Decide if RAG (vector search) is needed
        
        Args:
            query: User's question
            intent: Pre-classified intent (optional)
            
        Returns:
            True if RAG should be used
        """
        if intent is None:
            intent = self.classify_intent(query)
        
        # RAG is needed for knowledge searches
        if intent == QueryIntent.KNOWLEDGE_SEARCH:
            return True
        
        # Don't use RAG for greetings, simple conversations
        if intent in [QueryIntent.SIMPLE_GREETING, QueryIntent.CALCULATION]:
            return False
        
        # For unknown intents, use RAG as fallback
        return intent == QueryIntent.UNKNOWN
    
    def should_use_llm(self, query: str, intent: Optional[QueryIntent] = None) -> bool:
        """
        Decide if LLM is needed
        
        Args:
            query: User's question
            intent: Pre-classified intent (optional)
            
        Returns:
            True if LLM should be used
        """
        if intent is None:
            intent = self.classify_intent(query)
        
        # Simple greetings don't need LLM
        if intent == QueryIntent.SIMPLE_GREETING:
            return False
        
        # Calculations might not need LLM
        if intent == QueryIntent.CALCULATION:
            return False  # Can use Python eval
        
        # Everything else needs LLM
        return True
    
    def get_simple_response(self, query: str, intent: QueryIntent) -> Optional[str]:
        """
        Generate simple response without using models
        
        Args:
            query: User's question
            intent: Classified intent
            
        Returns:
            Response string or None if model is needed
        """
        query_lower = query.lower().strip()
        
        # Greetings
        if intent == QueryIntent.SIMPLE_GREETING:
            if any(word in query_lower for word in ['hi', 'hello', 'hey', 'good']):
                return "👋 Hello! How can I help you today? Try `/ask <question>` or send me an image!"
            
            if any(word in query_lower for word in ['thank', 'thanks', 'thx']):
                return "😊 You're welcome! Let me know if you need anything else."
            
            if any(word in query_lower for word in ['bye', 'goodbye', 'see you']):
                return "👋 Goodbye! Come back anytime you need help!"
        
        # Calculations (simple math)
        if intent == QueryIntent.CALCULATION:
            try:
                # Extract math expression
                match = re.search(r'(\d+[\+\-\*/]\d+)', query)
                if match:
                    expr = match.group(1)
                    result = eval(expr)  # Safe for simple math
                    return f"🔢 {expr} = {result}"
            except:
                pass
        
        return None
    
    def create_execution_plan(self, query: str, has_image: bool = False) -> Dict:
        """
        Create an execution plan for the query
        
        Args:
            query: User's question
            has_image: Whether user sent an image
            
        Returns:
            Execution plan dictionary
        """
        # CRITICAL: Images should NEVER go through agent routing
        # They are handled directly by vision_manager in bot_agentic.py
        # This method should not be called for images, but adding safety check
        if has_image:
            logger.warning("create_execution_plan called with image - should be handled directly!")
            return {
                'intent': 'image_analysis',
                'use_rag': False,
                'use_llm': False,
                'use_vision': True,
                'simple_response': None,
                'steps': [
                    {
                        'action': 'analyze_image',
                        'tool': 'vision_model',
                        'reason': 'Image analysis (should not reach here)'
                    }
                ]
            }
        
        # Classify intent for text queries only
        intent = self.classify_intent(query)
        
        # Check if simple response is possible
        simple_response = self.get_simple_response(query, intent)
        
        plan = {
            'intent': intent.value,
            'use_rag': self.should_use_rag(query, intent),
            'use_llm': self.should_use_llm(query, intent),
            'use_vision': has_image,
            'simple_response': simple_response,
            'steps': []
        }
        
        # Build execution steps
        if simple_response:
            plan['steps'].append({
                'action': 'return_simple_response',
                'tool': 'template',
                'reason': 'Query can be answered with template'
            })
        else:
            if has_image:
                plan['steps'].append({
                    'action': 'analyze_image',
                    'tool': 'vision_model',
                    'reason': 'Image analysis requested'
                })
            
            if plan['use_rag']:
                plan['steps'].append({
                    'action': 'search_knowledge_base',
                    'tool': 'vector_store',
                    'reason': 'Knowledge retrieval needed'
                })
            
            if plan['use_llm']:
                plan['steps'].append({
                    'action': 'generate_response',
                    'tool': 'ollama_llm',
                    'reason': 'Natural language generation needed'
                })
        
        logger.info(f"Execution plan: {plan}")
        return plan
    
    def estimate_cost(self, plan: Dict) -> Dict[str, float]:
        """
        Estimate computational cost of execution plan
        
        Args:
            plan: Execution plan
            
        Returns:
            Cost estimates (in relative units)
        """
        costs = {
            'time_seconds': 0.0,
            'memory_mb': 0.0,
            'compute_units': 0.0
        }
        
        for step in plan['steps']:
            tool = step['tool']
            
            if tool == 'template':
                costs['time_seconds'] += 0.001
                costs['compute_units'] += 0.1
            
            elif tool == 'vector_store':
                costs['time_seconds'] += 0.05
                costs['memory_mb'] += 50
                costs['compute_units'] += 1.0
            
            elif tool == 'ollama_llm':
                costs['time_seconds'] += 3.0
                costs['memory_mb'] += 2000
                costs['compute_units'] += 10.0
            
            elif tool == 'vision_model':
                costs['time_seconds'] += 2.0
                costs['memory_mb'] += 1000
                costs['compute_units'] += 8.0
        
        return costs
    
    def optimize_plan(self, plan: Dict) -> Dict:
        """
        Optimize execution plan to reduce cost
        
        Args:
            plan: Original execution plan
            
        Returns:
            Optimized plan
        """
        # If we have a simple response, skip everything else
        if plan['simple_response']:
            plan['use_rag'] = False
            plan['use_llm'] = False
        
        # If query is very short and not a question, skip RAG
        if not any(c in plan['intent'] for c in ['?', 'what', 'how', 'why']):
            if len(plan['intent'].split()) < 3:
                plan['use_rag'] = False
        
        return plan
    
    def explain_plan(self, plan: Dict) -> str:
        """
        Generate human-readable explanation of plan
        
        Args:
            plan: Execution plan
            
        Returns:
            Explanation string
        """
        lines = [f"**Query Intent:** {plan['intent'].replace('_', ' ').title()}"]
        
        if plan['simple_response']:
            lines.append("**Strategy:** Template response (fastest)")
        else:
            steps_text = []
            for step in plan['steps']:
                steps_text.append(f"• {step['action'].replace('_', ' ').title()} using {step['tool']}")
            
            lines.append("**Execution Steps:**")
            lines.extend(steps_text)
        
        costs = self.estimate_cost(plan)
        lines.append(f"\n**Estimated Time:** {costs['time_seconds']:.1f}s")
        
        return "\n".join(lines)


class AgenticQueryProcessor:
    """
    Processes queries using the agent's execution plan
    """
    
    def __init__(self, vector_store, llm_manager, vision_manager):
        """
        Initialize with model managers
        
        Args:
            vector_store: VectorStore instance
            llm_manager: LLMManager instance
            vision_manager: VisionManager instance
        """
        self.agent = AgentManager()
        self.vector_store = vector_store
        self.llm_manager = llm_manager
        self.vision_manager = vision_manager
        
        logger.info("Agentic Query Processor initialized")
    
    def process_query(self, query: str, conversation_history: List[Dict] = None,
                     image_bytes: bytes = None, explain_plan: bool = False) -> Dict:
        """
        Process query using agentic approach
        
        Args:
            query: User's question
            conversation_history: Previous messages
            image_bytes: Image data (if any)
            explain_plan: Whether to include plan explanation
            
        Returns:
            Response dictionary with answer and metadata
        """
        # Create execution plan
        plan = self.agent.create_execution_plan(query, has_image=image_bytes is not None)
        plan = self.agent.optimize_plan(plan)
        
        response = {
            'answer': '',
            'sources': [],
            'plan': plan if explain_plan else None,
            'plan_explanation': self.agent.explain_plan(plan) if explain_plan else None
        }
        
        # Execute plan
        if plan['simple_response']:
            # Fast path: return template response
            response['answer'] = plan['simple_response']
            logger.info("Used simple response (no models)")
            return response  # Early return for simple responses
        
        # Execute each step
        context_chunks = []
        
        for step in plan['steps']:
            if step['action'] == 'search_knowledge_base':
                # Retrieve relevant documents
                context_chunks = self.vector_store.search(query, k=3)
                response['sources'] = [c['source'] for c in context_chunks]
                logger.info(f"Retrieved {len(context_chunks)} documents")
            
            elif step['action'] == 'generate_response':
                # Generate with LLM
                if context_chunks:
                    # Use RAG
                    answer = self.llm_manager.generate_rag_response(
                        query, context_chunks, conversation_history
                    )
                else:
                    # Simple generation
                    answer = self.llm_manager.generate_simple_response(query)
                
                response['answer'] = answer
                logger.info("Generated LLM response")
            
            elif step['action'] == 'analyze_image':
                # Analyze image
                description = self.vision_manager.analyze_image(image_bytes)
                response['answer'] = description
                logger.info("Analyzed image")
        
        # Safety check - ensure answer exists
        if not response['answer']:
            response['answer'] = "I couldn't generate a response. Please try again."
            logger.warning("No answer generated, using fallback")
        
        return response