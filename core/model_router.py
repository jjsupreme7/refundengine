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

import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

import anthropic

# API clients
import openai


class TaskType(Enum):
    """Types of tasks that can be routed to different models."""

    EXTRACTION = "extraction"  # PDF/image scanning, OCR
    STRUCTURED_PARSING = "parsing"  # Extract structured data from text
    TAX_ANALYSIS = "analysis"  # Tax categorization, exemption analysis
    LEGAL_CITATION = "legal"  # Legal citation matching
    FINAL_DECISION = "decision"  # Final refund decision with reasoning
    VALIDATION = "validation"  # Format checking, confidence scoring
    EMBEDDING = "embedding"  # Vector embeddings


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
    "gpt-4o": ModelConfig(
        Provider.OPENAI, "gpt-4o", 4096, 0.1, "Strong multimodal model", "premium"
    ),
    "gpt-4o-standard": ModelConfig(
        Provider.OPENAI, "gpt-4o", 4096, 0.1, "Strong multimodal model", "standard"
    ),
    "gpt-4o-mini": ModelConfig(
        Provider.OPENAI, "gpt-4o-mini", 4096, 0.1, "Fast and cost-effective", "budget"
    ),
    # Anthropic models
    "claude-opus-4.5": ModelConfig(
        Provider.ANTHROPIC,
        "claude-opus-4-5-20251101",
        4096,
        0.1,
        "Highest reasoning capability",
        "premium",
    ),
    "claude-sonnet-4.5": ModelConfig(
        Provider.ANTHROPIC,
        "claude-sonnet-4-5-20250929",
        4096,
        0.1,
        "Best balance of capability and cost",
        "standard",
    ),
    "claude-haiku": ModelConfig(
        Provider.ANTHROPIC,
        "claude-3-5-haiku-20241022",
        4096,
        0.1,
        "Fast and affordable",
        "budget",
    ),
    # Embeddings
    "text-embedding-3-small": ModelConfig(
        Provider.OPENAI,
        "text-embedding-3-small",
        8191,
        0.0,
        "Standard embeddings",
        "budget",
    ),
}


# Task-to-model routing configuration
# Claude for reasoning tasks, GPT for extraction/validation
TASK_ROUTING = {
    TaskType.EXTRACTION: {
        "default": "gpt-4o",
        "fallback": "gpt-4o-mini",
        "high_stakes": "gpt-4o",
    },
    TaskType.STRUCTURED_PARSING: {
        "default": "gpt-4o",
        "fallback": "gpt-4o-mini",
        "high_stakes": "gpt-4o",
    },
    TaskType.TAX_ANALYSIS: {
        "default": "claude-sonnet-4.5",
        "fallback": "gpt-4o",
        "high_stakes": "claude-opus-4.5",
        "low_stakes": "claude-haiku",  # $1k-$5k uses budget model
    },
    TaskType.LEGAL_CITATION: {
        "default": "claude-sonnet-4.5",
        "fallback": "gpt-4o",
        "high_stakes": "claude-opus-4.5",
        "low_stakes": "claude-haiku",  # $1k-$5k uses budget model
    },
    TaskType.FINAL_DECISION: {
        "default": "claude-sonnet-4.5",
        "fallback": "gpt-4o",
        "high_stakes": "claude-opus-4.5",
        "low_stakes": "claude-haiku",  # $1k-$5k uses budget model
    },
    TaskType.VALIDATION: {
        "default": "gpt-4o-mini",
        "fallback": "gpt-4o-mini",
        "high_stakes": "gpt-4o",
    },
    TaskType.EMBEDDING: {
        "default": "text-embedding-3-small",
        "fallback": "text-embedding-3-small",
        "high_stakes": "text-embedding-3-small",
    },
}

