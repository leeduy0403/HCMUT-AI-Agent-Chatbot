from typing import List, Dict, Any, Optional
from datetime import datetime

class RAGResponseFormatter:
    @staticmethod
    def format_prompt(
        user_input: str,
        retrieved_context: str,
        chat_history: str,
        system_prompts: Dict[str, str],
        max_context_length: int = 2000
    ) -> str:
        """
        Format the RAG prompt with context management and prompt engineering
        """
        # Truncate context if too long while preserving meaning
        if len(retrieved_context) > max_context_length:
            retrieved_context = retrieved_context[:max_context_length] + "..."
            
        # Structure the prompt
        prompt = f"""
        # Role
        {system_prompts.get('ROLE', '')}

        # Skills
        {system_prompts.get('SKILLS', '')}

        # Tone
        {system_prompts.get('TONE', '')}

        # Tasks
        {system_prompts.get('TASKS', '')}

        # Examples
        {system_prompts.get('EXAMPLES', '')}

        # Constraints
        {system_prompts.get('CONSTRAINTS', '')}

        # Important Information
        {system_prompts.get('IMPORTANT_INFORMATION', '')}


        # Context from Knowledge Base:
        {retrieved_context}

        # Previous Conversation:
        {chat_history}

        # Current Question:
        {user_input}

        # Instructions:
        1. Use ONLY the provided context to answer the question
        2. If the context doesn't contain relevant information, admit that you don't know
        3. Format the answer clearly with bullet points when appropriate
        4. Be concise but thorough
        5. Match the language of the question (Vietnamese/English)
        6. Keep numerical values and specific details exactly as found in the context
        
        Answer:
        """
        
        return prompt.strip()
        
    @staticmethod
    def format_sources(matches: List[Dict[str, Any]]) -> str:
        """
        Format source citations for retrieved contexts
        """
        if not matches:
            return ""
            
        sources = []
        for match in matches:
            metadata = match['metadata']
            source = metadata.get('source', 'Unknown')
            score = match.get('score', 0)
            sources.append(f"- {source} (relevance: {score:.2f})")
            
        return "\n".join(sources)