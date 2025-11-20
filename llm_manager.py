"""
LLM Manager Module
Handles interaction with local Ollama models
"""

import logging
import ollama
from typing import List, Dict

logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self, model_name="llama3.2:3b", host="http://localhost:11434"):
        """
        Initialize LLM manager with Ollama
        
        Args:
            model_name: Ollama model name (e.g., 'llama3.2:3b', 'mistral', 'phi3')
            host: Ollama server host
        """
        self.model_name = model_name
        self.host = host
        logger.info(f"Initializing LLM with model: {model_name}")
        
        # Test connection
        try:
            self._test_connection()
            logger.info("✓ Successfully connected to Ollama")
        except Exception as e:
            logger.error(f"✗ Failed to connect to Ollama: {e}")
            logger.error("Make sure Ollama is running: 'ollama serve'")
            raise
    
    def _test_connection(self):
        """Test Ollama connection"""
        try:
            # List available models
            models = ollama.list()
            logger.info(f"Available models: {[m['name'] for m in models.get('models', [])]}")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Ollama at {self.host}") from e
    
    def generate_rag_response(self, query: str, context_chunks: List[Dict], 
                             conversation_history: List[Dict] = None) -> str:
        """
        Generate response using RAG (Retrieval-Augmented Generation)
        
        Args:
            query: User's question
            context_chunks: Retrieved relevant documents
            conversation_history: Previous conversation messages
            
        Returns:
            Generated response string
        """
        # Build context from retrieved chunks
        context_text = "\n\n".join([
            f"Document: {chunk['metadata'].get('title', 'Unknown')}\n{chunk['text']}"
            for chunk in context_chunks
        ])
        
        # Build the prompt
        system_prompt = """You are a helpful AI assistant. Answer questions based on the provided context. 
If the context doesn't contain relevant information, say so clearly. Be concise and accurate."""
        
        user_prompt = f"""Context from knowledge base:
{context_text}

Question: {query}

Please provide a clear and concise answer based on the context above."""
        
        # Add conversation history if available
        messages = []
        if conversation_history:
            messages.extend(conversation_history[-4:])  # Last 2 turns
        
        messages.append({
            'role': 'user',
            'content': user_prompt
        })
        
        try:
            # Generate response using Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                }
            )
            
            return response['message']['content']
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error while generating a response. Please try again."
    
    def generate_simple_response(self, prompt: str) -> str:
        """
        Generate a simple response without RAG context
        
        Args:
            prompt: User's prompt
            
        Returns:
            Generated response string
        """
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.7}
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I encountered an error. Please try again."
    
    def summarize_conversation(self, conversation_history: List[Dict]) -> str:
        """
        Summarize conversation history
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            Summary string
        """
        if not conversation_history:
            return "No conversation history to summarize."
        
        # Build conversation text
        conv_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history
        ])
        
        prompt = f"""Please provide a brief 2-3 sentence summary of this conversation:

{conv_text}

Summary:"""
        
        return self.generate_simple_response(prompt)