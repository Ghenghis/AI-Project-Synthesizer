# 🔀 LLM Routing Strategy

## Overview

This document defines **when to use which LLM** for optimal cost, speed, and quality balance.

---

## Provider Tiers

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          LLM PROVIDER HIERARCHY                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TIER 1: LOCAL (Free, Fast, Private)                                        │
│  ═══════════════════════════════════                                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Ollama    │ │  LM Studio  │ │  LocalAI    │ │    vLLM     │           │
│  │             │ │             │ │             │ │             │           │
│  │ • llama3.1  │ │ • Any GGUF  │ │ • OpenAI    │ │ • High      │           │
│  │ • mistral   │ │ • Any GGML  │ │   compatible│ │   throughput│           │
│  │ • codellama │ │             │ │             │ │             │           │
│  │ • deepseek  │ │             │ │             │ │             │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│  Cost: $0 | Latency: 50-500ms | Quality: Good                              │
│                                                                              │
│  TIER 2: FAST CLOUD (Cheap, Very Fast)                                      │
│  ═════════════════════════════════════                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                           │
│  │    Groq     │ │  Together   │ │  Fireworks  │                           │
│  │             │ │             │ │             │                           │
│  │ • llama3    │ │ • Mixtral   │ │ • llama3    │                           │
│  │ • mixtral   │ │ • llama3    │ │ • Mixtral   │                           │
│  │ 500 tok/s   │ │             │ │             │                           │
│  └─────────────┘ └─────────────┘ └─────────────┘                           │
│  Cost: $0.0001/1K | Latency: 100-300ms | Quality: Good                     │
│                                                                              │
│  TIER 3: PREMIUM CLOUD (Best Quality)                                       │
│  ════════════════════════════════════                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  Anthropic  │ │   OpenAI    │ │   Google    │ │   Mistral   │          │
│  │             │ │             │ │             │ │             │          │
│  │ • Claude    │ │ • GPT-4o    │ │ • Gemini    │ │ • Large     │          │
│  │   Sonnet    │ │ • GPT-4    │ │   Pro 1.5   │ │             │          │
│  │ • Claude    │ │ • o1        │ │             │ │             │          │
│  │   Opus      │ │             │ │             │ │             │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│  Cost: $0.003-0.06/1K | Latency: 500-2000ms | Quality: Excellent           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Task-to-LLM Mapping

### Quick Reference Table

| Task Type | Complexity | Recommended | Fallback | Reason |
|-----------|------------|-------------|----------|--------|
| **Reasoning** | Simple | Ollama | Groq | Fast, free |
| **Reasoning** | Complex | Claude Sonnet | GPT-4o | Best CoT |
| **Code Gen** | Simple | DeepSeek Coder (local) | Groq | Code-optimized |
| **Code Gen** | Complex | Claude Sonnet | GPT-4o | Best code quality |
| **Classification** | Any | Ollama | Groq | Fast, cheap |
| **Embedding** | Any | Ollama (nomic) | - | Always local |
| **Summarization** | Short | Ollama | Groq | Adequate |
| **Summarization** | Long | Claude Sonnet | - | 200k context |
| **Chat** | Casual | Ollama | Groq | Conversational |
| **Chat** | Technical | Claude Sonnet | GPT-4o | Accurate |
| **Testing** | Any | Claude Sonnet | Local | High quality |
| **Docs** | Any | Ollama | Claude | Cost efficient |

---

## Detailed Routing Rules

### 1. Complex Reasoning Tasks

**Use: Claude Sonnet / GPT-4o**

These tasks require deep chain-of-thought:
- Architecture design
- Multi-step planning
- Debugging complex issues
- Code review
- Security analysis

```python
# Example routing
if task.requires_chain_of_thought and task.complexity == "complex":
    return "anthropic", "claude-sonnet-4-20250514"
```

### 2. Code Generation

**Use: Varies by complexity**

| Scenario | Model | Reason |
|----------|-------|--------|
| Simple function | DeepSeek Coder 6.7B (local) | Fast, code-focused |
| Complex feature | Claude Sonnet | Best code quality |
| Boilerplate | Ollama llama3.1 | Fast, adequate |
| Refactoring | Claude Sonnet | Understands intent |

### 3. Quick Classifications

**Use: Local (Ollama)**

Fast, cheap tasks:
- Intent detection
- Sentiment analysis
- Category assignment
- Yes/no decisions

```python
# Always use local for classification
if task.type == "classification":
    return "ollama", "llama3.1:8b"
```

### 4. Embeddings

**Use: Always Local**

Never pay for embeddings:
- Use `nomic-embed-text` in Ollama
- Use `all-minilm` for speed
- Cache embeddings aggressively

### 5. Long Context Processing

**Use: Claude (200k context)**

When context exceeds 32k tokens:
- Large codebase analysis
- Documentation synthesis
- Multi-file refactoring

---

## Cost Optimization Strategies

