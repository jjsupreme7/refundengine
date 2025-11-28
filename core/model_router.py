"""
Multi-Model Router
==================

Routes different tasks to the optimal AI model based on task type and stakes.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │  STAGE 1: Extraction (GPT-5)                                │
    │  - PDF/image scanning, OCR, structured data parsing         │
    └─────────────────────┬───────────────────────────────────────┘
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  STAGE 2: Analysis (Claude Sonnet 4.5 / Opus 4.5)           │
    │  - Tax categorization, legal analysis, final decisions      │
    └─────────────────────┬───────────────────────────────────────┘
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  STAGE 3: Validation (GPT-4o-mini / Claude Haiku)           │
    │  - Format checking, confidence scoring, anomaly detection   │
    └─────────────────────────────────────────────────────────────┘

Usage:
    from core.model_router import ModelRouter

    router = ModelRouter()

    # Get model for a specific task
    model_config = router.get_model("extraction", stakes=5000)

    # Execute with automatic routing
    result = router.execute("extraction", prompt, stakes=5000)
"""

import os
from typing import Optional, Literal, Any
from dataclasses import dataclass
from enum import Enum

# API clients
import openai
import anthropic


class TaskType(Enum):
    """Types of tasks that can be routed to different models."""
    EXTRACTION = "extraction"           # PDF/image scanning, OCR
    STRUCTURED_PARSING = "parsing"      # Extract structured data from text
    TAX_ANALYSIS = "analysis"           # Tax categorization, exemption analysis
    LEGAL_CITATION = "legal"            # Legal citation matching
    FINAL_DECISION = "decision"         # Final refund decision with reasoning
    VALIDATION = "validation"           # Format checking, confidence scoring
    EMBEDDING = "embedding"             # Vector embeddings


