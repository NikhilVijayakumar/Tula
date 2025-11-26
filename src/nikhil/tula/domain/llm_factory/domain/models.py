# src/nikhil/tula/domain/llm_factory/domain/models.py


from typing import Dict, List, Optional, NamedTuple, TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from nikhil.tula.domain.llm_factory.service.direct_llm_client import DirectLLMClient


class LLMParameters(BaseModel):
    temperature: float = 0.0
    top_p: float = 1.0
    max_completion_tokens: int = 4096
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    stop: Optional[List[str]] = None


class LLMModelConfig(BaseModel):
    base_url: Optional[str] = None
    model: str
    api_key: Optional[str] = None
    api_version : Optional[str] = None


class LLMUseCaseConfig(BaseModel):
    default: str
    models: Dict[str, LLMModelConfig]


class LLMBuildResult(NamedTuple):
    llm: Any  # DirectLLMClient - using Any to avoid circular import issues
    model_name: str
