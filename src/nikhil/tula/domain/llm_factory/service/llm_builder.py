# src/nikhil/amsha/toolkit/llm_factory/dependency/llm_builder.py

from nikhil.tula.domain.llm_factory.domain.llm_type import LLMType
from nikhil.tula.domain.llm_factory.domain.models import LLMBuildResult
from nikhil.tula.domain.llm_factory.settings.llm_settings import LLMSettings
from nikhil.tula.domain.llm_factory.utils.llm_utils import LLMUtils
from nikhil.tula.domain.llm_factory.service.direct_llm_client import DirectLLMClient


class LLMBuilder:
    def __init__(self, settings: LLMSettings):
        self.settings: LLMSettings = settings

    def build(self, llm_type: LLMType, model_key: str = None) -> LLMBuildResult:
        model_config = self.settings.get_model_config(llm_type.value, model_key)
        params = self.settings.get_parameters(llm_type.value)

        clean_model_name = LLMUtils.extract_model_name(model_config.model)
        
        # Create direct LLM client using LiteLLM
        # LiteLLM automatically detects the provider from the model name
        llm_instance = DirectLLMClient(
            model=model_config.model,
            api_key=model_config.api_key,
            base_url=model_config.base_url,  # For LM Studio, local proxy, etc.
            temperature=params.temperature,
            top_p=params.top_p,
            max_completion_tokens=params.max_completion_tokens,
            presence_penalty=params.presence_penalty,
            frequency_penalty=params.frequency_penalty,
        )
        
        return LLMBuildResult(llm=llm_instance, model_name=clean_model_name)

    def build_creative(self, model_key: str = None) -> LLMBuildResult:
        LLMUtils.disable_telemetry()
        return self.build(LLMType.CREATIVE, model_key)

    def build_evaluation(self, model_key: str = None) -> LLMBuildResult:
        LLMUtils.disable_telemetry()
        return self.build(LLMType.EVALUATION, model_key)
