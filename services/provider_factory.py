"""
Provider Factory
Creates appropriate services based on configuration
Supports DashScope and Gemini providers
"""

import config
from .dashscope_service import DashScopeService
from openai import OpenAI
from .order_service import OrderService
from .llm_service import LLMService
from .gemini_live_service import GeminiLiveService


def create_llm_service(perf_monitor=None):
    """
    Create LLM service based on provider configuration

    Args:
        perf_monitor: PerformanceMetrics instance

    Returns:
        LLM service instance
    """
    if config.PROVIDER == 'gemini':
        # Gemini uses Live API which includes LLM
        # Return a wrapper or None since Live API handles LLM internally
        return None
    else:
        # DashScope with OpenAI-compatible API
        openai_client = OpenAI(
            api_key=config.DASHSCOPE_API_KEY,
            base_url=config.DASHSCOPE_BASE_URL,
            http_client=config.HTTP_CLIENT
        )
        dashscope_service = DashScopeService()
        return LLMService(openai_client, dashscope_service, perf_monitor)


def create_gemini_service(perf_monitor=None):
    """
    Create Gemini Standard API service (ASR + LLM)

    Args:
        perf_monitor: PerformanceMetrics instance

    Returns:
        GeminiStandardService instance or None if not using Gemini
    """
    if config.PROVIDER == 'gemini':
        from .gemini_standard_service import GeminiStandardService
        return GeminiStandardService(perf_monitor)
    return None


def create_order_service():
    """
    Create Order service

    Returns:
        OrderService instance
    """
    return OrderService()


def get_provider_info():
    """Get current provider configuration info"""
    return {
        'provider': config.PROVIDER,
        'asr': config.ASR_PROVIDER,
        'llm': config.LLM_PROVIDER,
        'tts': config.TTS_PROVIDER,
        'gemini_model': config.GEMINI_LIVE_MODEL if config.PROVIDER == 'gemini' else None
    }
