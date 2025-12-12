# 🧠 Memory & Learning System

## Overview

The Memory & Learning System gives the AI agents a **persistent brain** that:
- Remembers user preferences and project history
- Learns from successful patterns
- Improves recommendations over time
- Enables reasoning and planning

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         BRAIN ARCHITECTURE                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      REASONING ENGINE                                │    │
│  │                                                                      │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │    │
│  │  │   PLANNING     │  │   THINKING     │  │   DECIDING     │        │    │
│  │  │                │  │                │  │                │        │    │
│  │  │ • Goal decomp  │  │ • Chain of     │  │ • Option eval  │        │    │
│  │  │ • Task trees   │  │   thought      │  │ • Risk assess  │        │    │
│  │  │ • Scheduling   │  │ • Reflection   │  │ • Selection    │        │    │
│  │  └────────────────┘  └────────────────┘  └────────────────┘        │    │
│  │                              │                                      │    │
│  │                      Cloud LLMs for                                 │    │
│  │                   Complex Reasoning                                 │    │
│  │                  (Claude/GPT-4/Gemini)                             │    │
│  └──────────────────────────────┼──────────────────────────────────────┘    │
│                                 │                                            │
│  ┌──────────────────────────────┼──────────────────────────────────────┐    │
│  │                      MEMORY LAYERS                                   │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │              SHORT-TERM MEMORY (Context)                     │   │    │
│  │  │                                                              │   │    │
│  │  │  • Current conversation                                      │   │    │
│  │  │  • Active task state                                         │   │    │
│  │  │  • Recent tool outputs                                       │   │    │
│  │  │  • Working variables                                         │   │    │
│  │  │                                                              │   │    │
│  │  │  Storage: In-memory (Redis for distributed)                  │   │    │
│  │  │  Retention: Session duration                                 │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │              LONG-TERM MEMORY (Persistent)                   │   │    │
│  │  │                                                              │   │    │
│  │  │  • User preferences          • Project history               │   │    │
│  │  │  • Successful patterns       • Error solutions               │   │    │
│  │  │  • Code snippets             • API configurations            │   │    │
│  │  │                                                              │   │    │
│  │  │  Storage: SQLite (data/memory.db)                           │   │    │
│  │  │  Retention: Permanent                                        │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │              SEMANTIC MEMORY (Vector Store)                  │   │    │
│  │  │                                                              │   │    │
│  │  │  • Code embeddings           • Documentation chunks          │   │    │
│  │  │  • Solution patterns         • Error traces                  │   │    │
│  │  │  • Similar projects          • Best practices                │   │    │
│  │  │                                                              │   │    │
│  │  │  Storage: ChromaDB / Qdrant                                  │   │    │
│  │  │  Search: Semantic similarity                                 │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                 │                                            │
│  ┌──────────────────────────────┼──────────────────────────────────────┐    │
│  │                      LEARNING ENGINE                                 │    │
│  │                                                                      │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │    │
│  │  │   PATTERN      │  │  REINFORCEMENT │  │   KNOWLEDGE    │        │    │
│  │  │   LEARNING     │  │    LEARNING    │  │   DISTILLATION │        │    │
│  │  │                │  │                │  │                │        │    │
│  │  │ • Success      │  │ • Reward from  │  │ • Extract      │        │    │
│  │  │   patterns     │  │   user feedback│  │   patterns     │        │    │
│  │  │ • Failure      │  │ • Optimize     │  │ • Compress     │        │    │
│  │  │   patterns     │  │   decisions    │  │   knowledge    │        │    │
│  │  └────────────────┘  └────────────────┘  └────────────────┘        │    │
│  │                                                                      │    │
│  │  Local LLMs for learning (Ollama/LM Studio)                         │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Memory Schema

### SQLite Schema (data/memory.db)

