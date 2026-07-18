"""Central Model Hub for agent-to-agent orchestration on FPT AI Factory.

Enables configuring different specialized models for different tasks (NLU, Explanation, Router, etc.)
and implements adaptive fallback mechanisms to ensure we respect latency SLA limits:
- Latency < 3s when probing/asking clarifying questions.
- Latency < 5s when returning product recommendations with explanations.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from antigravity import fpt_client

logger = logging.getLogger(__name__)

# Registry of all text-generative models on FPT AI Factory with benchmarked profiles
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "gemma-4-26B-A4B-it": {
        "name": "gemma-4-26B-A4B-it",
        "type": "dense/moe",
        "avg_nlu_latency": 0.655,
        "nlu_accuracy": 100.0,
        "json_mode": True,
        "role": "nlu",
        "description": "Fastest and highly accurate Google Gemma-4 model. Default for NLU."
    },
    "Qwen2.5-VL-7B-Instruct": {
        "name": "Qwen2.5-VL-7B-Instruct",
        "type": "vision-language",
        "avg_nlu_latency": 0.825,
        "nlu_accuracy": 100.0,
        "json_mode": True,
        "role": "nlu",
        "description": "Very fast Qwen model. Excellent NLU alternative."
    },
    "DeepSeek-V4-Flash": {
        "name": "DeepSeek-V4-Flash",
        "type": "reasoning",
        "avg_nlu_latency": 0.912,
        "nlu_accuracy": 100.0,
        "json_mode": True,
        "role": "hybrid",
        "description": "Fast reasoning model by DeepSeek. Returns output in reasoning_content."
    },
    "GLM-5.2": {
        "name": "GLM-5.2",
        "type": "reasoning",
        "avg_nlu_latency": 1.059,
        "nlu_accuracy": 100.0,
        "json_mode": True,
        "role": "explainer",
        "description": "Most powerful reasoning model (z.ai 5.2). Excellent for logical trade-offs."
    },
    "gemma-4-31B-it": {
        "name": "gemma-4-31B-it",
        "type": "dense",
        "avg_nlu_latency": 1.533,
        "nlu_accuracy": 100.0,
        "json_mode": True,
        "role": "explainer",
        "description": "Highly capable Gemma-4 dense model."
    },
    "gemma-3-27b-it": {
        "name": "gemma-3-27b-it",
        "type": "dense",
        "avg_nlu_latency": 1.302,
        "nlu_accuracy": 100.0,
        "json_mode": True,
        "role": "hybrid",
        "description": "Reliable Gemma-3 model."
    },
    "Llama-3.3-70B-Instruct": {
        "name": "Llama-3.3-70B-Instruct",
        "type": "dense",
        "avg_nlu_latency": 1.667,
        "nlu_accuracy": 100.0,
        "json_mode": True,
        "role": "explainer",
        "description": "Large Llama model, higher latency but highly accurate."
    },
    "SaoLa3.1-medium": {
        "name": "SaoLa3.1-medium",
        "type": "dense",
        "avg_nlu_latency": 1.516,
        "nlu_accuracy": 100.0,
        "json_mode": True,
        "role": "hybrid",
        "description": "SaoLa local model tuning."
    },
    "gpt-oss-20b": {
        "name": "gpt-oss-20b",
        "type": "dense",
        "avg_nlu_latency": 1.147,
        "nlu_accuracy": 66.7,
        "json_mode": True,
        "role": "utility",
        "description": "Medium-sized open source GPT alternative."
    },
    "gpt-oss-120b": {
        "name": "gpt-oss-120b",
        "type": "dense",
        "avg_nlu_latency": 1.862,
        "nlu_accuracy": 66.7,
        "json_mode": True,
        "role": "utility",
        "description": "Very large GPT model, high latency and moderate accuracy."
    }
}

class ModelHub:
    """Manages role assignment and adaptive routing to FPT AI Factory models."""

    def __init__(self) -> None:
        # Default model routing setup
        self.nlu_model = os.environ.get("NLU_MODEL", "gemma-4-26B-A4B-it")
        self.explain_model = os.environ.get("EXPLAIN_MODEL", "GLM-5.2")
        self.router_model = os.environ.get("ROUTER_MODEL", "gemma-4-26B-A4B-it")
        
        # Verify configured models exist in registry, fallback if not
        if self.nlu_model not in MODEL_REGISTRY:
            self.nlu_model = "gemma-4-26B-A4B-it"
        if self.explain_model not in MODEL_REGISTRY:
            self.explain_model = "GLM-5.2"

    def get_model_for_role(self, role: str) -> str:
        """Get the model ID configured for a specific role ('nlu', 'explainer', 'router')."""
        if role == "nlu":
            return self.nlu_model
        elif role == "explainer":
            return self.explain_model
        elif role == "router":
            return self.router_model
        return self.nlu_model

    def call_agent(
        self,
        role: str,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.0,
        timeout: float = 3.0,
        response_format: Optional[Dict[str, Any]] = None,
        provider: str = "fpt"
    ) -> str:
        """Call a model assigned to a specific role with fallback protection to meet SLAs."""
        primary_model = model or self.get_model_for_role(role)
        
        # Adaptive extra body for reasoning models (GLM, DeepSeek)
        extra_body = None
        if "glm" in primary_model.lower():
            extra_body = {"chat_template_kwargs": {"enable_thinking": False}}
            
        try:
            logger.info(f"ModelHub: Calling primary model '{primary_model}' for role '{role}'")
            return fpt_client.chat_completion(
                primary_model,
                messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                response_format=response_format,
                provider=provider,
                extra_body=extra_body
            )
        except Exception as e:
            logger.warning(f"ModelHub: Primary model '{primary_model}' failed for role '{role}': {e}. Triggering fallback.")
            
            # Fallback strategy based on role
            if role == "nlu":
                # Fallback to extremely fast gemma-4-26B-A4B-it
                fallback_model = "gemma-4-26B-A4B-it"
            else:
                # Fallback to Qwen2.5-VL-7B-Instruct
                fallback_model = "Qwen2.5-VL-7B-Instruct"
                
            if fallback_model == primary_model:
                # If primary was already the fallback model, try another fast one
                fallback_model = "Qwen2.5-VL-7B-Instruct" if primary_model == "gemma-4-26B-A4B-it" else "gemma-4-26B-A4B-it"
                
            fb_extra_body = None
            if "glm" in fallback_model.lower():
                fb_extra_body = {"chat_template_kwargs": {"enable_thinking": False}}
                
            try:
                logger.info(f"ModelHub: Calling fallback model '{fallback_model}' for role '{role}'")
                return fpt_client.chat_completion(
                    fallback_model,
                    messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout,
                    response_format=response_format,
                    provider=provider,
                    extra_body=fb_extra_body
                )
            except Exception as fb_err:
                logger.error(f"ModelHub: Fallback model '{fallback_model}' also failed: {fb_err}")
                raise fb_err

# Global hub instance
hub = ModelHub()
