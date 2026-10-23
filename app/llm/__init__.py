from ..config import settings


def get_provider():
    if settings.llm_provider == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(settings.openai_api_key, settings.openai_model)
    from .gemini import GeminiProvider
    return GeminiProvider(settings.gemini_api_key, settings.gemini_model)