```sql
-- User preferences
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project history
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT,
    description TEXT,
    tech_stack TEXT,  -- JSON array
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP
);

-- Code patterns (successful solutions)
CREATE TABLE code_patterns (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT NOT NULL,  -- error_fix, feature, optimization
    context TEXT NOT NULL,       -- What problem it solves
    solution TEXT NOT NULL,      -- The code/command
    language TEXT,
    success_count INTEGER DEFAULT 1,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learning events
CREATE TABLE learning_events (
    id INTEGER PRIMARY KEY,
    event_type TEXT NOT NULL,    -- success, failure, feedback
    task_description TEXT,
    outcome TEXT,
    reward REAL,                 -- -1 to 1
    metadata TEXT,               -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation summaries
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    summary TEXT NOT NULL,
    key_decisions TEXT,          -- JSON array
    user_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent decisions (for learning)
CREATE TABLE agent_decisions (
    id INTEGER PRIMARY KEY,
    agent_type TEXT NOT NULL,
    decision_context TEXT NOT NULL,
    options_considered TEXT,     -- JSON array
    chosen_option TEXT NOT NULL,
    reasoning TEXT,
    outcome TEXT,
    reward REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Implementation

**File: `src/core/brain.py`**

```python
"""
Brain - Central memory and reasoning system.

Coordinates:
- Short-term memory (context)
- Long-term memory (SQLite)
- Semantic memory (Vector store)
- Reasoning engine (LLM)
- Learning engine (RL)
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Vector store
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from src.core.config import get_settings
from src.llm.router import LLMRouter

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Entry in memory."""
    
    key: str
    value: Any
    category: str
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5  # 0-1, for pruning


@dataclass 
class ReasoningContext:
    """Context for reasoning tasks."""
    
    goal: str
    constraints: list[str] = field(default_factory=list)
    relevant_memories: list[MemoryEntry] = field(default_factory=list)
    previous_attempts: list[dict] = field(default_factory=list)


