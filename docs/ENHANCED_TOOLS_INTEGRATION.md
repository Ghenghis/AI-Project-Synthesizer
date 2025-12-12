# 🔧 ENHANCED TOOLS INTEGRATION GUIDE

## Complete Integration Specifications for Autonomous Vibe Coder Platform

This document provides **comprehensive specifications** for integrating all enhanced tools into the AI Project Synthesizer platform.

---

## Table of Contents

1. [Piper TTS - Voice Output](#-piper-tts---voice-output)
2. [Mem0 - Advanced Memory Management](#-mem0---advanced-memory-management)
3. [LiteLLM - Unified LLM Proxy](#-litellm---unified-llm-proxy)
4. [Firecrawl - Web Scraping](#-firecrawl---web-scraping)
5. [Browser-Use - Browser Automation](#-browser-use---browser-automation)
6. [Complete Integration Architecture](#-complete-integration-architecture)
7. [Implementation Guide](#-implementation-guide)

---

## 🔊 Piper TTS - Voice Output

### Overview

**Piper TTS** is a fast, local neural text-to-speech system that enables agents to speak responses back to users - completing the voice interaction loop.

| Feature | Value |
|---------|-------|
| **Repository** | https://github.com/rhasspy/piper |
| **License** | MIT |
| **Speed** | Real-time synthesis |
| **Voices** | 100+ voices, 25+ languages |
| **GPU Support** | CUDA acceleration available |
| **Format** | ONNX models (~20-100MB each) |

### Why Piper TTS?

1. **Fully Local** - No cloud dependency, complete privacy
2. **Fast** - Real-time synthesis, <100ms latency
3. **Quality** - Neural voices sound natural
4. **Multi-Language** - English, Spanish, German, French, Chinese, etc.
5. **Lightweight** - Runs on CPU or GPU, ~20-100MB models
6. **WSL2 Compatible** - Works in Windows/WSL2 environment

### Installation

```bash
# Install via pip (in virtual environment)
pip install piper-tts

# Or for GPU acceleration
pip install piper-tts onnxruntime-gpu

# Install sounddevice for real-time playback
pip install sounddevice numpy
```

### Voice Models

Download from HuggingFace: https://huggingface.co/rhasspy/piper-voices

| Voice | Language | Quality | Size |
|-------|----------|---------|------|
| `en_US-lessac-medium` | English (US) | Medium | ~65MB |
| `en_US-amy-medium` | English (US Female) | Medium | ~65MB |
| `en_GB-alan-medium` | English (UK) | Medium | ~65MB |
| `de_DE-thorsten-medium` | German | Medium | ~65MB |
| `es_ES-davefx-medium` | Spanish | Medium | ~65MB |
| `zh_CN-huayan-medium` | Chinese | Medium | ~65MB |

### Integration Code

```python
# src/voice/tts_engine.py

import os
import wave
import numpy as np
import sounddevice as sd
from typing import Optional, Literal
from pathlib import Path
from piper.voice import PiperVoice

class PiperTTSEngine:
    """
    Local text-to-speech engine using Piper TTS.
    Provides voice feedback to users without cloud dependencies.
    """
    
    def __init__(
        self,
        model_path: str = "models/tts/en_US-lessac-medium.onnx",
        use_gpu: bool = False
    ):
        """
        Initialize Piper TTS engine.
        
        Args:
            model_path: Path to ONNX voice model
            use_gpu: Whether to use CUDA acceleration
        """
        self.model_path = Path(model_path)
        self.use_gpu = use_gpu
        self.voice: Optional[PiperVoice] = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the voice model."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Voice model not found: {self.model_path}\n"
                f"Download from: https://huggingface.co/rhasspy/piper-voices"
            )
        
        self.voice = PiperVoice.load(str(self.model_path), use_cuda=self.use_gpu)
        self.sample_rate = self.voice.config.sample_rate
    
    def speak(
        self,
        text: str,
        speaker_id: int = 0,
        length_scale: float = 1.0,  # Speed: 1.0 = normal, 1.5 = slower
        save_to_file: Optional[str] = None
    ) -> None:
        """
        Synthesize speech and play immediately.
        
        Args:
            text: Text to speak
            speaker_id: Speaker ID for multi-speaker models
            length_scale: Speech speed (1.0 = normal)
            save_to_file: Optional path to save WAV file
        """
        if not self.voice:
            raise RuntimeError("Voice model not loaded")
        
        # Synthesize to audio stream
        audio_chunks = []
        for audio_bytes in self.voice.synthesize_stream_raw(
            text,
            speaker_id=speaker_id,
            length_scale=length_scale
        ):
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_chunks.append(audio_data)
        
        # Combine all chunks
        full_audio = np.concatenate(audio_chunks)
        
        # Save to file if requested
        if save_to_file:
            with wave.open(save_to_file, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(full_audio.tobytes())
        
        # Play audio
        sd.play(full_audio, self.sample_rate)
        sd.wait()  # Wait for playback to finish
    
    def speak_async(self, text: str, **kwargs) -> None:
        """
        Synthesize and play without blocking (fire-and-forget).
        """
        import threading
        thread = threading.Thread(target=self.speak, args=(text,), kwargs=kwargs)
        thread.daemon = True
        thread.start()
    
    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        speaker_id: int = 0,
        length_scale: float = 1.0
    ) -> str:
        """
        Synthesize speech to WAV file without playing.
        
        Returns:
            Path to output file
        """
        self.speak(text, speaker_id, length_scale, save_to_file=output_path)
        return output_path


# Convenience function for agents
def agent_speak(text: str, voice: str = "default") -> None:
    """
    Simple interface for agents to speak.
    
    Usage:
        agent_speak("Your task is complete!")
    """
    engine = PiperTTSEngine()
    engine.speak(text)
```

### Agent Integration Pattern

```python
# Usage in agent workflows

class CoderAgent:
    def __init__(self):
        self.tts = PiperTTSEngine()
    
    async def complete_task(self, task: str):
        # Do work...
        result = await self._implement_code(task)
        
        # Speak completion to user
        self.tts.speak_async(
            f"Task complete. I've created {result.files_created} files "
            f"with {result.lines_of_code} lines of code."
        )
        
        return result
```

### Configuration

```yaml
# config/voice.yaml

tts:
  provider: piper
  enabled: true
  
  piper:
    model_path: models/tts/en_US-lessac-medium.onnx
    use_gpu: true  # Use CUDA if available
    default_speaker: 0
    speech_rate: 1.0  # 1.0 = normal speed
    
    # Feedback templates
    templates:
      task_start: "Starting task: {task_name}"
      task_complete: "Task complete. {summary}"
      error: "I encountered an error: {error_message}"
      question: "{question}"
      
  # When to speak (can be turned off per category)
  speak_on:
    task_start: true
    task_complete: true
    errors: true
    questions: true
    progress_updates: false  # Too verbose
```

---

## 🧠 Mem0 - Advanced Memory Management

### Overview

**Mem0** is a self-improving memory layer for AI applications. It extracts, consolidates, and retrieves information across sessions.

| Feature | Value |
|---------|-------|
| **Repository** | https://github.com/mem0ai/mem0 |
| **License** | Apache 2.0 |
| **Stars** | 41,000+ GitHub stars |
| **Downloads** | 14 million+ PyPI downloads |
| **Benchmarks** | 26% better than OpenAI Memory |
| **Latency** | 91% faster than full-context |
| **Token Savings** | 90% reduction vs full-context |

### Why Mem0?

1. **Intelligent Extraction** - Automatically extracts facts from conversations
2. **Multi-Level Memory** - User, session, and agent memory
3. **Hybrid Storage** - Vector DB + Key-Value + Graph database
4. **Self-Improving** - Learns and consolidates over time
5. **Framework Support** - Works with CrewAI, LangGraph, LangChain
6. **MCP Server** - Model Context Protocol integration available

### Installation

```bash
# Basic installation
pip install mem0ai

# With graph memory support
pip install "mem0ai[graph]"
```

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MEM0 INTEGRATION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐                  │
│  │  User Messages   │──▶│   Mem0 Core      │                  │
│  └──────────────────┘   │                  │                  │
│                         │  • Extract facts │                  │
│  ┌──────────────────┐   │  • Consolidate   │                  │
│  │  Agent Actions   │──▶│  • Deduplicate   │                  │
│  └──────────────────┘   │  • Score         │                  │
│                         └────────┬─────────┘                  │
│                                  │                             │
│         ┌────────────────────────┼────────────────────────┐   │
│         │                        │                        │   │
│         ▼                        ▼                        ▼   │
│  ┌─────────────┐         ┌─────────────┐          ┌──────────┐│
│  │  Vector DB  │         │  Key-Value  │          │  Graph   ││
│  │  (ChromaDB) │         │  (SQLite)   │          │  (Neo4j) ││
│  │             │         │             │          │          ││
│  │ Embeddings  │         │ Fast lookup │          │ Relations││
│  │ Similarity  │         │ Exact match │          │ Context  ││
│  └─────────────┘         └─────────────┘          └──────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Code

```python
# src/memory/mem0_integration.py

from typing import Dict, List, Optional, Any
from mem0 import Memory
import json
from datetime import datetime

class EnhancedMemorySystem:
    """
    Advanced memory management using Mem0.
    Provides persistent, intelligent memory for all agents.
    """
    
    def __init__(
        self,
        user_id: str = "default_user",
        llm_provider: str = "ollama",  # or "openai", "anthropic"
        embedding_model: str = "nomic-embed-text",
        db_path: str = "data/memory.db"
    ):
        """
        Initialize Mem0 memory system.
        
        Args:
            user_id: Unique identifier for the user
            llm_provider: LLM provider for memory extraction
            embedding_model: Model for embeddings
            db_path: Path to SQLite database
        """
        self.user_id = user_id
        
        # Configure Mem0
        config = {
            "llm": {
                "provider": llm_provider,
                "config": {
                    "model": "llama3.1" if llm_provider == "ollama" else "gpt-4o-mini",
                    "temperature": 0.1,
                }
            },
            "embedder": {
                "provider": "ollama" if llm_provider == "ollama" else "openai",
                "config": {
                    "model": embedding_model,
                }
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "synthesizer_memory",
                    "path": "data/chroma"
                }
            },
            "history_db_path": db_path,
        }
        
        self.memory = Memory.from_config(config)
    
    def add_memory(
        self,
        content: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Add a memory from conversation or agent action.
        
        Args:
            content: The content to remember
            agent_id: Optional agent identifier
            metadata: Optional metadata (category, importance, etc.)
        
        Returns:
            Result with memory IDs created
        """
        combined_metadata = {
            "timestamp": datetime.now().isoformat(),
            "source": agent_id or "user",
            **(metadata or {})
        }
        
        result = self.memory.add(
            content,
            user_id=self.user_id,
            agent_id=agent_id,
            metadata=combined_metadata
        )
        
        return result
    
    def search_memories(
        self,
        query: str,
        limit: int = 5,
        agent_id: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for relevant memories.
        
        Args:
            query: Search query
            limit: Maximum results to return
            agent_id: Filter by agent
            filters: Additional metadata filters
        
        Returns:
            List of relevant memories with scores
        """
        results = self.memory.search(
            query=query,
            user_id=self.user_id,
            agent_id=agent_id,
            limit=limit,
            filters=filters
        )
        
        return results.get("results", [])
    
    def get_context_for_task(
        self,
        task_description: str,
        include_user_preferences: bool = True,
        include_project_context: bool = True
    ) -> str:
        """
        Build context string for an agent task.
        
        Args:
            task_description: Description of the current task
            include_user_preferences: Include user preferences
            include_project_context: Include project history
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Get relevant task memories
        task_memories = self.search_memories(task_description, limit=5)
        if task_memories:
            context_parts.append("## Relevant Past Context")
            for mem in task_memories:
                context_parts.append(f"- {mem['memory']}")
        
        # Get user preferences
        if include_user_preferences:
            prefs = self.search_memories("user preferences style", limit=3)
            if prefs:
                context_parts.append("\n## User Preferences")
                for pref in prefs:
                    context_parts.append(f"- {pref['memory']}")
        
        # Get project context
        if include_project_context:
            project = self.search_memories("project architecture stack", limit=3)
            if project:
                context_parts.append("\n## Project Context")
                for p in project:
                    context_parts.append(f"- {p['memory']}")
        
        return "\n".join(context_parts)
    
    def remember_user_preference(
        self,
        preference_type: str,
        preference_value: str
    ) -> None:
        """
        Store a user preference.
        
        Args:
            preference_type: Type of preference (style, tool, framework, etc.)
            preference_value: The preference value
        """
        self.add_memory(
            f"User preference ({preference_type}): {preference_value}",
            metadata={
                "category": "user_preference",
                "preference_type": preference_type,
                "importance": "high"
            }
        )
    
    def remember_project_decision(
        self,
        decision: str,
        rationale: str,
        agent_id: str
    ) -> None:
        """
        Store a project decision for future reference.
        """
        self.add_memory(
            f"Decision: {decision}. Rationale: {rationale}",
            agent_id=agent_id,
            metadata={
                "category": "project_decision",
                "importance": "high"
            }
        )
    
    def get_all_memories(self, limit: int = 100) -> List[Dict]:
        """Get all memories for the user."""
        return self.memory.get_all(user_id=self.user_id, limit=limit)
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        return self.memory.delete(memory_id)
    
    def update_memory(self, memory_id: str, new_content: str) -> Dict:
        """Update an existing memory."""
        return self.memory.update(memory_id, data=new_content)


# MCP Server Integration
class Mem0MCPServer:
    """
    MCP Server wrapper for Mem0.
    Enables Claude Desktop and other MCP clients to use memory.
    """
    
    def __init__(self, memory_system: EnhancedMemorySystem):
        self.memory = memory_system
    
    def get_tools(self) -> List[Dict]:
        """Return MCP tool definitions."""
        return [
            {
                "name": "remember",
                "description": "Store information for later recall",
                "parameters": {
                    "content": {"type": "string", "description": "What to remember"},
                    "category": {"type": "string", "description": "Category (preference, decision, fact)"}
                }
            },
            {
                "name": "recall",
                "description": "Search memories for relevant information",
                "parameters": {
                    "query": {"type": "string", "description": "What to search for"},
                    "limit": {"type": "integer", "description": "Max results", "default": 5}
                }
            },
            {
                "name": "list_memories",
                "description": "List all stored memories",
                "parameters": {
                    "limit": {"type": "integer", "default": 20}
                }
            }
        ]
```

### Configuration

```yaml
# config/memory.yaml

memory:
  provider: mem0
  enabled: true
  
  mem0:
    # LLM for memory extraction
    llm_provider: ollama  # or openai, anthropic
    llm_model: llama3.1
    
    # Embedding model
    embedding_provider: ollama
    embedding_model: nomic-embed-text
    
    # Vector store
    vector_store: chroma
    vector_path: data/chroma
    
    # Database for history
    db_path: data/memory.db
    
    # Graph memory (optional, requires Neo4j)
    graph_enabled: false
    neo4j_url: bolt://localhost:7687
    
  # Memory categories
  categories:
    - user_preferences
    - project_decisions
    - architecture
    - code_patterns
    - errors_solutions
    - tool_usage
    
  # Auto-memory triggers
  auto_remember:
    user_corrections: true
    architecture_decisions: true
    error_solutions: true
    preferences_mentioned: true
```

---

## 🔀 LiteLLM - Unified LLM Proxy

### Overview

**LiteLLM** provides a unified interface to 100+ LLM providers with cost tracking, load balancing, and fallbacks.

| Feature | Value |
|---------|-------|
| **Repository** | https://github.com/BerriAI/litellm |
| **License** | MIT |
| **Providers** | 100+ (OpenAI, Anthropic, Ollama, Azure, etc.) |
| **Format** | OpenAI-compatible API |
| **Features** | Cost tracking, load balancing, fallbacks |

### Why LiteLLM?

1. **Unified API** - One interface for all LLM providers
2. **Cost Tracking** - Track spending per model/user
3. **Load Balancing** - Distribute across multiple deployments
4. **Fallbacks** - Automatic failover if one provider fails
5. **Rate Limiting** - Prevent abuse
6. **Caching** - Reduce redundant API calls

### Installation

```bash
# SDK installation
pip install litellm

# For proxy server
pip install "litellm[proxy]"
```

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LITELLM PROXY LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  All Agents ──▶ LiteLLM Router ──▶ Best Provider                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │   ┌─────────────┐    ┌─────────────┐    ┌────────────┐ │   │
│  │   │   Local     │    │   Cloud     │    │   Cloud    │ │   │
│  │   │   Ollama    │    │   Claude    │    │   OpenAI   │ │   │
│  │   │   (Free)    │    │   (Smart)   │    │   (GPT)    │ │   │
│  │   └─────────────┘    └─────────────┘    └────────────┘ │   │
│  │         │                  │                  │         │   │
│  │         └──────────────────┼──────────────────┘         │   │
│  │                            │                             │   │
│  │                    ┌───────▼───────┐                    │   │
│  │                    │   LiteLLM     │                    │   │
│  │                    │   Router      │                    │   │
│  │                    │               │                    │   │
│  │                    │ • Cost track  │                    │   │
│  │                    │ • Fallback    │                    │   │
│  │                    │ • Rate limit  │                    │   │
│  │                    │ • Cache       │                    │   │
│  │                    └───────────────┘                    │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Code

```python
# src/llm/litellm_router.py

import os
from typing import List, Dict, Optional, Any
from litellm import completion, acompletion
import litellm

# Enable cost tracking
litellm.success_callback = ["langfuse"]  # Optional: Langfuse logging

class UnifiedLLMRouter:
    """
    Unified LLM routing using LiteLLM.
    Provides cost tracking, fallbacks, and load balancing.
    """
    
    def __init__(self, config_path: str = "config/llm_routing.yaml"):
        """Initialize the LLM router."""
        self.config = self._load_config(config_path)
        self._setup_providers()
    
    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML."""
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_providers(self) -> None:
        """Configure provider API keys."""
        providers = self.config.get("providers", {})
        
        if providers.get("openai", {}).get("enabled"):
            os.environ["OPENAI_API_KEY"] = providers["openai"].get("api_key", "")
        
        if providers.get("anthropic", {}).get("enabled"):
            os.environ["ANTHROPIC_API_KEY"] = providers["anthropic"].get("api_key", "")
        
        if providers.get("groq", {}).get("enabled"):
            os.environ["GROQ_API_KEY"] = providers["groq"].get("api_key", "")
    
    def complete(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        task_type: str = "general",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
        fallback_models: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Any:
        """
        Complete a chat with automatic model selection.
        
        Args:
            messages: Chat messages
            model: Specific model (or auto-select based on task)
            task_type: Type of task (coding, reasoning, simple, etc.)
            max_tokens: Maximum response tokens
            temperature: Response randomness
            stream: Whether to stream response
            fallback_models: Models to try if primary fails
            metadata: Tracking metadata
        
        Returns:
            LLM response
        """
        # Auto-select model if not specified
        if not model:
            model = self._select_model(task_type, messages)
        
        # Build fallback list
        if not fallback_models:
            fallback_models = self._get_fallbacks(model)
        
        try:
            response = completion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream,
                metadata=metadata or {}
            )
            return response
        
        except Exception as e:
            # Try fallbacks
            for fallback in fallback_models:
                try:
                    return completion(
                        model=fallback,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=stream
                    )
                except:
                    continue
            
            raise e
    
    async def acomplete(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Async completion."""
        if not model:
            model = self._select_model(kwargs.get("task_type", "general"), messages)
        
        return await acompletion(
            model=model,
            messages=messages,
            **kwargs
        )
    
    def _select_model(self, task_type: str, messages: List[Dict]) -> str:
        """
        Select optimal model based on task type and content.
        
        Routing strategy:
        - Simple tasks → Local Ollama (free)
        - Coding → Claude Sonnet or GPT-4
        - Complex reasoning → Claude Opus or o1
        - Fast responses → Groq
        """
        routing = self.config.get("routing", {})
        
        # Check message complexity
        total_tokens = sum(len(m.get("content", "")) for m in messages) // 4
        
        # Route based on task type
        if task_type == "simple" and total_tokens < 500:
            return routing.get("simple", "ollama/llama3.1")
        
        elif task_type == "coding":
            return routing.get("coding", "anthropic/claude-sonnet-4-20250514")
        
        elif task_type == "reasoning":
            return routing.get("reasoning", "anthropic/claude-sonnet-4-20250514")
        
        elif task_type == "fast":
            return routing.get("fast", "groq/llama-3.1-70b-versatile")
        
        elif task_type == "long_context" or total_tokens > 10000:
            return routing.get("long_context", "anthropic/claude-sonnet-4-20250514")
        
        else:
            return routing.get("default", "ollama/llama3.1")
    
    def _get_fallbacks(self, primary_model: str) -> List[str]:
        """Get fallback models for a primary model."""
        fallbacks = self.config.get("fallbacks", {})
        return fallbacks.get(primary_model, [
            "ollama/llama3.1",
            "anthropic/claude-sonnet-4-20250514",
            "openai/gpt-4o"
        ])
    
    def get_cost_report(self) -> Dict:
        """Get cost tracking report."""
        # Integration with litellm cost tracking
        return litellm.get_model_cost_map()


# Convenience functions
def smart_complete(
    prompt: str,
    task_type: str = "general",
    system_prompt: Optional[str] = None
) -> str:
    """
    Simple interface for smart LLM completion.
    
    Usage:
        response = smart_complete("Write a Python function", task_type="coding")
    """
    router = UnifiedLLMRouter()
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = router.complete(messages, task_type=task_type)
    return response.choices[0].message.content
```

### LiteLLM Proxy Server Configuration

```yaml
# config/litellm_config.yaml

model_list:
  # Local models (FREE)
  - model_name: local-llama
    litellm_params:
      model: ollama/llama3.1
      api_base: http://localhost:11434
      
  - model_name: local-deepseek
    litellm_params:
      model: ollama/deepseek-coder-v2
      api_base: http://localhost:11434
      
  # Cloud models (PAID)
  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-sonnet-4-20250514
      api_key: os.environ/ANTHROPIC_API_KEY
      
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      
  - model_name: groq-fast
    litellm_params:
      model: groq/llama-3.1-70b-versatile
      api_key: os.environ/GROQ_API_KEY

# Routing rules
router_settings:
  routing_strategy: "least-busy"  # or "simple-shuffle", "latency-based"
  
  # Model groups for fallback
  model_group_alias:
    coding:
      - claude-sonnet
      - gpt-4o
      - local-deepseek
    fast:
      - groq-fast
      - local-llama
    default:
      - local-llama
      - claude-sonnet

# Cost tracking
litellm_settings:
  success_callback: ["langfuse"]
  failure_callback: ["langfuse"]
  set_verbose: false
  
# Rate limiting
general_settings:
  master_key: sk-synthesizer-master-key
  database_url: "postgresql://user:pass@localhost/litellm"
```

---

## 🔥 Firecrawl - Web Scraping

### Overview

**Firecrawl** turns any website into clean, LLM-ready markdown or structured data.

| Feature | Value |
|---------|-------|
| **Repository** | https://github.com/firecrawl/firecrawl |
| **License** | AGPL-3.0 |
| **Output** | Markdown, JSON, screenshots |
| **Features** | JS rendering, anti-bot bypass, crawling |
| **Speed** | <1 second per page |
| **Coverage** | 96% of websites |

### Why Firecrawl?

1. **LLM-Ready Output** - Clean markdown, not messy HTML
2. **JavaScript Rendering** - Handles dynamic sites
3. **Anti-Bot Bypass** - Handles CAPTCHAs and blocks
4. **Structured Extraction** - Extract specific data with AI
5. **Full Site Crawling** - Scrape entire websites
6. **Self-Hostable** - Run locally or use cloud API

### Installation

```bash
pip install firecrawl-py
```

### Integration Code

```python
# src/tools/firecrawl_tool.py

from typing import Dict, List, Optional, Any
from firecrawl import FirecrawlApp
import json

class FirecrawlResearchTool:
    """
    Web research tool using Firecrawl.
    Enables agents to gather information from any website.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        self_hosted_url: Optional[str] = None
    ):
        """
        Initialize Firecrawl tool.
        
        Args:
            api_key: Firecrawl API key (for cloud)
            self_hosted_url: URL of self-hosted instance
        """
        if self_hosted_url:
            self.app = FirecrawlApp(api_url=self_hosted_url)
        elif api_key:
            self.app = FirecrawlApp(api_key=api_key)
        else:
            raise ValueError("Either api_key or self_hosted_url required")
    
    def scrape_page(
        self,
        url: str,
        formats: List[str] = ["markdown"],
        wait_for: Optional[str] = None,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Scrape a single page.
        
        Args:
            url: URL to scrape
            formats: Output formats (markdown, html, screenshot, links)
            wait_for: CSS selector to wait for
            timeout: Timeout in milliseconds
        
        Returns:
            Scraped content in requested formats
        """
        params = {
            "formats": formats,
            "timeout": timeout
        }
        
        if wait_for:
            params["waitFor"] = wait_for
        
        result = self.app.scrape_url(url, params=params)
        return result
    
    def crawl_site(
        self,
        url: str,
        max_pages: int = 10,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Crawl an entire website.
        
        Args:
            url: Starting URL
            max_pages: Maximum pages to crawl
            exclude_patterns: URL patterns to exclude
            include_patterns: URL patterns to include
        
        Returns:
            List of scraped pages
        """
        params = {
            "limit": max_pages,
        }
        
        if exclude_patterns:
            params["excludePaths"] = exclude_patterns
        if include_patterns:
            params["includePaths"] = include_patterns
        
        result = self.app.crawl_url(url, params=params)
        return result.get("data", [])
    
    def search_and_scrape(
        self,
        query: str,
        num_results: int = 5
    ) -> List[Dict]:
        """
        Search the web and scrape results.
        
        Args:
            query: Search query
            num_results: Number of results to scrape
        
        Returns:
            Scraped content from search results
        """
        results = self.app.search(query, params={"limit": num_results})
        return results.get("data", [])
    
    def extract_structured_data(
        self,
        url: str,
        prompt: str,
        schema: Optional[Dict] = None
    ) -> Dict:
        """
        Extract structured data from a page using AI.
        
        Args:
            url: URL to extract from
            prompt: Description of what to extract
            schema: Optional JSON schema for output
        
        Returns:
            Extracted structured data
        """
        params = {
            "formats": ["extract"],
            "extract": {
                "prompt": prompt
            }
        }
        
        if schema:
            params["extract"]["schema"] = schema
        
        result = self.app.scrape_url(url, params=params)
        return result.get("extract", {})
    
    def get_site_map(self, url: str) -> List[str]:
        """
        Get all URLs from a website (fast).
        
        Args:
            url: Website URL
        
        Returns:
            List of all URLs found
        """
        result = self.app.map_url(url)
        return result.get("links", [])


# Research Agent Integration
class ResearchAgent:
    """
    Agent that uses Firecrawl for web research.
    """
    
    def __init__(self, firecrawl_tool: FirecrawlResearchTool):
        self.tool = firecrawl_tool
    
    async def research_topic(
        self,
        topic: str,
        depth: str = "basic"  # basic, detailed, comprehensive
    ) -> Dict[str, Any]:
        """
        Research a topic by searching and analyzing web sources.
        """
        # Search for relevant pages
        search_results = self.tool.search_and_scrape(topic, num_results=5)
        
        # Extract key information from each source
        findings = []
        for result in search_results:
            finding = {
                "source": result.get("url"),
                "title": result.get("metadata", {}).get("title"),
                "content_summary": result.get("markdown", "")[:1000],
            }
            findings.append(finding)
        
        return {
            "topic": topic,
            "sources_analyzed": len(findings),
            "findings": findings
        }
    
    async def extract_documentation(
        self,
        docs_url: str,
        max_pages: int = 20
    ) -> List[Dict]:
        """
        Extract documentation from a docs site.
        Useful for learning about libraries/frameworks.
        """
        # Get all doc pages
        pages = self.tool.crawl_site(
            docs_url,
            max_pages=max_pages,
            include_patterns=["*/docs/*", "*/guide/*", "*/api/*"]
        )
        
        # Format for LLM context
        docs = []
        for page in pages:
            docs.append({
                "title": page.get("metadata", {}).get("title"),
                "url": page.get("url"),
                "content": page.get("markdown", "")
            })
        
        return docs
```

### Configuration

```yaml
# config/firecrawl.yaml

firecrawl:
  # Cloud API (easier setup)
  api_key: ${FIRECRAWL_API_KEY}
  
  # OR Self-hosted (more control)
  # self_hosted_url: http://localhost:3002
  
  # Default settings
  defaults:
    formats:
      - markdown
    timeout: 30000
    max_pages: 10
    
  # Research agent settings
  research:
    max_sources: 5
    extract_summaries: true
    save_raw_content: false
    
  # Rate limiting
  rate_limit:
    requests_per_minute: 20
```

---

## 🌐 Browser-Use - Browser Automation

### Overview

**Browser-Use** enables AI agents to control web browsers using natural language.

| Feature | Value |
|---------|-------|
| **Repository** | https://github.com/browser-use/browser-use |
| **Stars** | 60,000+ GitHub stars |
| **Funding** | $17M seed funding |
| **Backend** | Playwright |
| **LLM Support** | All major providers |
| **Speed** | 3-5x faster than alternatives |

### Why Browser-Use?

1. **Natural Language Control** - Just describe what to do
2. **Visual + HTML** - Uses both vision and DOM
3. **Self-Correcting** - Automatic error recovery
4. **Multi-LLM** - Works with any LLM provider
5. **Custom Actions** - Add your own tools
6. **Production Ready** - Cloud option available

### Installation

```bash
# Install browser-use
pip install browser-use

# Install browser
playwright install chromium
```

### Integration Code

```python
# src/tools/browser_automation.py

import asyncio
from typing import Optional, Dict, Any, List
from browser_use import Browser, Agent
from browser_use.agent.service import Agent as BrowserAgent

class BrowserAutomationTool:
    """
    Browser automation tool using Browser-Use.
    Enables agents to interact with websites.
    """
    
    def __init__(
        self,
        llm_provider: str = "anthropic",
        headless: bool = True
    ):
        """
        Initialize browser automation.
        
        Args:
            llm_provider: LLM provider for the browser agent
            headless: Run browser without GUI
        """
        self.llm_provider = llm_provider
        self.headless = headless
        self.browser: Optional[Browser] = None
    
    async def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if not self.browser:
            self.browser = Browser(headless=self.headless)
        return self.browser
    
    async def execute_task(
        self,
        task: str,
        starting_url: Optional[str] = None,
        max_steps: int = 20,
        save_trace: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a browser task using natural language.
        
        Args:
            task: Natural language task description
            starting_url: URL to start from
            max_steps: Maximum actions to take
            save_trace: Save execution trace
        
        Returns:
            Task result with extracted data
        """
        browser = await self._get_browser()
        
        # Create agent for this task
        agent = BrowserAgent(
            task=task,
            browser=browser,
            llm=self._get_llm()
        )
        
        # Navigate to starting URL if provided
        if starting_url:
            await browser.goto(starting_url)
        
        # Execute task
        result = await agent.run(max_steps=max_steps)
        
        return {
            "success": result.is_done,
            "steps_taken": len(result.history),
            "result": result.result,
            "extracted_data": result.extracted_data
        }
    
    def _get_llm(self):
        """Get LLM based on provider."""
        if self.llm_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model="claude-sonnet-4-20250514")
        elif self.llm_provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4o")
        else:
            from langchain_ollama import ChatOllama
            return ChatOllama(model="llama3.1")
    
    async def fill_form(
        self,
        url: str,
        form_data: Dict[str, str],
        submit: bool = True
    ) -> Dict[str, Any]:
        """
        Fill out a web form.
        
        Args:
            url: URL of the form
            form_data: Field names and values
            submit: Whether to submit the form
        
        Returns:
            Result of form submission
        """
        # Build task description
        fields = ", ".join([f"{k}: {v}" for k, v in form_data.items()])
        task = f"Go to {url}, fill in the form with: {fields}"
        if submit:
            task += ", then submit the form"
        
        return await self.execute_task(task, starting_url=url)
    
    async def extract_data(
        self,
        url: str,
        data_description: str
    ) -> Dict[str, Any]:
        """
        Extract specific data from a webpage.
        
        Args:
            url: URL to extract from
            data_description: Description of data to extract
        
        Returns:
            Extracted data
        """
        task = f"Go to {url} and extract: {data_description}"
        return await self.execute_task(task, starting_url=url)
    
    async def take_screenshot(
        self,
        url: str,
        output_path: str
    ) -> str:
        """
        Take a screenshot of a webpage.
        
        Args:
            url: URL to screenshot
            output_path: Path to save screenshot
        
        Returns:
            Path to saved screenshot
        """
        browser = await self._get_browser()
        await browser.goto(url)
        await browser.screenshot(path=output_path)
        return output_path
    
    async def close(self):
        """Close browser instance."""
        if self.browser:
            await self.browser.close()
            self.browser = None


# Example usage patterns
async def demo_browser_automation():
    """Demonstrate browser automation capabilities."""
    
    tool = BrowserAutomationTool(headless=False)
    
    try:
        # Example 1: Research task
        result = await tool.execute_task(
            task="Search for 'Python async programming' on Google and summarize the top 3 results",
            starting_url="https://google.com"
        )
        print(f"Research result: {result}")
        
        # Example 2: Form filling
        result = await tool.fill_form(
            url="https://example.com/contact",
            form_data={
                "name": "John Doe",
                "email": "john@example.com",
                "message": "Hello from AI agent!"
            },
            submit=False  # Don't actually submit
        )
        
        # Example 3: Data extraction
        result = await tool.extract_data(
            url="https://news.ycombinator.com",
            data_description="The titles and point counts of the top 5 stories"
        )
        
    finally:
        await tool.close()
```

### Configuration

```yaml
# config/browser.yaml

browser:
  provider: browser-use
  enabled: true
  
  browser_use:
    # Browser settings
    headless: true
    timeout: 60000
    
    # LLM for browser control
    llm_provider: anthropic
    llm_model: claude-sonnet-4-20250514
    
    # Execution limits
    max_steps: 30
    max_retries: 3
    
    # Cloud option (for production)
    use_cloud: false
    cloud_api_key: ${BROWSER_USE_API_KEY}
    
  # Task templates
  templates:
    research: "Search for '{query}' and summarize the top {n} results"
    fill_form: "Fill form at {url} with: {data}"
    extract: "Extract {description} from {url}"
    screenshot: "Take a screenshot of {url}"
    
  # Safety settings
  safety:
    allowed_domains: []  # Empty = all allowed
    blocked_domains:
      - "*.bank.com"
      - "*.gov"
    require_approval_for:
      - form_submit
      - login
      - payment
```

---

## 🏗️ Complete Integration Architecture

### Updated System Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                        AUTONOMOUS VIBE CODER PLATFORM - ENHANCED                              │
│                     "You dream it. You describe it. AI builds it."                           │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  ╔═══════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                          USER INPUT LAYER                                              ║  │
│  ║                                                                                        ║  │
│  ║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              ║  │
│  ║  │  🎤 VOICE    │  │  💬 CHAT     │  │  🖥️ WEB UI   │  │  📡 API      │              ║  │
│  ║  │              │  │              │  │              │  │              │              ║  │
│  ║  │  GLM-ASR     │  │  Natural     │  │  Dashboard   │  │  MCP Server  │              ║  │
│  ║  │  (1.5B)      │  │  Language    │  │  TUI         │  │  REST/WS     │              ║  │
│  ║  │  Multi-lang  │  │              │  │              │  │              │              ║  │
│  ║  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘              ║  │
│  ║         │                  │                  │                  │                    ║  │
│  ║         └──────────────────┼──────────────────┼──────────────────┘                    ║  │
│  ║                            │                  │                                        ║  │
│  ║                     ┌──────▼──────────────────▼──────┐                                ║  │
│  ║                     │      🔊 PIPER TTS             │  ◀──── Voice Feedback          ║  │
│  ║                     │      (Response Speech)        │                                 ║  │
│  ║                     └────────────────────────────────┘                                ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════════════════╝  │
│                                         │                                                    │
│                                         ▼                                                    │
│  ╔═══════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                       ORCHESTRATION BRAIN + MEMORY                                     ║  │
│  ║                                                                                        ║  │
│  ║  ┌────────────────────────────────────────────────────────────────────────────────┐  ║  │
│  ║  │                        MASTER COORDINATOR                                       │  ║  │
│  ║  │                                                                                 │  ║  │
│  ║  │  • Intent Classification      • Task Decomposition                             │  ║  │
│  ║  │  • Framework Selection        • Agent Assignment                               │  ║  │
│  ║  │  • Progress Tracking          • Error Escalation                               │  ║  │
│  ║  └────────────────────────────────────────────────────────────────────────────────┘  ║  │
│  ║                                         │                                             ║  │
│  ║  ┌────────────────────────────────────────────────────────────────────────────────┐  ║  │
│  ║  │                        🧠 MEM0 MEMORY LAYER                                     │  ║  │
│  ║  │                                                                                 │  ║  │
│  ║  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │  ║  │
│  ║  │  │ User Prefs   │  │ Project      │  │ Code         │  │ Error        │       │  ║  │
│  ║  │  │ & Style      │  │ Decisions    │  │ Patterns     │  │ Solutions    │       │  ║  │
│  ║  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘       │  ║  │
│  ║  │              │              │              │              │                     │  ║  │
│  ║  │              └──────────────┼──────────────┴──────────────┘                     │  ║  │
│  ║  │                             │                                                   │  ║  │
│  ║  │                    Vector DB (ChromaDB) + Key-Value (SQLite)                   │  ║  │
│  ║  └────────────────────────────────────────────────────────────────────────────────┘  ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════════════════╝  │
│                                         │                                                    │
│                                         ▼                                                    │
│  ╔═══════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                        🔀 LITELLM UNIFIED LLM LAYER                                    ║  │
│  ║                                                                                        ║  │
│  ║  ┌─────────────────────────────────────────────────────────────────────────────────┐ ║  │
│  ║  │  Single API ──▶ 100+ LLM Providers with Cost Tracking + Fallbacks              │ ║  │
│  ║  │                                                                                  │ ║  │
│  ║  │  LOCAL (Free)              │  CLOUD (Powerful)           │  FAST (Speed)       │ ║  │
│  ║  │  ├── Ollama/llama3.1       │  ├── Claude Sonnet          │  ├── Groq           │ ║  │
│  ║  │  ├── Ollama/deepseek       │  ├── Claude Opus            │  └── Together.ai    │ ║  │
│  ║  │  └── LM Studio             │  ├── GPT-4o                 │                      │ ║  │
│  ║  │                            │  └── Gemini Pro             │                      │ ║  │
│  ║  └─────────────────────────────────────────────────────────────────────────────────┘ ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════════════════╝  │
│                                         │                                                    │
│                                         ▼                                                    │
│  ╔═══════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                    AGENT FRAMEWORK LAYER                                               ║  │
│  ║                                                                                        ║  │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     ║  │
│  ║  │  Microsoft  │ │   CrewAI    │ │  LangGraph  │ │   OpenAI    │ │  LangChain  │     ║  │
│  ║  │   Agent     │ │             │ │             │ │   Swarm     │ │   + n8n     │     ║  │
│  ║  │  Framework  │ │  Role-Based │ │  Stateful   │ │             │ │             │     ║  │
│  ║  │             │ │  Crews      │ │  Workflows  │ │  Lightweight│ │  Already    │     ║  │
│  ║  │ SK+AutoGen  │ │             │ │             │ │  Handoffs   │ │  Integrated │     ║  │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘     ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════════════════╝  │
│                                         │                                                    │
│                                         ▼                                                    │
│  ╔═══════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                     SPECIALIST AGENTS (14 Total)                                       ║  │
│  ║                                                                                        ║  │
│  ║  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       ║  │
│  ║  │Architect│ │ Coder  │ │ Tester │ │ DevOps │ │  Docs  │ │ Debug  │ │Security│       ║  │
│  ║  │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │       ║  │
│  ║  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       ║  │
│  ║  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐ ┌────────────────┐  ║  │
│  ║  │Database│ │  API   │ │Frontend│ │  Git   │ │   🔥 Research  │ │   🌐 Browser   │  ║  │
│  ║  │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │     Agent      │ │     Agent      │  ║  │
│  ║  │        │ │        │ │        │ │        │ │   (Firecrawl)  │ │  (Browser-Use) │  ║  │
│  ║  └────────┘ └────────┘ └────────┘ └────────┘ └────────────────┘ └────────────────┘  ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════════════════╝  │
│                                         │                                                    │
│                                         ▼                                                    │
│  ╔═══════════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                      CLI EXECUTION LAYER                                               ║  │
│  ║                                                                                        ║  │
│  ║  ┌─────────────────────────────────────────────────────────────────────────────────┐ ║  │
│  ║  │  AGENTS EXECUTE ALL CLI COMMANDS - USERS NEVER TOUCH TERMINAL                   │ ║  │
│  ║  │                                                                                  │ ║  │
│  ║  │  Git │ Docker │ Python │ Node │ pip │ npm │ pytest │ ruff │ kubectl │ aws      │ ║  │
│  ║  │  cargo │ go │ terraform │ ansible │ make │ cmake │ gradle │ maven │ yarn      │ ║  │
│  ║  └─────────────────────────────────────────────────────────────────────────────────┘ ║  │
│  ║                                                                                        ║  │
│  ║  ┌─────────────────────────────────────────────────────────────────────────────────┐ ║  │
│  ║  │  ERROR RECOVERY: Auto-detect errors → Auto-fix → Retry → Learn from failures   │ ║  │
│  ║  └─────────────────────────────────────────────────────────────────────────────────┘ ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════════════════╝  │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Complete Package Dependencies

```toml
# pyproject.toml - Full dependencies including enhanced tools

[project.optional-dependencies]
# Voice I/O
voice = [
    "transformers>=4.40.0",          # For GLM-ASR
    "torch>=2.0.0",                  # PyTorch
    "torchaudio>=2.0.0",             # Audio processing
    "sounddevice>=0.4.6",            # Audio input/output
    "soundfile>=0.12.0",             # Audio files
    "webrtcvad>=2.0.10",             # Voice activity detection
    "piper-tts>=1.2.0",              # Piper TTS
    "onnxruntime>=1.15.0",           # ONNX runtime
    # "onnxruntime-gpu>=1.15.0",     # GPU acceleration (optional)
]

# Memory & Learning
memory = [
    "mem0ai>=0.1.13",                # Mem0 memory
    "chromadb>=0.4.0",               # Vector store
    "sentence-transformers>=2.2.0",  # Embeddings
]

# LLM Routing
llm = [
    "litellm>=1.40.0",               # Unified LLM proxy
    "langchain>=0.1.0",              # LangChain
    "langchain-anthropic>=0.1.0",    # Claude
    "langchain-openai>=0.1.0",       # OpenAI
    "langchain-ollama>=0.1.0",       # Ollama
]

# Web Tools
web = [
    "firecrawl-py>=0.0.16",          # Firecrawl
    "browser-use>=0.1.0",            # Browser-Use
    "playwright>=1.40.0",            # Browser automation backend
]

# Agent Frameworks
agents = [
    "crewai>=0.51.0",                # CrewAI
    "crewai-tools>=0.4.0",           # CrewAI tools
    "langgraph>=0.0.40",             # LangGraph
    "semantic-kernel>=1.27.0",       # Microsoft SK
    "pyautogen>=0.2.0",              # AutoGen
]

# Full installation
all = [
    "ai-project-synthesizer[voice,memory,llm,web,agents]",
]
```

---

## 📋 Implementation Checklist

### Phase 1: Foundation + Voice (Weeks 1-3)

- [ ] **CLI Executor**
  - [ ] PowerShell/Bash command execution
  - [ ] Error detection and pattern matching
  - [ ] Auto-recovery patterns
  
- [ ] **Voice Input (GLM-ASR)**
  - [ ] Model download and setup
  - [ ] Audio pipeline (mic → transcription)
  - [ ] Intent parser
  
- [ ] **Voice Output (Piper TTS)**
  - [ ] Voice model setup (en_US-lessac-medium)
  - [ ] Real-time synthesis
  - [ ] Agent feedback integration

### Phase 2: Memory + LLM (Weeks 4-5)

- [ ] **Mem0 Integration**
  - [ ] Memory extraction setup
  - [ ] ChromaDB vector store
  - [ ] User preferences tracking
  - [ ] Project context memory
  
- [ ] **LiteLLM Router**
  - [ ] Provider configuration
  - [ ] Smart routing rules
  - [ ] Cost tracking
  - [ ] Fallback chains

### Phase 3: Agent Frameworks (Weeks 6-7)

- [ ] **Framework Integration**
  - [ ] CrewAI setup
  - [ ] LangGraph setup
  - [ ] Microsoft Agent Framework
  - [ ] Framework router

- [ ] **Specialist Agents**
  - [ ] 12 core agents
  - [ ] Research agent (Firecrawl)
  - [ ] Browser agent (Browser-Use)

### Phase 4: Polish + Production (Weeks 8-10)

- [ ] **Web Tools**
  - [ ] Firecrawl integration
  - [ ] Browser-Use integration
  - [ ] Rate limiting
  
- [ ] **Testing & Documentation**
  - [ ] 80%+ test coverage
  - [ ] API documentation
  - [ ] User guides

---

## 🎯 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Voice Accuracy | 95%+ | Test transcription |
| TTS Latency | <200ms | Time to first audio |
| Memory Recall | 90%+ | Relevant context retrieval |
| LLM Cost Savings | 80% local | Track API calls |
| Error Recovery | 90%+ | Auto-fix success rate |
| Web Scraping | 95% success | Firecrawl completion |
| Browser Tasks | 85% success | Browser-Use completion |

---

## 📚 Additional Resources

- **Piper TTS Voices**: https://huggingface.co/rhasspy/piper-voices
- **Mem0 Documentation**: https://docs.mem0.ai
- **LiteLLM Documentation**: https://docs.litellm.ai
- **Firecrawl Documentation**: https://docs.firecrawl.dev
- **Browser-Use Documentation**: https://github.com/browser-use/browser-use

---

*Document Version: 2.0*
*Last Updated: December 2024*
*Status: Complete Specification*
