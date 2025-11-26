# src/nikhil/amsha/toolkit/llm_factory/dependency/container.py
# container.py
from dependency_injector import containers, providers

from nikhil.tula.domain.llm_factory.service.llm_builder import LLMBuilder
from nikhil.tula.domain.llm_factory.settings.llm_settings import LLMSettings
from nikhil.tula.utils.yaml_utils import YamlUtils


class LLMContainer(containers.DeclarativeContainer):
    """The Dependency Injection Container."""

    config = providers.Configuration()

    yaml_data = providers.Singleton(
        YamlUtils.yaml_safe_load,
        config.llm.yaml_path,
    )

    llm_settings = providers.Singleton(
        lambda data: LLMSettings(**data),
        yaml_data,
    )

    # This part remains the same.
    llm_builder = providers.Factory(
        LLMBuilder,
        settings=llm_settings,
    )