class Brain:
    """
    Central brain coordinating memory and reasoning.
    """
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.settings = get_settings()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        self._init_vector_store()
        self._init_llm_router()
        
        # Short-term memory (in-memory)
        self.short_term: dict[str, MemoryEntry] = {}
        self.context_window: list[dict] = []
    
    def _init_database(self) -> None:
        """Initialize SQLite database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT,
                description TEXT,
                tech_stack TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS code_patterns (
                id INTEGER PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                context TEXT NOT NULL,
                solution TEXT NOT NULL,
                language TEXT,
                success_count INTEGER DEFAULT 1,
                failure_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS learning_events (
                id INTEGER PRIMARY KEY,
                event_type TEXT NOT NULL,
                task_description TEXT,
                outcome TEXT,
                reward REAL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id INTEGER PRIMARY KEY,
                agent_type TEXT NOT NULL,
                decision_context TEXT NOT NULL,
                options_considered TEXT,
                chosen_option TEXT NOT NULL,
                reasoning TEXT,
                outcome TEXT,
                reward REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
    
    def _init_vector_store(self) -> None:
        """Initialize ChromaDB vector store."""
        if not CHROMA_AVAILABLE:
            logger.warning("ChromaDB not available - semantic search disabled")
            self.vector_store = None
            return
        
        self.chroma_client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="data/chroma",
            anonymized_telemetry=False,
        ))
        
        # Create collections
        self.code_collection = self.chroma_client.get_or_create_collection(
            name="code_patterns",
            metadata={"hnsw:space": "cosine"},
        )
        
        self.docs_collection = self.chroma_client.get_or_create_collection(
            name="documentation",
            metadata={"hnsw:space": "cosine"},
        )
    
    def _init_llm_router(self) -> None:
        """Initialize LLM router for reasoning."""
        self.llm_router = LLMRouter()
    
    # ========== Short-Term Memory ==========
    
    def remember_short_term(self, key: str, value: Any, category: str = "general") -> None:
        """Store in short-term memory."""
        self.short_term[key] = MemoryEntry(
            key=key,
            value=value,
            category=category,
        )
    
    def recall_short_term(self, key: str) -> Optional[Any]:
        """Recall from short-term memory."""
        entry = self.short_term.get(key)
        return entry.value if entry else None
    
    def add_to_context(self, role: str, content: str) -> None:
        """Add message to context window."""
        self.context_window.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Trim context if too long
        if len(self.context_window) > 50:
            self.context_window = self.context_window[-50:]
    
    # ========== Long-Term Memory ==========
    
    def store_preference(self, key: str, value: Any, category: str = "general") -> None:
        """Store user preference."""
        self.conn.execute("""
            INSERT INTO user_preferences (key, value, category)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
        """, (key, json.dumps(value), category))
        self.conn.commit()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        cursor = self.conn.execute(
            "SELECT value FROM user_preferences WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        return json.loads(row["value"]) if row else default
    
    def store_pattern(
        self,
        pattern_type: str,
        context: str,
        solution: str,
        language: Optional[str] = None,
    ) -> None:
        """Store successful code pattern."""
        # Check if similar pattern exists
        cursor = self.conn.execute("""
            SELECT id FROM code_patterns 
            WHERE pattern_type = ? AND context = ?
        """, (pattern_type, context))
        
        existing = cursor.fetchone()
        
        if existing:
            self.conn.execute("""
                UPDATE code_patterns 
                SET success_count = success_count + 1
                WHERE id = ?
            """, (existing["id"],))
        else:
            self.conn.execute("""
                INSERT INTO code_patterns (pattern_type, context, solution, language)
                VALUES (?, ?, ?, ?)
            """, (pattern_type, context, solution, language))
        
        self.conn.commit()
        
        # Also store in vector DB for semantic search
        if self.vector_store:
            self.code_collection.add(
                documents=[f"{context}\n\n{solution}"],
                metadatas=[{"type": pattern_type, "language": language or ""}],
                ids=[f"pattern_{datetime.now().timestamp()}"],
            )
    
    def find_similar_patterns(self, query: str, n_results: int = 5) -> list[dict]:
        """Find similar patterns using semantic search."""
        if not self.vector_store:
            return []
        
        results = self.code_collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        
        patterns = []
        for i, doc in enumerate(results["documents"][0]):
            patterns.append({
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        
        return patterns
    
    # ========== Reasoning Engine ==========
    
    async def reason(
        self,
        goal: str,
        context: Optional[ReasoningContext] = None,
        use_cloud_llm: bool = True,
    ) -> dict[str, Any]:
        """
        Perform reasoning to achieve a goal.
        
        Uses chain-of-thought prompting with cloud LLMs
        for complex reasoning tasks.
        """
        # Build reasoning prompt
        prompt = self._build_reasoning_prompt(goal, context)
        
        # Select LLM (cloud for complex reasoning)
        if use_cloud_llm:
            model = self.settings.reasoning_model or "claude-sonnet-4-20250514"
        else:
            model = self.settings.ollama_model or "llama3.1:8b"
        
        # Execute reasoning
        response = await self.llm_router.complete(
            prompt=prompt,
            model=model,
            temperature=0.7,
            max_tokens=4096,
        )
        
        # Parse reasoning output
        return self._parse_reasoning_output(response)
    
    def _build_reasoning_prompt(
        self,
        goal: str,
        context: Optional[ReasoningContext] = None,
    ) -> str:
        """Build chain-of-thought reasoning prompt."""
        
        prompt = f"""You are an expert AI reasoning engine. Think step-by-step to achieve the goal.

## Goal
{goal}

"""
        
        if context:
            if context.constraints:
                prompt += "## Constraints\n"
                for c in context.constraints:
                    prompt += f"- {c}\n"
                prompt += "\n"
            
            if context.relevant_memories:
                prompt += "## Relevant Knowledge\n"
                for mem in context.relevant_memories[:5]:
                    prompt += f"- {mem.key}: {mem.value}\n"
                prompt += "\n"
            
            if context.previous_attempts:
                prompt += "## Previous Attempts\n"
                for attempt in context.previous_attempts[-3:]:
                    prompt += f"- Tried: {attempt.get('action')}, Result: {attempt.get('result')}\n"
                prompt += "\n"
        
        prompt += """## Instructions