### Strategy 1: Prompt Caching

```python
# Cache expensive prompts
cache_key = hash(system_prompt + task_type)
if cache_key in prompt_cache:
    return prompt_cache[cache_key]
```

### Strategy 2: Response Caching

```python
# Cache LLM responses for repeated queries
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_llm_call(prompt_hash: str, model: str):
    return llm.complete(prompt)
```

### Strategy 3: Local-First with Fallback

```python
async def smart_complete(prompt: str, task_type: str):
    # Try local first
    try:
        result = await ollama.complete(prompt)
        if is_quality_acceptable(result, task_type):
            return result
    except Exception:
        pass
    
    # Fallback to cloud
    return await claude.complete(prompt)
```

### Strategy 4: Batch Processing

```python
# Batch similar requests
async def batch_process(items: list, batch_size: int = 10):
    batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
    
    results = []
    for batch in batches:
        combined_prompt = format_batch(batch)
        response = await llm.complete(combined_prompt)
        results.extend(parse_batch_response(response))
    
    return results
```

---

## Configuration

**File: `config/llm_routing.yaml`**

```yaml
# LLM Routing Configuration

providers:
  local:
    ollama:
      base_url: "http://localhost:11434"
      default_model: "llama3.1:8b"
      models:
        - llama3.1:8b
        - llama3.1:70b
        - deepseek-coder:6.7b
        - deepseek-coder:33b
        - codellama:34b
        - mistral:7b
        - nomic-embed-text
    
    lmstudio:
      base_url: "http://localhost:1234/v1"
      default_model: "local-model"
  
  fast_cloud:
    groq:
      api_key: "${GROQ_API_KEY}"
      default_model: "llama-3.1-70b-versatile"
      rate_limit: 30  # requests per minute
    
    together:
      api_key: "${TOGETHER_API_KEY}"
      default_model: "meta-llama/Llama-3-70b-chat-hf"
  
  premium:
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      models:
        reasoning: "claude-sonnet-4-20250514"
        complex: "claude-sonnet-4-20250514"
    
    openai:
      api_key: "${OPENAI_API_KEY}"
      models:
        default: "gpt-4o"
        reasoning: "o1-preview"

routing_rules:
  # Task type -> provider mapping
  reasoning:
    simple: ["ollama", "groq"]
    medium: ["groq", "anthropic"]
    complex: ["anthropic", "openai"]
  
  code_generation:
    simple: ["ollama:deepseek-coder:6.7b", "groq"]
    medium: ["ollama:deepseek-coder:33b", "anthropic"]
    complex: ["anthropic", "openai"]
  
  classification:
    all: ["ollama", "groq"]
  
  embedding:
    all: ["ollama:nomic-embed-text"]
  
  summarization:
    short: ["ollama", "groq"]
    long: ["anthropic"]  # Needs 200k context

cost_limits:
  daily_budget: 10.0  # USD
  warning_threshold: 0.8  # 80% of budget
  
  provider_limits:
    anthropic:
      daily: 5.0
      per_request: 0.50
    openai:
      daily: 5.0
      per_request: 0.50

fallback_chain:
  # If primary fails, try these in order
  - ollama
  - groq
  - anthropic
  - openai
```

---

## Implementation

**File: `src/llm/router.py` (Updated)**

