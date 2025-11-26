"""
Direct LLM client using LiteLLM for unified interface

Supports 100+ LLM providers through LiteLLM:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Google (Gemini, PaLM)
- Anthropic (Claude)
- Local models via LM Studio, Ollama
- Azure OpenAI
- And many more...

Configuration is done via model name prefix (e.g., "openai/gpt-4", "gemini/gemini-pro")
"""

from typing import List, Dict, Any, Optional
from litellm import completion
import os


class DirectLLMClient:
    """
    Direct LLM API client using LiteLLM
    
    LiteLLM provides a unified interface for 100+ LLM providers.
    No need for provider-specific packages - just configure the model name.
    """
    
    def __init__(self, 
                 model: str, 
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 **kwargs):
        """
        Initialize LLM client with LiteLLM
        
        Args:
            model: Model name - for LM Studio use "openai/model-name"
            api_key: API key (LM Studio doesn't need real key)
            base_url: Base URL (e.g., "http://localhost:1234/v1" for LM Studio)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.params = kwargs
        
        print(f"[LLM] Initializing LLM client:")
        print(f"   Model: {model}")
        print(f"   Base URL: {base_url or 'default'}")
        print(f"   API Key: {'Set' if api_key else 'Not set'}")
        
        # Set API key in environment if provided
        if api_key:
            self._set_api_key_for_provider(model, api_key)
    
    def _set_api_key_for_provider(self, model: str, api_key: str):
        """Set API key in environment for the provider"""
        model_lower = model.lower()
        
        # LiteLLM uses standard environment variables
        if 'gpt' in model_lower or 'openai' in model_lower:
            os.environ['OPENAI_API_KEY'] = api_key
        elif 'gemini' in model_lower or 'palm' in model_lower:
            os.environ['GEMINI_API_KEY'] = api_key
        elif 'claude' in model_lower or 'anthropic' in model_lower:
            os.environ['ANTHROPIC_API_KEY'] = api_key
        # For other providers, LiteLLM will handle it via api_key parameter
    
    def call(self, messages: List[Dict[str, str]]) -> str:
        """
        Make LLM API call using LiteLLM
        
        IMPORTANT: This makes a REAL API call - no simulation!
        Any errors will be raised immediately with clear messages.
        """
        # Prepare completion parameters
        completion_params = {
            'model': self.model,
            'messages': messages,
            'temperature': self.params.get('temperature', 0.0),
            'max_tokens': self.params.get('max_completion_tokens', 4096),
            'top_p': self.params.get('top_p', 1.0),
        }
        
        # Add API key if provided
        if self.api_key:
            completion_params['api_key'] = self.api_key
        
        # Add base_url for LM Studio/custom endpoints
        if self.base_url:
            completion_params['base_url'] = self.base_url
        
        # Add optional parameters
        if 'presence_penalty' in self.params:
            completion_params['presence_penalty'] = self.params['presence_penalty']
        if 'frequency_penalty' in self.params:
            completion_params['frequency_penalty'] = self.params['frequency_penalty']
        
        print(f"\n[LLM] Calling LLM: {self.model}")
        if self.base_url:
            print(f"   Endpoint: {self.base_url}")
        print(f"   Message length: {len(str(messages))} chars")
        
        try:
            # REAL API CALL - NO SIMULATION
            response = completion(**completion_params)
            
            result = response.choices[0].message.content
            print(f"   [OK] Response received: {len(result)} chars")
            
            return result
            
        except Exception as e:
            # CLEAR ERROR MESSAGE
            error_msg = f"""
[ERROR] LLM API CALL FAILED

Model: {self.model}
Base URL: {self.base_url or 'default'}
Error: {str(e)}

Possible causes:
1. LM Studio not running (if using local model)
2. Wrong base_url or port number
3. Model not loaded in LM Studio
4. Network/connection issue
5. Invalid API key (for cloud providers)

Check:
- Is LM Studio running? (http://localhost:1234)
- Is the correct model loaded?
- Is the base_url correct in config?
"""
            print(error_msg)
            raise RuntimeError(error_msg) from e
    
    def call_stream(self, messages: List[Dict[str, str]]):
        """
        Make streaming LLM API call
        
        Args:
            messages: List of message dicts
        
        Yields:
            Chunks of response text
        
        Example:
            for chunk in client.call_stream(messages):
                print(chunk, end='', flush=True)
        """
        completion_params = {
            'model': self.model,
            'messages': messages,
            'temperature': self.params.get('temperature', 0.0),
            'max_tokens': self.params.get('max_completion_tokens', 4096),
            'top_p': self.params.get('top_p', 1.0),
            'stream': True  # Enable streaming
        }
        
        if self.api_key:
            completion_params['api_key'] = self.api_key
        if self.base_url:
            completion_params['base_url'] = self.base_url
        
        try:
            response = completion(**completion_params)
            
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                        
        except Exception as e:
            raise RuntimeError(f"Streaming LLM API call failed: {e}")