1. Analyze the goal and break it into steps
2. Consider constraints and previous attempts
3. Reason through each step
4. Provide your plan

## Your Reasoning (think step by step)
"""
        
        return prompt
    
    def _parse_reasoning_output(self, response: str) -> dict[str, Any]:
        """Parse reasoning output into structured format."""
        return {
            "reasoning": response,
            "steps": self._extract_steps(response),
            "decision": self._extract_decision(response),
        }
    
    def _extract_steps(self, text: str) -> list[str]:
        """Extract numbered steps from reasoning."""
        import re
        steps = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)', text, re.DOTALL)
        return [s.strip() for s in steps]
    
    def _extract_decision(self, text: str) -> Optional[str]:
        """Extract final decision from reasoning."""
        import re
        decision_match = re.search(
            r'(?:decision|conclusion|recommend|final|plan):\s*(.+?)(?:\n\n|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        return decision_match.group(1).strip() if decision_match else None
    
    # ========== Learning Engine ==========
    
    def record_learning_event(
        self,
        event_type: str,
        task_description: str,
        outcome: str,
        reward: float,
        metadata: Optional[dict] = None,
    ) -> None:
        """Record event for learning."""
        self.conn.execute("""
            INSERT INTO learning_events (event_type, task_description, outcome, reward, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (event_type, task_description, outcome, reward, json.dumps(metadata or {})))
        self.conn.commit()
    
    def record_decision(
        self,
        agent_type: str,
        context: str,
        options: list[str],
        chosen: str,
        reasoning: str,
    ) -> int:
        """Record agent decision for later learning."""
        cursor = self.conn.execute("""
            INSERT INTO agent_decisions 
            (agent_type, decision_context, options_considered, chosen_option, reasoning)
            VALUES (?, ?, ?, ?, ?)
        """, (agent_type, context, json.dumps(options), chosen, reasoning))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_decision_outcome(self, decision_id: int, outcome: str, reward: float) -> None:
        """Update decision with outcome and reward."""
        self.conn.execute("""
            UPDATE agent_decisions 
            SET outcome = ?, reward = ?
            WHERE id = ?
        """, (outcome, reward, decision_id))
        self.conn.commit()
    
    async def learn_from_feedback(self, feedback: str, task_context: str) -> None:
        """Learn from user feedback."""
        # Determine reward from feedback
        reward = await self._analyze_feedback(feedback)
        
        # Record learning event
        self.record_learning_event(
            event_type="user_feedback",
            task_description=task_context,
            outcome=feedback,
            reward=reward,
        )
        
        # If positive, store as pattern
        if reward > 0.5:
            self.store_preference(
                f"feedback_{datetime.now().timestamp()}",
                {"context": task_context, "feedback": feedback},
                category="learned",
            )
    
    async def _analyze_feedback(self, feedback: str) -> float:
        """Analyze feedback to determine reward (-1 to 1)."""
        prompt = f"""Analyze this user feedback and rate it from -1 (very negative) to 1 (very positive).

Feedback: {feedback}

Respond with only a number between -1 and 1."""
        
        response = await self.llm_router.complete(
            prompt=prompt,
            model=self.settings.ollama_model or "llama3.1:8b",
            temperature=0,
            max_tokens=10,
        )
        
        try:
            return float(response.strip())
        except ValueError:
            return 0.0
```

---

## Reinforcement Learning Component

**File: `src/core/reinforcement_learning.py`**

```python
"""
Reinforcement Learning - Optimizes agent decisions over time.

Uses reward signals from:
- User feedback (explicit)
- Task success/failure (implicit)
- Code quality metrics (automated)
"""

