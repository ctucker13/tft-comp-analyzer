from typing import Dict, Any, Optional
from enum import Enum
import os
import asyncio

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class LLMClient:
    def __init__(self, provider: LLMProvider, model: str):
        self.provider = provider
        self.model = model
        self.client = None
        
        # Initialize client based on provider
        try:
            if provider == LLMProvider.OPENAI:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key or api_key == "your_openai_key_here":
                    print("Warning: No valid OpenAI API key found, using mock responses")
                    self.client = None
                else:
                    self.client = OpenAI(api_key=api_key)
                    
            elif provider == LLMProvider.ANTHROPIC:
                from anthropic import Anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key or api_key == "your_anthropic_key_here":
                    print("Warning: No valid Anthropic API key found, using mock responses")
                    self.client = None
                else:
                    self.client = Anthropic(api_key=api_key)
        except ImportError as e:
            print(f"Error importing {provider.value} library: {e}")
            self.client = None
    
    def _is_mock_mode(self) -> bool:
        """Check if we should use mock responses"""
        return self.client is None
    
    def _generate_mock_response(self, messages: list) -> str:
        """Generate a mock response based on the conversation context"""
        last_message = messages[-1]["content"] if messages else ""
        
        if "extract" in last_message.lower() and "composition" in last_message.lower():
            return """
**TFT Composition Analysis (Mock Data)**

Based on the match data, here are the key compositions identified:

**Composition 1: Scrap-Challenger**
- Primary Traits: Scrap (4), Challenger (3)
- Key Carry: Jinx (4-cost)
- Supporting Units: Vi, Blitzcrank, Ezreal
- Average Placement: 3.2
- Items: Infinity Edge on Jinx, Warmog's on Vi

**Composition 2: Invoker Build**
- Primary Traits: Invoker (2), Bodyguard (2)  
- Key Carry: Viktor or similar mage
- Supporting Units: Various frontline
- Average Placement: 4.1
- Items: AP items on carry

**Performance Notes:**
- Scrap comps showed strong mid-game power
- Challenger trait provided good positioning flexibility
- Item quality heavily influenced final placement
            """
            
        elif "performance" in last_message.lower() and "pattern" in last_message.lower():
            return """
**Performance Pattern Analysis (Mock Data)**

**Highest Performing Compositions:**
1. **Scrap-Challenger** - Average placement: 3.2
   - 65% top-4 rate
   - Strong at levels 7-8
   - Flexible item requirements

2. **Invoker Builds** - Average placement: 4.1  
   - 55% top-4 rate
   - High-roll dependent
   - Strong late game scaling

**Key Performance Insights:**
- Compositions with 4+ cost carries averaged 1.3 better placement
- Trait diversity (3+ active traits) correlated with better performance
- Early game economy management was crucial for top placements

**Surprising Findings:**
- Traditional "meta" comps underperformed when contested
- Flexible builds with good items outperformed forced comps
- Positioning appeared more impactful than pure composition strength
            """
            
        elif "meta report" in last_message.lower() or "tier list" in last_message.lower():
            return """
**TFT Meta Report & Strategic Guide (Mock Analysis)**

## **TIER LIST**

**S-Tier (Consistent Top 4)**
- Scrap-Challenger Jinx
- Flex Invoker builds

**A-Tier (Strong with proper items)**  
- Bodyguard comps
- Trait-stacking builds

**B-Tier (Situational strength)**
- Off-meta combinations
- Economic builds

## **RECOMMENDATIONS BY SKILL LEVEL**

**Beginner Players:**
- Focus on Scrap builds (forgiving, consistent)
- Prioritize basic item combinations
- Don't force contested comps

**Intermediate Players:** 
- Learn flexible Invoker transitions
- Master positioning fundamentals
- Practice economic decision-making

**Advanced Players:**
- Experiment with off-meta synergies
- Perfect late-game positioning
- Master contested lobby navigation

## **EMERGING TRENDS**
- Item flexibility becoming more valuable than perfect comps
- Positioning micro-adjustments showing significant impact
- Economic builds viable in high-contest lobbies

## **SPECIFIC RECOMMENDATIONS**
- **Items:** Prioritize Infinity Edge, Warmog's, defensive items
- **Positioning:** Keep carries protected but within range
- **Economy:** Don't sacrifice too much HP for perfect items
            """
        else:
            return f"Mock response for: {last_message[:100]}..."
    
    async def generate(self, messages: list, **kwargs) -> str:
        """Generate response from LLM or return mock data"""
    
        print(f"DEBUG: LLM Client - Provider: {self.provider}")
        print(f"DEBUG: LLM Client - Model: {self.model}")
        print(f"DEBUG: LLM Client - Is mock mode: {self._is_mock_mode()}")
        print(f"DEBUG: LLM Client - Client exists: {self.client is not None}")
        
        # Use mock if no valid client
        if self._is_mock_mode():
            print("Using mock LLM response...")
            return self._generate_mock_response(messages)
        
        try:
            if self.provider == LLMProvider.OPENAI:
                # OpenAI doesn't have native async, so run in executor
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=kwargs.get("max_tokens", 1000),
                        temperature=kwargs.get("temperature", 0.7)
                    )
                )
                return response.choices[0].message.content or "No response generated"
            
            elif self.provider == LLMProvider.ANTHROPIC:
                print(f"Attempting Anthropic API call with model: {self.model}")
                # Extract system message and user messages for Anthropic format
                system_msg = None
                user_messages = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_msg = msg["content"]
                    else:
                        user_messages.append(msg)
                
                # Create message with proper format
                message_params = {
                    "model": self.model,
                    "max_tokens": kwargs.get("max_tokens", 1000),
                    "messages": user_messages
                }
                
                if system_msg:
                    message_params["system"] = system_msg
                
                response = self.client.messages.create(**message_params)
                return response.content[0].text if response.content else "No response generated"
            
        except Exception as e:
            print(f"Error generating response from {self.provider.value}: {e}")
            print("Falling back to mock response...")
            return self._generate_mock_response(messages)
        
        return "No response generated"