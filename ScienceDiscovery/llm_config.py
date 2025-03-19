import autogen

# Load configuration for gpt-4o-mini
config_list_4o_mini = autogen.config_list_from_models(model_list=["gpt-4o-mini"])

# Load configuration for gpt-4turbo-mini
config_list_4turbo_mini = autogen.config_list_from_models(model_list=["gpt-4o-mini"])

# gpt-4o-mini base configuration
gpt4o_mini_config = {
    "chat_model": "gpt-4o-mini",       # 指定使用 gpt-4o-mini
    "cache_seed": 42,                 # Ensures reproducibility across runs
    "temperature": 0.8,               # Deterministic output for precise tasks
    "config_list": config_list_4o_mini,
    "timeout": 540000,                # Timeout in milliseconds
    "max_tokens": 1000                # Limits response length
}

# gpt-4o-mini configuration optimized for knowledge graph processing
gpt4o_mini_config_graph = {
    "chat_model": "gpt-4o-mini",       # 指定使用 gpt-4o-mini
    "cache_seed": 42,
    "temperature": 0.8,               # Slightly increased randomness for reasoning tasks
    "config_list": config_list_4o_mini,
    "timeout": 540000,
    "max_tokens": 1500
}

# gpt-4turbo-mini base configuration
gpt4turbo_mini_config = {
    "chat_model": "gpt-4o-mini",   # 指定使用 gpt-4turbo-mini
    "cache_seed": 42,
    "temperature": 0.8,               # Higher randomness for generative tasks
    "config_list": config_list_4turbo_mini,
    "timeout": 540000,
    "max_tokens": 1024
}

# gpt-4turbo-mini configuration optimized for complex knowledge graph reasoning
gpt4turbo_mini_config_graph = {
    "chat_model": "gpt-4o-mini",   # 指定使用 gpt-4turbo-mini
    "cache_seed": 42,
    "temperature": 0.8,               # Increased randomness for complex inference
    "config_list": config_list_4turbo_mini,
    "timeout": 540000,
    "max_tokens": 2000
}