import json
import logging
import random
from dataclasses import dataclass
from typing import Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class State:
    """Environment state for RL."""
    
    task_type: str          # code, test, deploy, docs
    complexity: str         # simple, medium, complex
    context_features: dict  # Extracted features


@dataclass
class Action:
    """Possible action."""
    
    name: str
    parameters: dict


class ReinforcementLearner:
    """
    Simple Q-learning based decision optimizer.
    
    Learns which actions work best for different states.
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        exploration_rate: float = 0.2,
    ):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        
        # Q-table: state -> action -> value
        self.q_table: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # Action history for learning
        self.episode_history: list[tuple] = []
    
    def _state_key(self, state: State) -> str:
        """Convert state to string key."""
        return f"{state.task_type}:{state.complexity}"
    
    def select_action(
        self,
        state: State,
        available_actions: list[Action],
    ) -> Action:
        """
        Select action using epsilon-greedy policy.
        
        Balances exploration vs exploitation.
        """
        state_key = self._state_key(state)
        
        # Exploration: random action
        if random.random() < self.epsilon:
            return random.choice(available_actions)
        
        # Exploitation: best known action
        action_values = self.q_table[state_key]
        
        if not action_values:
            return random.choice(available_actions)
        
        best_action_name = max(action_values, key=action_values.get)
        
        for action in available_actions:
            if action.name == best_action_name:
                return action
        
        return random.choice(available_actions)
    
    def record_step(
        self,
        state: State,
        action: Action,
        reward: float,
        next_state: Optional[State] = None,
    ) -> None:
        """Record step for learning."""
        self.episode_history.append((state, action, reward, next_state))
    
    def learn_from_episode(self) -> None:
        """Update Q-values from episode history."""
        
        # Work backwards through history
        future_reward = 0
        
        for state, action, reward, next_state in reversed(self.episode_history):
            state_key = self._state_key(state)
            action_name = action.name
            
            # Get current Q-value
            current_q = self.q_table[state_key][action_name]
            
            # Calculate target
            if next_state:
                next_key = self._state_key(next_state)
                max_next_q = max(self.q_table[next_key].values()) if self.q_table[next_key] else 0
                target = reward + self.gamma * max_next_q
            else:
                target = reward
            
            # Update Q-value
            new_q = current_q + self.lr * (target - current_q)
            self.q_table[state_key][action_name] = new_q
        
        # Clear history
        self.episode_history = []
    
    def get_best_actions(self, state: State, top_k: int = 3) -> list[tuple[str, float]]:
        """Get best actions for a state."""
        state_key = self._state_key(state)
        action_values = self.q_table[state_key]
        
        sorted_actions = sorted(action_values.items(), key=lambda x: x[1], reverse=True)
        return sorted_actions[:top_k]
    
    def save(self, path: str) -> None:
        """Save Q-table to file."""
        with open(path, "w") as f:
            json.dump(dict(self.q_table), f, indent=2)
    
    def load(self, path: str) -> None:
        """Load Q-table from file."""
        try:
            with open(path) as f:
                data = json.load(f)
                self.q_table = defaultdict(lambda: defaultdict(float), {
                    k: defaultdict(float, v) for k, v in data.items()
                })
        except FileNotFoundError:
            logger.info("No saved Q-table found, starting fresh")
```

---

## Knowledge Distillation

**File: `src/core/knowledge_distillation.py`**

```python
"""
Knowledge Distillation - Compress learned patterns.