class Provider(Enum):
    """AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    provider: Provider
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.1
    reason: str = ""
    cost_tier: str = "standard"  # "budget", "standard", "premium"


# Model definitions
MODELS = {
    # OpenAI models
    "gpt-5": ModelConfig(Provider.OPENAI, "gpt-5", 4096, 0.1, "Latest OpenAI flagship", "premium"),
    "gpt-4o": ModelConfig(Provider.OPENAI, "gpt-4o", 4096, 0.1, "Strong multimodal model", "standard"),
    "gpt-4o-mini": ModelConfig(Provider.OPENAI, "gpt-4o-mini", 4096, 0.1, "Fast and cost-effective", "budget"),

    # Anthropic models
    "claude-opus-4.5": ModelConfig(Provider.ANTHROPIC, "claude-opus-4-5-20251101", 4096, 0.1, "Highest reasoning capability", "premium"),
    "claude-sonnet-4.5": ModelConfig(Provider.ANTHROPIC, "claude-sonnet-4-5-20250929", 4096, 0.1, "Best balance of capability and cost", "standard"),
    "claude-haiku": ModelConfig(Provider.ANTHROPIC, "claude-3-5-haiku-20241022", 4096, 0.1, "Fast and affordable", "budget"),

    # Embeddings
    "text-embedding-3-small": ModelConfig(Provider.OPENAI, "text-embedding-3-small", 8191, 0.0, "Standard embeddings", "budget"),
}


# Task-to-model routing configuration
TASK_ROUTING = {
    TaskType.EXTRACTION: {
        "default": "gpt-5",
        "fallback": "gpt-4o",
        "high_stakes": "gpt-5",
    },
    TaskType.STRUCTURED_PARSING: {
        "default": "gpt-5",
        "fallback": "gpt-4o",
        "high_stakes": "gpt-5",
    },
    TaskType.TAX_ANALYSIS: {
        "default": "claude-sonnet-4.5",
        "fallback": "gpt-5",
        "high_stakes": "claude-opus-4.5",
    },
    TaskType.LEGAL_CITATION: {
        "default": "claude-sonnet-4.5",
        "fallback": "gpt-5",
        "high_stakes": "claude-opus-4.5",
    },
    TaskType.FINAL_DECISION: {
        "default": "claude-sonnet-4.5",
        "fallback": "gpt-5",
        "high_stakes": "claude-opus-4.5",
    },
    TaskType.VALIDATION: {
        "default": "gpt-4o-mini",
        "fallback": "claude-haiku",
        "high_stakes": "gpt-4o",
    },
    TaskType.EMBEDDING: {
        "default": "text-embedding-3-small",
        "fallback": "text-embedding-3-small",
        "high_stakes": "text-embedding-3-small",
    },
}

# Stakes thresholds
STAKES_THRESHOLD_HIGH = 25000      # $25k+ uses premium models
STAKES_THRESHOLD_MEDIUM = 5000    # $5k-$25k uses standard models


class ModelRouter:
    """
    Routes tasks to the optimal AI model based on task type and stakes.

    Example:
        router = ModelRouter()

        # Simple usage - get model config for a task
        config = router.get_model("extraction")

        # With stakes consideration
        config = router.get_model("analysis", stakes=50000)
        # Returns claude-opus-4.5 for high-stakes analysis

        # Execute a task with automatic model selection
        result = router.execute(
            task_type="analysis",
            prompt="Analyze this tax situation...",
            stakes=50000
        )
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the model router.

        Args:
            openai_api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            anthropic_api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")

        # Initialize clients lazily
        self._openai_client = None
        self._anthropic_client = None

        # Validate at least one API key is available
        if not self.openai_api_key and not self.anthropic_api_key:
            raise ValueError("At least one API key (OpenAI or Anthropic) is required")

    @property
    def openai_client(self) -> openai.OpenAI:
        """Lazy-load OpenAI client."""
        if self._openai_client is None:
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self._openai_client = openai.OpenAI(api_key=self.openai_api_key)
        return self._openai_client

    @property
    def anthropic_client(self) -> anthropic.Anthropic:
        """Lazy-load Anthropic client."""
        if self._anthropic_client is None:
            if not self.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self._anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        return self._anthropic_client

    def _parse_task_type(self, task: str | TaskType) -> TaskType:
        """Convert string task type to enum."""
        if isinstance(task, TaskType):
            return task

        task_lower = task.lower()
        mapping = {
            "extraction": TaskType.EXTRACTION,
            "extract": TaskType.EXTRACTION,
            "ocr": TaskType.EXTRACTION,
            "scan": TaskType.EXTRACTION,
            "parsing": TaskType.STRUCTURED_PARSING,
            "parse": TaskType.STRUCTURED_PARSING,
            "structured": TaskType.STRUCTURED_PARSING,
            "analysis": TaskType.TAX_ANALYSIS,
            "analyze": TaskType.TAX_ANALYSIS,
            "tax": TaskType.TAX_ANALYSIS,
            "categorize": TaskType.TAX_ANALYSIS,
            "legal": TaskType.LEGAL_CITATION,
            "citation": TaskType.LEGAL_CITATION,
            "law": TaskType.LEGAL_CITATION,
            "decision": TaskType.FINAL_DECISION,
            "decide": TaskType.FINAL_DECISION,
            "final": TaskType.FINAL_DECISION,
            "validation": TaskType.VALIDATION,
            "validate": TaskType.VALIDATION,
            "check": TaskType.VALIDATION,
            "embedding": TaskType.EMBEDDING,
            "embed": TaskType.EMBEDDING,
        }

        if task_lower in mapping:
            return mapping[task_lower]

        raise ValueError(f"Unknown task type: {task}. Valid types: {list(mapping.keys())}")

    def _get_stakes_tier(self, stakes: float) -> str:
        """Determine stakes tier based on dollar amount."""
        if stakes >= STAKES_THRESHOLD_HIGH:
            return "high_stakes"
        elif stakes >= STAKES_THRESHOLD_MEDIUM:
            return "default"
        else:
            return "default"  # Could add "low_stakes" for even cheaper models

    def get_model(
        self,
        task: str | TaskType,
        stakes: float = 0,
        prefer_provider: Optional[Provider] = None,
    ) -> ModelConfig:
        """
        Get the optimal model configuration for a task.

        Args:
            task: Type of task (extraction, analysis, legal, decision, validation, embedding)
            stakes: Dollar amount at stake (higher = better model)
            prefer_provider: Optional provider preference

        Returns:
            ModelConfig with provider, model_id, and settings

        Example:
            >>> router = ModelRouter()
            >>> config = router.get_model("analysis", stakes=50000)
            >>> print(config.model_id)
            'claude-opus-4-5-20251101'
        """
        task_type = self._parse_task_type(task)
        stakes_tier = self._get_stakes_tier(stakes)

        # Get routing configuration for this task
        routing = TASK_ROUTING.get(task_type)
        if not routing:
            raise ValueError(f"No routing configured for task type: {task_type}")

        # Select model based on stakes tier
        model_key = routing.get(stakes_tier, routing["default"])
        model_config = MODELS.get(model_key)

        if not model_config:
            # Fall back to default
            model_key = routing["fallback"]
            model_config = MODELS.get(model_key)

        # Check if preferred provider is available and has capability
        if prefer_provider:
            # Find alternative model from preferred provider
            for key, config in MODELS.items():
                if config.provider == prefer_provider and config.cost_tier == model_config.cost_tier:
                    model_config = config
                    break

        # Verify we have the API key for this provider
        if model_config.provider == Provider.OPENAI and not self.openai_api_key:
            # Fall back to Anthropic
            model_key = routing["fallback"]
            if "claude" in model_key:
                model_config = MODELS[model_key]
            else:
                raise ValueError("OpenAI model selected but no API key available")

        elif model_config.provider == Provider.ANTHROPIC and not self.anthropic_api_key:
            # Fall back to OpenAI
            model_key = routing["fallback"]
            if "gpt" in model_key:
                model_config = MODELS[model_key]
            else:
                raise ValueError("Anthropic model selected but no API key available")

        # Add reason based on stakes
        if stakes >= STAKES_THRESHOLD_HIGH:
            model_config = ModelConfig(
                provider=model_config.provider,
                model_id=model_config.model_id,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                reason=f"${stakes:,.0f} at stake - using premium model for maximum accuracy",
                cost_tier=model_config.cost_tier,
            )
        elif stakes >= STAKES_THRESHOLD_MEDIUM:
            model_config = ModelConfig(
                provider=model_config.provider,
                model_id=model_config.model_id,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                reason=f"${stakes:,.0f} at stake - using standard model",
                cost_tier=model_config.cost_tier,
            )

        return model_config

    def execute(
        self,
        task: str | TaskType,
        prompt: str,
        stakes: float = 0,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        images: Optional[list[str]] = None,  # Base64-encoded images for vision tasks
    ) -> dict[str, Any]:
        """
        Execute a task with automatic model selection.

        Args:
            task: Type of task
            prompt: The prompt to send
            stakes: Dollar amount at stake
            system_prompt: Optional system prompt
            max_tokens: Override max tokens
            temperature: Override temperature
            images: List of base64-encoded images for vision tasks

        Returns:
            Dict with:
                - content: The model's response text
                - model: Model ID used
                - provider: Provider used
                - reason: Why this model was selected
                - usage: Token usage info

        Example:
            >>> result = router.execute(
            ...     task="analysis",
            ...     prompt="Is this purchase exempt from sales tax?",
            ...     stakes=10000
            ... )
            >>> print(result["content"])
        """
        model_config = self.get_model(task, stakes)

        # Override settings if provided
        final_max_tokens = max_tokens or model_config.max_tokens
        final_temperature = temperature if temperature is not None else model_config.temperature

        # Execute based on provider
        if model_config.provider == Provider.OPENAI:
            return self._execute_openai(
                model_config, prompt, system_prompt, final_max_tokens, final_temperature, images
            )
        elif model_config.provider == Provider.ANTHROPIC:
            return self._execute_anthropic(
                model_config, prompt, system_prompt, final_max_tokens, final_temperature, images
            )
        else:
            raise ValueError(f"Unsupported provider: {model_config.provider}")

    def _execute_openai(
        self,
        config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        images: Optional[list[str]],
    ) -> dict[str, Any]:
        """Execute request using OpenAI API."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Build user message
        if images:
            # Vision request
            content = [{"type": "text", "text": prompt}]
            for img in images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img}"}
                })
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": prompt})

        response = self.openai_client.chat.completions.create(
            model=config.model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return {
            "content": response.choices[0].message.content,
            "model": config.model_id,
            "provider": "openai",
            "reason": config.reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        }

    def _execute_anthropic(
        self,
        config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        images: Optional[list[str]],
    ) -> dict[str, Any]:
        """Execute request using Anthropic API."""
        # Build message content
        if images:
            content = []
            for img in images:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img,
                    }
                })
            content.append({"type": "text", "text": prompt})
        else:
            content = prompt

        kwargs = {
            "model": config.model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": content}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.anthropic_client.messages.create(**kwargs)

        return {
            "content": response.content[0].text,
            "model": config.model_id,
            "provider": "anthropic",
            "reason": config.reason,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }
        }

    def get_embedding(self, text: str) -> list[float]:
        """
        Get embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding


# Convenience function for quick access
def get_router() -> ModelRouter:
    """Get a ModelRouter instance with default configuration."""
    return ModelRouter()


# Export
__all__ = [
    "ModelRouter",
    "ModelConfig",
    "TaskType",
    "Provider",
    "MODELS",
    "TASK_ROUTING",
    "get_router",
]
