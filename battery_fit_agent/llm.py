"""Chat-model factory. One switch picks the backend; everything else is model-agnostic.

    provider       key (environment variable)  notes
    gemini         GOOGLE_API_KEY              free key at aistudio.google.com (free tier: few requests/day)
    anthropic      ANTHROPIC_API_KEY           Claude via the Claude API (platform.claude.com, pay as you go)
    groq           GROQ_API_KEY                free tier at console.groq.com; text only (no plot images)
    openrouter     OPENROUTER_API_KEY          many models, some free (":free" model ids); text only here
    ollama         -                           any local model served by Ollama, e.g. qwen2.5:14b
"""
import os

DEFAULT_MODELS = {
    "gemini": "gemini-3.8-flash",
    "anthropic": "claude-haiku-5-5",
    "groq": "openai/gpt-oss-120b",
    "openrouter": None,                 # pick a model id with tool support on openrouter.ai/models
    "ollama": "llama3.1:8b",
}
PROVIDERS = list(DEFAULT_MODELS)
_OPENAI_COMPATIBLE = {"groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
                      "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY")}
_KEYS = {"gemini": "GOOGLE_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
         **{p: k for p, (_, k) in _OPENAI_COMPATIBLE.items()}}


def get_chat_model(provider="gemini", model=None, temperature=0.0, requests_per_minute=None,
                   ollama_url="http://localhost:11434"):
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"unknown provider {provider!r}; choose from {PROVIDERS}")
    model = model or DEFAULT_MODELS[provider]
    if not model:
        raise ValueError(f"--model is required for provider {provider!r}")
    if provider in _KEYS and not os.getenv(_KEYS[provider]):
        raise RuntimeError(f"Set {_KEYS[provider]} for provider {provider!r}")
    limiter = None
    if requests_per_minute:                                   # stay inside free-tier rate limits
        from langchain_core.rate_limiters import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(requests_per_second=requests_per_minute / 60, check_every_n_seconds=0.2)
    common = dict(temperature=temperature, rate_limiter=limiter)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, max_retries=6, **common)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, max_tokens=2048, max_retries=6, **common)
    if provider in _OPENAI_COMPATIBLE:
        from langchain_openai import ChatOpenAI
        url, key = _OPENAI_COMPATIBLE[provider]
        return ChatOpenAI(model=model, base_url=url, api_key=os.environ[key], max_retries=6, **common)
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, base_url=ollama_url, num_ctx=16384, **common)


def supports_images(provider):
    """Whether the investigator should attach the diagnostic plot to its first message."""
    return provider in ("gemini", "anthropic")


def structured(llm, schema):
    """Structured output via tool calling, which every provider here supports
    (some OpenAI-compatible endpoints reject OpenAI's json_schema mode)."""
    try:
        return llm.with_structured_output(schema, method="function_calling")
    except (TypeError, ValueError, NotImplementedError):
        return llm.with_structured_output(schema)