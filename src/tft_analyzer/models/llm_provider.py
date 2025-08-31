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
        """Initialize the LLM client with proper error handling and validation"""
        print(f"🔧 Initializing {self.provider} client...")
        
        try:
            # Use string comparison to avoid enum instance issues
            if self.provider.value == "anthropic":
                print("  ✅ Entered Anthropic initialization branch")
                
                if not self._is_valid_api_key(self.api_key, "sk-ant-"):
                    print("  ❌ Invalid Anthropic API key format")
                    self.client = None
                    return
                
                print("  📦 Importing anthropic...")
                from anthropic import Anthropic
                print("  ✅ Import successful")
                
                print("  🔨 Creating client...")
                self.client = Anthropic(api_key=self.api_key)
                print("  ✅ Anthropic client created successfully!")
                
            elif self.provider.value == "openai":
                print("  ✅ Entered OpenAI initialization branch")
                
                if not self._is_valid_api_key(self.api_key, "sk-"):
                    print("  ❌ Invalid OpenAI API key format")
                    self.client = None
                    return
                
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                print("  ✅ OpenAI client created successfully!")
                
            else:
                print(f"  ⚠️ Unknown provider: {self.provider.value}")
                self.client = None
                
        except ImportError as e:
            print(f"  ❌ Import failed: {e}")
            print(f"  Install with: pip install {self.provider.value}")
            self.client = None
        except Exception as e:
            print(f"  ❌ Client creation failed: {e}")
            print(f"  Error type: {type(e).__name__}")
            self.client = None
    
    def _is_valid_api_key(self, api_key: str, expected_prefix: str) -> bool:
        """Validate API key format and content with debugging"""
        print(f"  🔍 Validating API key...")
        print(f"    Key exists: {bool(api_key)}")
        
        if not api_key:
            print("    ❌ No API key provided")
            return False
        
        print(f"    Key length: {len(api_key)}")
        print(f"    Expected prefix: {expected_prefix}")
        print(f"    Key starts with prefix: {api_key.startswith(expected_prefix)}")
        
        # Check for placeholder values
        placeholder_indicators = [
            "your_openai_key_here",
            "your_anthropic_key_here", 
            "sk-...",
            "your_api_key_here",
            ""
        ]
        
        is_placeholder = api_key in placeholder_indicators
        print(f"    Is placeholder: {is_placeholder}")
        
        if is_placeholder:
            print("    ❌ API key is a placeholder")
            return False
        
        # Check expected prefix
        if not api_key.startswith(expected_prefix):
            print(f"    ❌ API key doesn't start with expected prefix {expected_prefix}")
            return False
        
        # Check minimum length (real keys are much longer)
        if len(api_key) < 20:
            print(f"    ❌ API key too short (< 20 characters)")
            return False
        
        print("    ✅ API key validation passed")
        return True
    
    def _is_mock_mode(self) -> bool:
        """Check if we should use mock responses"""
        is_mock = (
            self.client is None or 
            not self.api_key or
            not self._is_valid_api_key(
                self.api_key, 
                "sk-ant-" if self.provider.value == "anthropic" else "sk-"
            )
        )
        
        return is_mock
    
    def _generate_mock_response(self, messages: list) -> str:
        """Generate a mock response based on the conversation context"""
        if not messages:
            return "Mock response: No messages provided"
        
        last_message = messages[-1]["content"] if messages else ""
        
        if "extract" in last_message.lower() and "composition" in last_message.lower():
            return """**TFT Composition Analysis (Mock Data)**

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
- Item quality heavily influenced final placement"""
            
        elif "performance" in last_message.lower() and "pattern" in last_message.lower():
            return """**Performance Pattern Analysis (Mock Data)**

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
- Positioning appeared more impactful than pure composition strength"""
            
        elif "meta report" in last_message.lower() or "tier list" in last_message.lower():
            return """**TFT Meta Report & Strategic Guide (Mock Analysis)**

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

**SPECIFIC RECOMMENDATIONS**
- **Items:** Prioritize Infinity Edge, Warmog's, defensive items
- **Positioning:** Keep carries protected but within range
- **Economy:** Don't sacrifice too much HP for perfect items"""
        else:
            return f"Mock TFT analysis response for: {last_message[:100]}..."
    
    async def generate(self, messages: list, **kwargs) -> str:
        """Generate response from LLM or return mock data"""
        
        print(f"DEBUG: LLM Client - Provider: {self.provider}")
        print(f"DEBUG: LLM Client - Model: {self.model}")
        print(f"DEBUG: LLM Client - Is mock mode: {self._is_mock_mode()}")
        print(f"DEBUG: LLM Client - Client exists: {self.client is not None}")
        print(f"DEBUG: LLM Client - API key present: {bool(self.api_key)}")
        if self.api_key:
            print(f"DEBUG: LLM Client - API key prefix: {self.api_key[:12]}...")
        
        # Use mock if no valid client
        if self._is_mock_mode():
            print("Using mock LLM response...")
            return self._generate_mock_response(messages)
        
        try:
            # Use string comparison for provider check
            if self.provider.value == "openai":
                print("Calling OpenAI API...")
                # OpenAI doesn't have native async, so run in executor
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=kwargs.get("max_tokens", 2000),
                        temperature=kwargs.get("temperature", 0.7)
                    )
                )
                result = response.choices[0].message.content or "No response generated"
                print(f"✓ Got OpenAI response ({len(result)} characters)")
                print(f"Response preview: {result[:200]}...")
                return result
            
            elif self.provider.value == "anthropic":
                print(f"Calling Anthropic API with model: {self.model}")
                
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
                
                print(f"  Making API call with {len(user_messages)} messages...")
                response = self.client.messages.create(**message_params)
                
                if response.content and len(response.content) > 0:
                    result = response.content[0].text
                    print(f"✓ Got Anthropic response ({len(result)} characters)")
                    print(f"Response preview: {result[:200]}...")
                    return result
                else:
                    print("❌ No content in Anthropic response")
                    return "No content received from Anthropic API"
            
            else:
                print(f"❌ Unsupported provider: {self.provider.value}")
                return "Unsupported provider"
            
        except Exception as e:
            print(f"❌ Error generating response from {self.provider.value}: {e}")
            print(f"Error type: {type(e).__name__}")
            print("Falling back to mock response...")
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