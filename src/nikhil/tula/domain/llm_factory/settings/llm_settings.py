# src/nikhil/amsha/toolkit/llm_factory/settings/llm_settings.py

from typing import Dict, Optional

from pydantic import BaseModel

from nikhil.tula.domain.llm_factory.domain.models import LLMUseCaseConfig, LLMParameters, LLMModelConfig


class LLMSettings(BaseModel):
    llm: Dict[str, LLMUseCaseConfig]  # creative, evaluation, etc.
    llm_parameters: Dict[str, LLMParameters]

    def get_model_config(self, use_case: str, model_key: Optional[str] = None) -> LLMModelConfig:
        use_case_config = self.llm.get(use_case)
        if not use_case_config:
            raise ValueError(f"Use case '{use_case}' not found.")

        selected_model_key = model_key or use_case_config.default
        model_config = use_case_config.models.get(selected_model_key)

        if not model_config:
            raise ValueError(f"Model '{selected_model_key}' not found in use case '{use_case}'.")

        return model_config

    def get_parameters(self, use_case: str) -> LLMParameters:
        return self.llm_parameters.get(use_case, LLMParameters())
