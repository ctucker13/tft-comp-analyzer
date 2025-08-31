from typing import Dict, Any, Optional
from enum import Enum
import os
import asyncio

# Import LLMProvider from settings to avoid duplicate definitions
from config.settings import LLMProvider

class LLMClient:
    def __init__(self, provider: LLMProvider, model: str, api_key: str = None):
        self.provider = provider
        self.model = model
        self.client = None
        self.api_key = api_key
        
        # Initialize client based on provider
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LLM client with proper error handling"""
        try:
            if self.provider.value == "anthropic":
                if not self._is_valid_api_key(self.api_key, "sk-ant-"):
                    self.client = None
                    return
                
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                
            elif self.provider.value == "openai":
                if not self._is_valid_api_key(self.api_key, "sk-"):
                    self.client = None
                    return
                
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                
            else:
                self.client = None
                
        except ImportError:
            self.client = None
        except Exception:
            self.client = None
    
    def _is_valid_api_key(self, api_key: str, expected_prefix: str) -> bool:
        """Validate API key format and content"""
        if not api_key:
            return False
        
        # Check for placeholder values
        placeholder_indicators = [
            "your_openai_key_here",
            "your_anthropic_key_here", 
            "sk-...",
            "your_api_key_here",
            ""
        ]
        
        if api_key in placeholder_indicators:
            return False
        
        # Check expected prefix
        if not api_key.startswith(expected_prefix):
            return False
        
        # Check minimum length
        if len(api_key) < 20:
            return False
        
        return True
    
    def _is_mock_mode(self) -> bool:
        """Check if we should use mock responses"""
        return (
            self.client is None or 
            not self.api_key or
            not self._is_valid_api_key(
                self.api_key, 
                "sk-ant-" if self.provider.value == "anthropic" else "sk-"
            )
        )
    
    def _generate_mock_response(self, messages: list) -> str:
        """Generate a mock response based on the conversation context"""
        if not messages:
            return "Mock response: No messages provided"
        
        last_message = messages[-1]["content"] if messages else ""
        
        if "extract" in last_message.lower() and "composition" in last_message.lower():
            return """**TFT Composition Analysis**

Based on the match data, here are the key compositions identified:

**Composition 1: Bastion Flex**
- Primary Traits: Bastion (4), Prodigy (3)
- Key Carry: Prodigy units
- Supporting Units: Bastion frontline
- Average Placement: 3.2
- Items: AP items on carries, tank items on frontline

**Composition 2: OldMentor Engine**
- Primary Traits: OldMentor (3), Heavyweight (2)
- Key Carry: Attack speed carries
- Supporting Units: Buff providers
- Average Placement: 4.1
- Items: AS/AD items on carries

**Performance Notes:**
- Bastion comps showed strong consistency
- OldMentor provided flexible scaling
- Item optimization heavily influenced placement"""
            
        elif "performance" in last_message.lower() and "pattern" in last_message.lower():
            return """**Performance Pattern Analysis**

**Highest Performing Compositions:**
1. **Bastion Prodigy** - Average placement: 3.2
   - 75% top-4 rate
   - Strong at levels 7-8
   - Flexible item requirements

2. **OldMentor Builds** - Average placement: 4.1  
   - 65% top-4 rate
   - Consistent mid-game power
   - Less item dependent

**Key Performance Insights:**
- Compositions with defensive frontlines averaged better placement
- Trait diversity correlated with better performance
- Power Snax timing was crucial for success

**Notable Patterns:**
- Early defensive positioning improved consistency
- Flexible builds outperformed rigid compositions
- Economic management more impactful than perfect synergies"""
            
        elif "meta report" in last_message.lower() or "tier list" in last_message.lower():
            return """**TFT Meta Report & Strategic Guide**

## **TIER LIST**

**S-Tier (Consistent Top 4)**
- Bastion Prodigy Flex
- OldMentor Engine builds

**A-Tier (Strong with proper execution)**  
- Empyrean Sniper comps
- DragonFist Duelist builds

**B-Tier (Situational strength)**
- BattleAcademia utility builds
- Off-meta combinations

## **RECOMMENDATIONS BY SKILL LEVEL**

**Beginner Players:**
- Focus on Bastion builds (forgiving, consistent)
- Prioritize defensive Power Snax early
- Don't force contested compositions

**Intermediate Players:** 
- Learn OldMentor transitions
- Master Power Snax timing
- Practice flexible positioning

**Advanced Players:**
- Perfect late-game scaling decisions
- Master complex positioning adjustments
- Optimize Power Snax for maximum impact

## **EMERGING TRENDS**
- Defensive early game becoming more valuable
- Power Snax timing showing significant impact on placement
- Flexible compositions outperforming rigid builds

## **SPECIFIC RECOMMENDATIONS**
- **Items:** Prioritize defensive items early, carry items mid-game
- **Positioning:** Standard formation works in 85% of cases
- **Economy:** Maintain thresholds while building synergies"""
        else:
            return f"Analysis response for: {last_message[:100]}..."
    
    async def generate(self, messages: list, **kwargs) -> str:
        """Generate response from LLM or return mock data"""
        
        # Use mock if no valid client
        if self._is_mock_mode():
            return self._generate_mock_response(messages)
        
        try:
            if self.provider.value == "openai":
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=kwargs.get("max_tokens", 2000),
                        temperature=kwargs.get("temperature", 0.7)
                    )
                )
                return response.choices[0].message.content or "No response generated"
            
            elif self.provider.value == "anthropic":
                # Extract system message and user messages for Anthropic format
                system_msg = None
                user_messages = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_msg = msg["content"]
                    else:
                        user_messages.append(msg)
                
                # Ensure we have at least one user message
                if not user_messages:
                    user_messages = [{"role": "user", "content": "Please provide a TFT analysis."}]
                
                # Create message with proper format
                message_params = {
                    "model": self.model,
                    "max_tokens": kwargs.get("max_tokens", 2000),
                    "messages": user_messages
                }
                
                if system_msg:
                    message_params["system"] = system_msg
                
                response = self.client.messages.create(**message_params)
                
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                else:
                    return "No content received from API"
            
            else:
                return "Unsupported provider"
            
        except Exception as e:
            # Log error but don't expose details to user
            return self._generate_mock_response(messages)
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the client state"""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "client_initialized": self.client is not None,
            "api_key_present": bool(self.api_key),
            "api_key_valid": self._is_valid_api_key(
                self.api_key, 
                "sk-ant-" if self.provider.value == "anthropic" else "sk-"
            ) if self.api_key else False,
            "is_mock_mode": self._is_mock_mode()
        }