# Stakes thresholds
STAKES_THRESHOLD_HIGH = 10000  # $10k+ uses premium models (Claude Opus)
STAKES_THRESHOLD_MEDIUM = 5000  # $5k-$25k uses standard models (Claude Sonnet)
STAKES_THRESHOLD_LOW_MEDIUM = 1000  # $1k-$5k uses budget models (Claude Haiku)


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

        raise ValueError(
            f"Unknown task type: {task}. Valid types: {list(mapping.keys())}"
        )

    def _get_stakes_tier(self, stakes: float) -> str:
        """Determine stakes tier based on dollar amount."""
        if stakes >= STAKES_THRESHOLD_HIGH:
            return "high_stakes"
        elif stakes >= STAKES_THRESHOLD_MEDIUM:
            return "default"
        elif stakes >= STAKES_THRESHOLD_LOW_MEDIUM:
            return "low_stakes"  # $1k-$5k uses cheaper models
        else:
            return "low_stakes"  # <$1k uses budget models

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
                if (
                    config.provider == prefer_provider
                    and config.cost_tier == model_config.cost_tier
                ):
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
        response_format: Optional[dict] = None,  # OpenAI structured outputs schema
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
        final_temperature = (
            temperature if temperature is not None else model_config.temperature
        )

        # Execute based on provider
        if model_config.provider == Provider.OPENAI:
            return self._execute_openai(
                model_config,
                prompt,
                system_prompt,
                final_max_tokens,
                final_temperature,
                images,
                response_format,
            )
        elif model_config.provider == Provider.ANTHROPIC:
            return self._execute_anthropic(
                model_config,
                prompt,
                system_prompt,
                final_max_tokens,
                final_temperature,
                images,
                response_format,
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
        response_format: Optional[dict] = None,
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
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img}"},
                    }
                )
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": prompt})

        # Build API call kwargs
        api_kwargs = {
            "model": config.model_id,
            "messages": messages,
            "max_completion_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add structured outputs if provided (guarantees valid JSON)
        if response_format:
            api_kwargs["response_format"] = response_format

        response = self.openai_client.chat.completions.create(**api_kwargs)

        return {
            "content": response.choices[0].message.content,
            "model": config.model_id,
            "provider": "openai",
            "reason": config.reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }

    def _execute_anthropic(
        self,
        config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        images: Optional[list[str]],
        response_format: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Execute request using Anthropic API."""
        # If response_format is provided, add JSON instructions to system prompt
        # Claude doesn't support OpenAI's json_schema natively, so we enforce via prompt
        if response_format and response_format.get("type") == "json_schema":
            schema = response_format.get("json_schema", {}).get("schema", {})
            json_instruction = (
                "\n\nIMPORTANT: You MUST respond with ONLY valid JSON matching this exact schema. "
                "Do NOT include any text before or after the JSON. Do NOT wrap in markdown code blocks. "
                "Start your response with { and end with }.\n\n"
                f"Required JSON Schema:\n{json.dumps(schema, indent=2)}"
            )
            if system_prompt:
                system_prompt = system_prompt + json_instruction
            else:
                system_prompt = json_instruction.strip()

        # Build message content
        if images:
            content = []
            for img in images:
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img,
                        },
                    }
                )
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

        # Retry with exponential backoff for rate limits
        max_retries = 3
        base_delay = 30  # seconds

        for attempt in range(max_retries):
            try:
                response = self.anthropic_client.messages.create(**kwargs)
                return {
                    "content": response.content[0].text,
                    "model": config.model_id,
                    "provider": "anthropic",
                    "reason": config.reason,
                    "usage": {
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens
                        + response.usage.output_tokens,
                    },
                }
            except anthropic.RateLimitError as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)  # 30s, 60s, 120s
                    print(
                        f"  ⏳ Rate limited, waiting {delay}s before retry {attempt + 2}/{max_retries}..."
                    )
                    time.sleep(delay)
                else:
                    raise e

    def execute_with_web_search(
        self,
        prompt: str,
        stakes: float = 0,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Execute a research task using Claude with web search enabled.

        This performs ACTUAL web searches, not just AI inference from training data.
        Use this for vendor research, legal citation lookups, and fact-checking.

        Args:
            prompt: The research prompt
            stakes: Dollar amount at stake (determines model quality)
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens for response

        Returns:
            Dict with:
                - content: The model's response with research findings
                - sources: List of sources/URLs found
                - model: Model ID used
                - provider: Provider used
        """
        # Use best Claude model for research tasks
        if stakes >= STAKES_THRESHOLD_HIGH:
            model_id = "claude-opus-4-5-20251101"
        else:
            model_id = "claude-sonnet-4-5-20250929"

        # Default system prompt for tax research
        if not system_prompt:
            system_prompt = """You are a tax research specialist for Washington State tax law.
When researching vendors or tax questions:
1. Search for authoritative sources (WA DOR, RCW, WAC)
2. Look up the vendor's actual business type and services
3. Find relevant tax classifications and exemptions
4. Cite your sources with URLs when available
5. Be thorough but concise in your analysis"""

        # Build the request with web search tool enabled
        kwargs = {
            "model": model_id,
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        # Retry with exponential backoff for rate limits
        max_retries = 3
        base_delay = 30  # seconds

        for attempt in range(max_retries):
            try:
                # Use beta header for web search
                response = self.anthropic_client.beta.messages.create(
                    betas=["web-search-2025-03-05"], **kwargs
                )

                # Extract text content and any sources from the response
                text_content = ""
                sources = []

                for block in response.content:
                    if hasattr(block, "text") and block.text:
                        text_content += block.text
                    # Web search results may include citations
                    if (
                        hasattr(block, "type")
                        and block.type == "web_search_tool_result"
                    ):
                        if hasattr(block, "url"):
                            sources.append(block.url)

                return {
                    "content": text_content,
                    "sources": sources,
                    "model": model_id,
                    "provider": "anthropic",
                    "usage": {
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens
                        + response.usage.output_tokens,
                    },
                }

            except anthropic.RateLimitError as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)  # 30s, 60s, 120s
                    print(
                        f"  ⏳ Web search rate limited, waiting {delay}s before retry {attempt + 2}/{max_retries}..."
                    )
                    time.sleep(delay)
                else:
                    raise e

            except Exception as e:
                # Fallback to regular execution without web search if tool not available
                print(
                    f"  ⚠️  Web search unavailable, falling back to standard research: {e}"
                )
                return self.execute(
                    task="analysis",
                    prompt=prompt,
                    stakes=stakes,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                )

    def execute_with_thinking(
        self,
        prompt: str,
        stakes: float = 0,
        system_prompt: Optional[str] = None,
        max_tokens: int = 16000,
        thinking_budget: int = 10000,
    ) -> dict[str, Any]:
        """
        Execute with extended thinking for complex reasoning tasks.

        This enables Claude's "thinking" mode where it reasons step-by-step
        before providing a final answer. Great for complex tax analysis.

        Args:
            prompt: The analysis prompt
            stakes: Dollar amount at stake (higher = more thinking budget)
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens for final response
            thinking_budget: Token budget for thinking (default 10k)

        Returns:
            Dict with:
                - content: The final answer
                - thinking: The reasoning process (if available)
                - model: Model ID used
                - provider: Provider used
                - usage: Token usage info

        Example:
            >>> result = router.execute_with_thinking(
            ...     prompt="Should this $50k software purchase be exempt?",
            ...     stakes=50000,
            ...     thinking_budget=15000
            ... )
            >>> print(result["thinking"])  # See reasoning
            >>> print(result["content"])   # Final answer
        """
        # Scale thinking budget based on stakes
        if stakes >= STAKES_THRESHOLD_HIGH:
            model_id = "claude-opus-4-5-20251101"
            # More thinking for higher stakes
            thinking_budget = max(thinking_budget, 15000)
        else:
            model_id = "claude-sonnet-4-5-20250929"

        # Build request with thinking enabled
        kwargs = {
            "model": model_id,
            "max_tokens": max_tokens,
            "thinking": {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            },
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self.anthropic_client.messages.create(**kwargs)

            # Extract thinking and content from response
            thinking_text = ""
            content_text = ""

            for block in response.content:
                if hasattr(block, "type"):
                    if block.type == "thinking":
                        thinking_text = block.thinking
                    elif block.type == "text":
                        content_text = block.text

            return {
                "content": content_text,
                "thinking": thinking_text,
                "model": model_id,
                "provider": "anthropic",
                "thinking_budget_used": thinking_budget,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                },
            }

        except Exception as e:
            # Fallback to regular execution if thinking not supported
            print(f"  ⚠️  Extended thinking unavailable, falling back to standard: {e}")
            return self.execute(
                task="analysis",
                prompt=prompt,
                stakes=stakes,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )

    def execute_smart(
        self,
        prompt: str,
        task_type: str = "analysis",
        stakes: float = 0,
        vendor_name: Optional[str] = None,
        ai_confidence: Optional[float] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Automatically selects the best execution method based on context.

        Decision logic:
        1. Unknown vendor → Web Search (need to find what they sell)
        2. Stakes > $25k → Extended Thinking (too important to rush)
        3. AI confidence < 70% → Extended Thinking (needs more reasoning)
        4. Complex task types → Extended Thinking (legal, exemption analysis)
        5. Otherwise → Standard fast execution

        Args:
            prompt: The analysis prompt
            task_type: Type of task (analysis, legal, decision, etc.)
            stakes: Dollar amount at stake
            vendor_name: Optional vendor to check against DB
            ai_confidence: Optional confidence score from previous analysis
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens for response

        Returns:
            Dict with content, model, provider, method_used, and usage

        Example:
            >>> result = router.execute_smart(
            ...     prompt="Analyze this purchase...",
            ...     task_type="analysis",
            ...     stakes=50000,
            ...     vendor_name="Acme Corp"
            ... )
            >>> print(result["method_used"])  # "thinking", "web_search", or "standard"
        """
        method_used = "standard"
        reason = ""

        # 1. VENDOR RESEARCH - unknown vendors get web search + extended thinking
        if vendor_name and self._is_unknown_vendor(vendor_name):
            print(
                f"  🔍 Unknown vendor '{vendor_name}' - using web search + extended thinking"
            )

            # Step 1: Web search to find out what this vendor sells
            research_prompt = f"""Research this vendor: {vendor_name}

Find out:
1. What products/services do they sell?
2. Are they a software company, hardware, consulting, etc.?
3. What is their primary business?

Be thorough - this info will be used for WA State tax analysis."""

            research_result = self.execute_with_web_search(
                research_prompt, stakes, system_prompt, max_tokens
            )

            # Step 2: Extended thinking to analyze tax implications
            analysis_prompt = f"""Based on this vendor research:

VENDOR: {vendor_name}
RESEARCH FINDINGS:
{research_result['content']}

ORIGINAL QUESTION:
{prompt}

Analyze the Washington State sales/use tax implications. Consider:
- Is this tangible personal property or a service?
- Are there any applicable exemptions (RCW 82.08, WAC 458-20)?
- What is your confidence level and why?"""

            result = self.execute_with_thinking(
                analysis_prompt, stakes, system_prompt, max_tokens
            )

            result["method_used"] = "web_search+thinking"
            result["routing_reason"] = (
                f"Unknown vendor '{vendor_name}' - researched then analyzed"
            )
            result["research"] = research_result["content"]
            result["sources"] = research_result.get("sources", [])
            return result

        # 2. HIGH STAKES - use extended thinking
        if stakes >= STAKES_THRESHOLD_HIGH:
            print(f"  🧠 High stakes (${stakes:,.0f}) - using extended thinking")
            result = self.execute_with_thinking(
                prompt, stakes, system_prompt, max_tokens
            )
            result["method_used"] = "thinking"
            result["routing_reason"] = (
                f"High stakes (${stakes:,.0f}) - used extended reasoning"
            )
            return result

        # 3. LOW CONFIDENCE - needs deeper reasoning
        if ai_confidence is not None and ai_confidence < 0.7:
            print(
                f"  🧠 Low confidence ({ai_confidence:.0%}) - using extended thinking"
            )
            result = self.execute_with_thinking(
                prompt, stakes, system_prompt, max_tokens
            )
            result["method_used"] = "thinking"
            result["routing_reason"] = (
                f"Low confidence ({ai_confidence:.0%}) - used extended reasoning"
            )
            return result

        # 4. COMPLEX TASK TYPES - use extended thinking
        complex_tasks = ["legal", "decision", "exemption_analysis", "citation"]
        if task_type.lower() in complex_tasks:
            print(f"  🧠 Complex task '{task_type}' - using extended thinking")
            result = self.execute_with_thinking(
                prompt, stakes, system_prompt, max_tokens
            )
            result["method_used"] = "thinking"
            result["routing_reason"] = f"Complex task type '{task_type}'"
            return result

        # 5. DEFAULT - standard fast execution
        result = self.execute(task_type, prompt, stakes, system_prompt, max_tokens)
        result["method_used"] = "standard"
        result["routing_reason"] = "Standard analysis - no special requirements"
        return result

    def _is_unknown_vendor(self, vendor_name: str) -> bool:
        """
        Check if vendor exists in our database.

        Returns True if vendor is unknown (not in vendor_products table).
        """
        try:
            # Import here to avoid circular imports
            from core.database import get_supabase_client

            supabase = get_supabase_client()

            # Check vendor_products table
            result = (
                supabase.table("vendor_products")
                .select("id")
                .ilike("vendor_name", f"%{vendor_name}%")
                .limit(1)
                .execute()
            )

            return len(result.data) == 0
        except Exception:
            # If DB check fails, assume unknown to be safe
            return True

    def get_embedding(self, text: str) -> list[float]:
        """
        Get embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        response = self.openai_client.embeddings.create(
            input=text, model="text-embedding-3-small"
        )
        return response.data[0].embedding

    # ========== OpenAI Batch API Methods (50% discount, 24hr turnaround) ==========

    def create_batch_file(
        self,
        requests: list[dict],
        output_path: str = "scripts/cache/batch_requests.jsonl",
    ) -> str:
        """
        Create a JSONL file for OpenAI Batch API.

        Args:
            requests: List of request dicts with keys: custom_id, prompt, system_prompt, images
            output_path: Path to save the JSONL file

        Returns:
            Path to the created file
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            for req in requests:
                # Build messages
                messages = []
                if req.get("system_prompt"):
                    messages.append({"role": "system", "content": req["system_prompt"]})

                # Handle images for vision requests
                if req.get("images"):
                    content = [{"type": "text", "text": req["prompt"]}]
                    for img in req["images"]:
                        content.append(
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{img}"},
                            }
                        )
                    messages.append({"role": "user", "content": content})
                else:
                    messages.append({"role": "user", "content": req["prompt"]})

                batch_request = {
                    "custom_id": req["custom_id"],
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": req.get("model", "gpt-4o"),
                        "messages": messages,
                        "max_tokens": req.get("max_tokens", 4096),
                        "temperature": req.get("temperature", 0.1),
                    },
                }
                f.write(json.dumps(batch_request) + "\n")

        return output_path

    def submit_batch(
        self, jsonl_path: str, description: str = "Refund Engine extraction batch"
    ) -> dict:
        """
        Submit a batch job to OpenAI Batch API.

        Args:
            jsonl_path: Path to the JSONL file with requests
            description: Description for the batch job

        Returns:
            Dict with batch_id and status
        """
        # Upload the file
        with open(jsonl_path, "rb") as f:
            file_response = self.openai_client.files.create(file=f, purpose="batch")

        # Create the batch
        batch_response = self.openai_client.batches.create(
            input_file_id=file_response.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": description},
        )

        return {
            "batch_id": batch_response.id,
            "status": batch_response.status,
            "input_file_id": file_response.id,
            "created_at": batch_response.created_at,
        }

    def check_batch_status(self, batch_id: str) -> dict:
        """
        Check the status of a batch job.

        Args:
            batch_id: The batch ID returned from submit_batch

        Returns:
            Dict with status, progress, and output_file_id if complete
        """
        batch = self.openai_client.batches.retrieve(batch_id)

        result = {
            "batch_id": batch_id,
            "status": batch.status,
            "request_counts": {
                "total": batch.request_counts.total,
                "completed": batch.request_counts.completed,
                "failed": batch.request_counts.failed,
            },
        }

        if batch.status == "completed" and batch.output_file_id:
            result["output_file_id"] = batch.output_file_id

        if batch.status == "failed" and batch.error_file_id:
            result["error_file_id"] = batch.error_file_id

        return result

    def get_batch_results(
        self, batch_id: str, output_path: str = "scripts/cache/batch_results.jsonl"
    ) -> list[dict]:
        """
        Download and parse batch results.

        Args:
            batch_id: The batch ID
            output_path: Path to save the results

        Returns:
            List of result dicts with custom_id and content
        """
        status = self.check_batch_status(batch_id)

        if status["status"] != "completed":
            raise ValueError(f"Batch not complete. Status: {status['status']}")

        if "output_file_id" not in status:
            raise ValueError("No output file available")

        # Download the results
        file_response = self.openai_client.files.content(status["output_file_id"])
        content = file_response.text

        # Save to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)

        # Parse results
        results = []
        for line in content.strip().split("\n"):
            if line:
                data = json.loads(line)
                result = {
                    "custom_id": data["custom_id"],
                    "content": data["response"]["body"]["choices"][0]["message"][
                        "content"
                    ],
                    "usage": data["response"]["body"]["usage"],
                }
                results.append(result)

        return results

    def wait_for_batch(
        self, batch_id: str, poll_interval: int = 60, max_wait: int = 86400  # 24 hours
    ) -> dict:
        """
        Wait for a batch to complete, polling periodically.

        Args:
            batch_id: The batch ID
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait

        Returns:
            Final status dict
        """
        import time

        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = self.check_batch_status(batch_id)
            print(
                f"  Batch {batch_id[:8]}... status: {status['status']} "
                f"({status['request_counts']['completed']}/{status['request_counts']['total']})"
            )

            if status["status"] in ["completed", "failed", "expired", "cancelled"]:
                return status

            time.sleep(poll_interval)

        raise TimeoutError(f"Batch {batch_id} did not complete within {max_wait}s")


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
    "STAKES_THRESHOLD_HIGH",
    "STAKES_THRESHOLD_MEDIUM",
    "get_router",
]