```python
"""
Smart LLM Router with cost optimization.
"""

import logging
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(Enum):
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    CLASSIFICATION = "classification"
    EMBEDDING = "embedding"
    SUMMARIZATION = "summarization"
    CHAT = "chat"


class Complexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class RoutingDecision:
    provider: str
    model: str
    reason: str
    estimated_cost: float
    fallback: Optional[tuple[str, str]] = None


class LLMRouter:
    """
    Routes LLM requests to optimal provider.
    """
    
    def __init__(self, config_path: str = "config/llm_routing.yaml"):
        self.config = self._load_config(config_path)
        self.daily_spend = 0.0
        self._init_clients()
    
    def _load_config(self, path: str) -> dict:
        """Load routing configuration."""
        config_file = Path(path)
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        return self._default_config()
    
    def _default_config(self) -> dict:
        """Default configuration if file not found."""
        return {
            "providers": {
                "local": {"ollama": {"default_model": "llama3.1:8b"}},
                "premium": {"anthropic": {"models": {"reasoning": "claude-sonnet-4-20250514"}}},
            },
            "cost_limits": {"daily_budget": 10.0},
        }
    
    def _init_clients(self) -> None:
        """Initialize LLM clients."""
        # Clients are initialized lazily
        self._clients = {}
    
    def route(
        self,
        task_type: TaskType,
        complexity: Complexity = Complexity.SIMPLE,
        context_length: int = 0,
        require_fast: bool = False,
        require_cheap: bool = False,
    ) -> RoutingDecision:
        """
        Route request to optimal LLM.
        """
        # Check budget
        if self._over_budget():
            return RoutingDecision(
                provider="ollama",
                model="llama3.1:8b",
                reason="Daily budget exceeded - using local LLM",
                estimated_cost=0.0,
            )
        
        # Embeddings always local
        if task_type == TaskType.EMBEDDING:
            return RoutingDecision(
                provider="ollama",
                model="nomic-embed-text",
                reason="Embeddings always use local model",
                estimated_cost=0.0,
            )
        
        # Classification always local (fast enough)
        if task_type == TaskType.CLASSIFICATION:
            return RoutingDecision(
                provider="ollama",
                model="llama3.1:8b",
                reason="Classification uses local model for speed",
                estimated_cost=0.0,
            )
        
        # Fast + cheap = local
        if require_fast and require_cheap:
            return RoutingDecision(
                provider="ollama",
                model="llama3.1:8b",
                reason="Fast and cheap requirement",
                estimated_cost=0.0,
            )
        
        # Long context = Claude
        if context_length > 32000:
            return RoutingDecision(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                reason="Long context requires Claude's 200k window",
                estimated_cost=self._estimate_cost("anthropic", context_length),
                fallback=("ollama", "llama3.1:70b"),
            )
        
        # Complex reasoning = Claude
        if task_type == TaskType.REASONING and complexity == Complexity.COMPLEX:
            return RoutingDecision(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                reason="Complex reasoning benefits from Claude",
                estimated_cost=self._estimate_cost("anthropic", context_length),
                fallback=("openai", "gpt-4o"),
            )
        
        # Complex code = Claude
        if task_type == TaskType.CODE_GENERATION and complexity == Complexity.COMPLEX:
            return RoutingDecision(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                reason="Complex code generation needs high quality",
                estimated_cost=self._estimate_cost("anthropic", context_length),
                fallback=("ollama", "deepseek-coder:33b"),
            )
        
        # Medium complexity = Groq (fast cloud)
        if complexity == Complexity.MEDIUM:
            return RoutingDecision(
                provider="groq",
                model="llama-3.1-70b-versatile",
                reason="Medium complexity uses fast cloud",
                estimated_cost=self._estimate_cost("groq", context_length),
                fallback=("ollama", "llama3.1:8b"),
            )
        
        # Default = local
        return RoutingDecision(
            provider="ollama",
            model="llama3.1:8b",
            reason="Default to local for cost efficiency",
            estimated_cost=0.0,
        )
    
    def _over_budget(self) -> bool:
        """Check if daily budget exceeded."""
        limit = self.config.get("cost_limits", {}).get("daily_budget", 10.0)
        return self.daily_spend >= limit
    
    def _estimate_cost(self, provider: str, tokens: int) -> float:
        """Estimate cost for provider."""
        # Rough estimates per 1K tokens
        costs = {
            "anthropic": 0.003,  # $3/1M input
            "openai": 0.005,    # $5/1M input
            "groq": 0.0001,     # $0.10/1M
            "ollama": 0.0,
        }
        return costs.get(provider, 0.0) * (tokens / 1000)
    
    async def complete(
        self,
        prompt: str,
        task_type: TaskType = TaskType.CHAT,
        complexity: Complexity = Complexity.SIMPLE,
        **kwargs,
    ) -> str:
        """
        Complete prompt using optimal LLM.
        """
        # Get routing decision
        decision = self.route(
            task_type=task_type,
            complexity=complexity,
            context_length=len(prompt),
        )
        
        logger.info(f"Routing to {decision.provider}/{decision.model}: {decision.reason}")
        
        # Get or create client
        client = self._get_client(decision.provider)
        
        try:
            response = await client.complete(
                prompt=prompt,
                model=decision.model,
                **kwargs,
            )
            
            # Track cost
            self.daily_spend += decision.estimated_cost
            
            return response
            
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}")
            
            # Try fallback
            if decision.fallback:
                fb_provider, fb_model = decision.fallback
                fb_client = self._get_client(fb_provider)
                return await fb_client.complete(prompt=prompt, model=fb_model, **kwargs)
            
            raise
    
    def _get_client(self, provider: str):
        """Get or create LLM client."""
        if provider not in self._clients:
            self._clients[provider] = self._create_client(provider)
        return self._clients[provider]
    
    def _create_client(self, provider: str):
        """Create LLM client for provider."""
        if provider == "ollama":
            from src.llm.ollama_client import OllamaClient
            return OllamaClient()
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic()
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI()
        elif provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq()
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

---

## Summary

| Scenario | Use This | Why |
|----------|----------|-----|
| Budget-conscious | Ollama → Groq → Cloud | Minimize cost |
| Speed-critical | Groq or Ollama | Lowest latency |
| Quality-critical | Claude Sonnet | Best results |
| Long context | Claude | 200k tokens |
| Code generation | DeepSeek (local) or Claude | Code-optimized |
| Embeddings | Always Ollama | Zero cost |

The smart router automatically handles all these decisions!
