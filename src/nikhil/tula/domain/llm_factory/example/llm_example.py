    creative_result_default = builder.build_creative()
    print(f"      Model Name: {creative_result_default.model_name}")
    print(f"      Full Model Path: {creative_result_default.llm.model}")
    print(f"      Temperature: {creative_result_default.llm.temperature}")


def run_example_b(builder: LLMBuilder):
    """Example B: Build a specific 'creative' LLM (llama)."""
    print("\n   => Running Example B: Building specific 'llama' creative LLM...")
    creative_result_llama = builder.build_creative(model_key="llama")
    print(f"      Model Name: {creative_result_llama.model_name}")
    print(f"      Full Model Path: {creative_result_llama.llm.model}")
    print(f"      Temperature: {creative_result_llama.llm.temperature}")


def run_example_c(builder: LLMBuilder):
    """Example C: Build the default 'evaluation' LLM (gemma)."""
    print("\n   => Running Example C: Building default 'evaluation' LLM...")
    # This will also trigger the 'disable_telemetry' utility.
    evaluation_result_default = builder.build_evaluation()
    print(f"      Model Name: {evaluation_result_default.model_name}")
    print(f"      Full Model Path: {evaluation_result_default.llm.model}")
    print(f"      Temperature: {evaluation_result_default.llm.temperature}")


def main():
    """
    An example script demonstrating how to use the Amsha LLM Factory
    with a Dependency Injection Container.
    """
    print("--- Running Amsha LLM Factory Example (with DI Container) ---")

    container = LLMContainer()

    config_path = Path("config/llm_config.yaml")
    container.config.llm.yaml_path.from_value(str(config_path))
    print(f"   Container configured to use '{config_path}'.")

    print("\n2. Requesting the LLMBuilder from the container...")
    try:
        builder: LLMBuilder = container.llm_builder()
        print("   LLMBuilder created successfully by the container.")
    except Exception as e:
        print(f"   Error creating builder: {e}")
        return

    run_example_a(builder)
    # run_example_b(builder)
    # run_example_c(builder)

    print("\n--- Example Finished ---")


if __name__ == "__main__":
    main()
