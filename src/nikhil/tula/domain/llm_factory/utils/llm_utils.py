# src/nikhil/tula/domain/llm_factory/utils/llm_utils.py

import os


class LLMUtils:
    
    @staticmethod
    def disable_telemetry():
        """Disable LLM telemetry"""
        # LiteLLM doesn't have telemetry by default
        # Set environment variable to be sure
        os.environ['LITELLM_TELEMETRY'] = '0'
    
    @staticmethod
    def extract_model_name(model_string: str) -> str:
        """
        Extract a clean model name from the full path
        
        Args:
            model_string: Full model path (e.g., "gemini/gemini-1.5-flash")
        
        Returns:
            Clean model name (e.g., "gemini-1.5-flash")
        """
        prefixes = ["lm_studio/", "gemini/", "open_ai/", "openai/", "azure/", "ollama/"]
        for prefix in prefixes:
            if model_string.startswith(prefix):
                return model_string[len(prefix):]
        return model_string