Periodically analyzes stored patterns and:
- Removes duplicates
- Generalizes specific patterns
- Creates reusable templates
"""

import logging
from typing import Any
from dataclasses import dataclass
import sqlite3

from src.llm.router import LLMRouter
from src.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class DistilledKnowledge:
    """Compressed, generalized knowledge."""
    
    category: str
    pattern: str
    applicability: str  # When to use
    confidence: float
    source_count: int   # How many patterns it was derived from


class KnowledgeDistiller:
    """
    Compresses and generalizes stored patterns.
    """
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.settings = get_settings()
        self.llm_router = LLMRouter()
    
    async def distill_patterns(self, pattern_type: str) -> list[DistilledKnowledge]:
        """
        Distill patterns of a given type into general knowledge.
        """
        # Get all patterns of this type
        cursor = self.conn.execute("""
            SELECT context, solution, language, success_count
            FROM code_patterns
            WHERE pattern_type = ?
            ORDER BY success_count DESC
            LIMIT 100
        """, (pattern_type,))
        
        patterns = cursor.fetchall()
        
        if len(patterns) < 3:
            return []
        
        # Group similar patterns
        groups = await self._group_similar(patterns)
        
        # Distill each group
        distilled = []
        for group in groups:
            knowledge = await self._distill_group(pattern_type, group)
            if knowledge:
                distilled.append(knowledge)
        
        return distilled
    
    async def _group_similar(self, patterns: list) -> list[list]:
        """Group similar patterns together."""
        
        # Use LLM to cluster patterns
        pattern_texts = [f"Context: {p['context']}\nSolution: {p['solution']}" for p in patterns]
        
        prompt = f"""Group these {len(patterns)} code patterns into clusters of similar solutions.

Patterns:
{chr(10).join(f'{i+1}. {t[:200]}...' for i, t in enumerate(pattern_texts))}

Respond with groups as JSON: {{"groups": [[1,2,3], [4,5], ...]}}
Group by similar problem/solution type, not just language."""
        
        response = await self.llm_router.complete(
            prompt=prompt,
            model=self.settings.ollama_model or "llama3.1:8b",
            temperature=0,
        )
        
        try:
            import json
            result = json.loads(response)
            groups = []
            for indices in result.get("groups", []):
                group = [patterns[i-1] for i in indices if 0 < i <= len(patterns)]
                if group:
                    groups.append(group)
            return groups
        except Exception:
            # Fallback: return all as one group
            return [patterns]
    
    async def _distill_group(
        self,
        pattern_type: str,
        group: list,
    ) -> Optional[DistilledKnowledge]:
        """Distill a group of patterns into generalized knowledge."""
        
        if not group:
            return None
        
        # Build prompt
        examples = "\n\n".join([
            f"Example {i+1}:\nContext: {p['context']}\nSolution: {p['solution']}"
            for i, p in enumerate(group[:5])
        ])
        
        prompt = f"""Analyze these {len(group)} similar code patterns and extract the general knowledge.

{examples}

Create a generalized pattern that:
1. Captures the common solution approach
2. Uses placeholders for specific values
3. Explains when to apply this pattern

Respond in this format:
PATTERN: (the generalized solution template)
APPLICABILITY: (when to use this pattern)
CONFIDENCE: (0.0-1.0, how reliable is this pattern)"""
        
        response = await self.llm_router.complete(
            prompt=prompt,
            model=self.settings.ollama_model or "llama3.1:8b",
            temperature=0,
        )
        
        # Parse response
        lines = response.strip().split("\n")
        pattern = ""
        applicability = ""
        confidence = 0.5
        
        for line in lines:
            if line.startswith("PATTERN:"):
                pattern = line.replace("PATTERN:", "").strip()
            elif line.startswith("APPLICABILITY:"):
                applicability = line.replace("APPLICABILITY:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    pass
        
        if not pattern:
            return None
        
        return DistilledKnowledge(
            category=pattern_type,
            pattern=pattern,
            applicability=applicability,
            confidence=confidence,
            source_count=len(group),
        )
    
    def store_distilled(self, knowledge: DistilledKnowledge) -> None:
        """Store distilled knowledge."""
        self.conn.execute("""
            INSERT INTO code_patterns (pattern_type, context, solution, success_count)
            VALUES (?, ?, ?, ?)
        """, (
            f"distilled_{knowledge.category}",
            knowledge.applicability,
            knowledge.pattern,
            knowledge.source_count,
        ))
        self.conn.commit()
```

---

## LLM Routing Strategy

When to use which LLM:

| Task | Recommended LLM | Reason |
|------|-----------------|--------|
| Complex reasoning | Claude/GPT-4 | Best chain-of-thought |
| Code generation | Claude/GPT-4 | Best code quality |
| Quick classification | Ollama (local) | Fast, low latency |
| Pattern matching | Ollama (local) | Adequate quality, free |
| Embedding generation | Ollama (local) | Free, good enough |
| Long context analysis | Claude | 200k context window |
| Cost-sensitive tasks | Ollama/LM Studio | Zero API cost |

**File: `src/llm/smart_router.py`**

```python
"""
Smart LLM Router - Selects optimal LLM for each task.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

