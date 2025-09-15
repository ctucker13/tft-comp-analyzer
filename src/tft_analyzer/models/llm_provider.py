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
        
        # More flexible prefix checking for different API key formats
        if expected_prefix == "sk-ant-":
            # Anthropic keys can have different formats: sk-ant-* or sk-ant-api*
            if not (api_key.startswith("sk-ant-") or api_key.startswith("sk-ant-api")):
                return False
        elif expected_prefix == "sk-":
            # OpenAI keys: sk-* or sk-proj-*
            if not (api_key.startswith("sk-") or api_key.startswith("sk-proj-")):
                return False
        else:
            # Default exact prefix matching
            if not api_key.startswith(expected_prefix):
                return False
        
        # Check minimum length
        if len(api_key) < 20:
            return False
        
        return True
    
    def _is_mock_mode(self) -> bool:
        """Check if we should use mock responses - DISABLED for production"""
        # Force real API usage only - require valid keys
        if (self.client is None or 
            not self.api_key or
            not self._is_valid_api_key(
                self.api_key, 
                "sk-ant-" if self.provider.value == "anthropic" else "sk-"
            )):
            # More detailed error message
            if not self.api_key:
                raise ValueError(f"❌ No {self.provider.value} API key provided. Please set the API key in your .env file.")
            elif self.client is None:
                raise ValueError(f"❌ Failed to initialize {self.provider.value} client. Please check your API key format.")
            else:
                raise ValueError(f"❌ Invalid {self.provider.value} API key format. Please check your .env file.")
        return False
    
    def _generate_mock_response(self, messages: list) -> str:
        """Generate a mock response - DISABLED in production"""
        raise ValueError("❌ Mock responses disabled. Real API key required for all analysis.")
    
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