from src.core.config import get_settings


class TaskComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class TaskType(Enum):
    REASONING = "reasoning"
    CODE_GEN = "code_generation"
    CLASSIFICATION = "classification"
    EMBEDDING = "embedding"
    SUMMARIZATION = "summarization"
    CHAT = "chat"


@dataclass
class RoutingDecision:
    """LLM routing decision."""
    
    provider: str        # ollama, lmstudio, anthropic, openai
    model: str
    reason: str
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None


class SmartRouter:
    """Routes tasks to optimal LLM."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def route(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        context_length: int = 0,
        require_fast: bool = False,
        require_cheap: bool = False,
    ) -> RoutingDecision:
        """
        Select optimal LLM based on task requirements.
        """
        
        # Fast + cheap = always local
        if require_fast and require_cheap:
            return RoutingDecision(
                provider="ollama",
                model=self.settings.ollama_model or "llama3.1:8b",
                reason="Fast and cheap requirement - using local LLM",
            )
        
        # Complex reasoning = cloud
        if task_type == TaskType.REASONING and complexity == TaskComplexity.COMPLEX:
            return RoutingDecision(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                reason="Complex reasoning requires best chain-of-thought capability",
                fallback_provider="openai",
                fallback_model="gpt-4o",
            )
        
        # Code generation = cloud (for quality)
        if task_type == TaskType.CODE_GEN and complexity != TaskComplexity.SIMPLE:
            return RoutingDecision(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                reason="Code generation benefits from larger model",
                fallback_provider="ollama",
                fallback_model="deepseek-coder:33b",
            )
        
        # Long context = Claude
        if context_length > 32000:
            return RoutingDecision(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                reason="Long context requires Claude's 200k window",
            )
        
        # Embeddings = always local
        if task_type == TaskType.EMBEDDING:
            return RoutingDecision(
                provider="ollama",
                model="nomic-embed-text",
                reason="Embeddings are efficient locally",
            )
        
        # Classification = local (fast enough)
        if task_type == TaskType.CLASSIFICATION:
            return RoutingDecision(
                provider="ollama",
                model=self.settings.ollama_model or "llama3.1:8b",
                reason="Classification is fast locally",
                fallback_provider="lmstudio",
                fallback_model="local-model",
            )
        
        # Default = local for cost
        return RoutingDecision(
            provider="ollama",
            model=self.settings.ollama_model or "llama3.1:8b",
            reason="Default to local for cost efficiency",
            fallback_provider="anthropic",
            fallback_model="claude-sonnet-4-20250514",
        )
```

---

## Summary

The Memory & Learning System provides:

1. **Short-Term Memory**: Context window, working state
2. **Long-Term Memory**: SQLite for preferences, patterns, history
3. **Semantic Memory**: ChromaDB for similarity search
4. **Reasoning Engine**: Chain-of-thought with cloud LLMs
5. **Learning Engine**: RL for decision optimization
6. **Knowledge Distillation**: Pattern compression and generalization
7. **Smart Routing**: Optimal LLM selection per task

---

## Next Document

See **[IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)** for the phased action plan.
