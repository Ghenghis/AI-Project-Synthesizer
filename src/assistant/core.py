"""
AI Project Synthesizer - Conversational Assistant Core

The intelligent assistant that:
1. Talks to users naturally via voice AND text (always both)
2. Asks clarifying questions to understand what users need
3. Uses the best available LLM for thinking
4. Searches across platforms to find solutions
5. Synthesizes projects and generates code
6. Voice can be toggled on/off

This is the BRAIN that makes everything useful.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum

from src.core.config import get_settings
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class AssistantState(str, Enum):
    """Current state of the assistant."""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    WAITING_FOR_INPUT = "waiting_for_input"
    EXECUTING = "executing"


class TaskType(str, Enum):
    """Types of tasks the assistant can help with."""
    SEARCH = "search"           # Find projects/code/datasets
    ANALYZE = "analyze"         # Analyze a repository
    SYNTHESIZE = "synthesize"   # Combine multiple projects
    GENERATE = "generate"       # Generate new code
    EXPLAIN = "explain"         # Explain code/concepts
    DEBUG = "debug"             # Help debug issues
    CHAT = "chat"               # General conversation


@dataclass
class Message:
    """A message in the conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float = 0.0
    voice_audio: Optional[bytes] = None  # Audio if voice enabled
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskContext:
    """Context for the current task."""
    task_type: TaskType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    clarifications_needed: List[str] = field(default_factory=list)
    clarifications_received: Dict[str, str] = field(default_factory=dict)
    results: Any = None
    completed: bool = False


@dataclass
class AssistantConfig:
    """Configuration for the assistant."""
    voice_enabled: bool = True
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    auto_speak: bool = True  # Automatically speak responses
    thinking_model: str = "auto"  # auto = best available
    max_clarifications: int = 3
    personality: str = "helpful"  # helpful, concise, detailed


class ConversationalAssistant:
    """
    The main conversational AI assistant.

    Features:
    - Natural language understanding
    - Voice + text output (always both)
    - Clarifying questions for ambiguous requests
    - Multi-step task completion
    - Context-aware responses

    Example:
        assistant = ConversationalAssistant()

        # Start conversation
        response = await assistant.chat("I want to build a chatbot")
        # Assistant asks: "What kind of chatbot? Web-based, Discord, Telegram?"

        response = await assistant.chat("Discord bot with AI")
        # Assistant asks: "Should it use a local LLM or cloud API?"

        response = await assistant.chat("Local LLM")
        # Assistant: "I found these projects that could help..."
    """

    def __init__(self, config: Optional[AssistantConfig] = None):
        """Initialize the assistant."""
        self.config = config or AssistantConfig()
        self.state = AssistantState.IDLE
        self.conversation: List[Message] = []
        self.current_task: Optional[TaskContext] = None

        # Initialize components lazily
        self._llm = None
        self._voice = None
        self._search = None

        # Callbacks for UI integration
        self._on_state_change: Optional[Callable] = None
        self._on_message: Optional[Callable] = None
        self._on_voice_start: Optional[Callable] = None
        self._on_voice_end: Optional[Callable] = None

        self._init_system_prompt()

    def _init_system_prompt(self):
        """Initialize the system prompt."""
        self.system_prompt = """You are an AI assistant for the AI Project Synthesizer.
Your job is to help users find, analyze, and combine code projects.

IMPORTANT BEHAVIORS:
1. Always ask clarifying questions if the request is ambiguous
2. Break complex tasks into steps and confirm each step
3. Be conversational and helpful
4. When searching, explain what you're looking for and why
5. Provide actionable recommendations

CAPABILITIES:
- Search GitHub, HuggingFace, and Kaggle for projects
- Analyze repositories for quality and compatibility
- Synthesize multiple projects into one
- Generate documentation and code
- Explain technical concepts

When responding:
- Keep responses concise but informative
- Use bullet points for lists
- Ask ONE clarifying question at a time
- Confirm understanding before executing tasks"""

    async def _get_llm(self):
        """Get or initialize LLM client."""
        if self._llm is None:
            get_settings()

            # Try LM Studio first (local)
            try:
                from src.llm.lmstudio_client import LMStudioClient
                self._llm = LMStudioClient()
                self._llm_provider = "lmstudio"
                secure_logger.info("Using LM Studio for assistant")
            except Exception:
                pass

            # Try Ollama
            if self._llm is None:
                try:
                    from src.llm.ollama_client import OllamaClient
                    self._llm = OllamaClient()
                    self._llm_provider = "ollama"
                    secure_logger.info("Using Ollama for assistant")
                except Exception:
                    pass

            # Fallback message
            if self._llm is None:
                secure_logger.warning("No LLM available - using basic responses")

        return self._llm

    async def _get_voice(self):
        """Get or initialize voice client."""
        if self._voice is None and self.config.voice_enabled:
            try:
                from src.voice.elevenlabs_client import ElevenLabsClient
                self._voice = ElevenLabsClient()
                secure_logger.info("Voice enabled with ElevenLabs")
            except Exception as e:
                secure_logger.warning(f"Voice not available: {e}")
        return self._voice

    async def _get_search(self):
        """Get or initialize search client."""
        if self._search is None:
            from src.discovery.unified_search import create_unified_search
            self._search = create_unified_search()
        return self._search

    def set_voice_enabled(self, enabled: bool):
        """Toggle voice on/off."""
        self.config.voice_enabled = enabled
        if not enabled:
            self._voice = None

    async def chat(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and generate response.

        Args:
            user_input: User's message (text)

        Returns:
            Dict with:
            - text: Response text
            - audio: Audio bytes (if voice enabled)
            - state: Current assistant state
            - task: Current task info (if any)
            - actions: Suggested next actions
        """
        self.state = AssistantState.THINKING
        self._notify_state_change()

        # Add user message to conversation
        user_msg = Message(role="user", content=user_input)
        self.conversation.append(user_msg)

        # Analyze intent and generate response
        response_text = await self._generate_response(user_input)

        # Generate voice if enabled
        audio = None
        if self.config.voice_enabled and self.config.auto_speak:
            audio = await self._generate_voice(response_text)

        # Add assistant message
        assistant_msg = Message(
            role="assistant",
            content=response_text,
            voice_audio=audio,
        )
        self.conversation.append(assistant_msg)

        self.state = AssistantState.IDLE
        self._notify_state_change()

        return {
            "text": response_text,
            "audio": audio,
            "state": self.state.value,
            "task": self._get_task_info(),
            "actions": self._get_suggested_actions(),
        }

    async def _generate_response(self, user_input: str) -> str:
        """Generate response using LLM."""
        llm = await self._get_llm()

        if llm is None:
            return await self._generate_basic_response(user_input)

        # Build conversation context
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add recent conversation (last 10 messages)
        for msg in self.conversation[-10:]:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current input
        messages.append({"role": "user", "content": user_input})

        try:
            # Check if this needs clarification or action
            intent = await self._analyze_intent(user_input)

            if intent["needs_clarification"]:
                return intent["clarification_question"]

            if intent["action"]:
                return await self._execute_action(intent)

            # General response - build prompt from messages
            prompt = self.system_prompt + "\n\n"
            for msg in messages[1:]:  # Skip system message (already added)
                prompt += f"{msg['role'].upper()}: {msg['content']}\n"
            prompt += "ASSISTANT: "

            result = await llm.complete(prompt)
            return result.content if hasattr(result, 'content') else str(result)

        except Exception as e:
            secure_logger.error(f"LLM error: {e}")
            return await self._generate_basic_response(user_input)

    async def _analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """Analyze user intent to determine next action."""
        input_lower = user_input.lower()

        # Search intent
        if any(word in input_lower for word in ["find", "search", "look for", "discover"]):
            # Check if we have enough info
            if len(user_input.split()) < 5:
                return {
                    "needs_clarification": True,
                    "clarification_question": self._get_search_clarification(user_input),
                    "action": None,
                }
            return {
                "needs_clarification": False,
                "action": "search",
                "query": user_input,
            }

        # Build/create intent
        if any(word in input_lower for word in ["build", "create", "make", "develop"]):
            if not self.current_task:
                return {
                    "needs_clarification": True,
                    "clarification_question": self._get_build_clarification(user_input),
                    "action": None,
                }

        # Analyze intent
        if any(word in input_lower for word in ["analyze", "review", "check", "evaluate"]):
            if "http" not in input_lower and "github.com" not in input_lower:
                return {
                    "needs_clarification": True,
                    "clarification_question": "Which repository would you like me to analyze? Please provide a URL or name.",
                    "action": None,
                }
            return {
                "needs_clarification": False,
                "action": "analyze",
                "query": user_input,
            }

        # Default: no specific action
        return {
            "needs_clarification": False,
            "action": None,
        }

    def _get_search_clarification(self, user_input: str) -> str:
        """Get clarification question for search."""
        questions = [
            "What type of project are you looking for? (e.g., web app, ML model, data pipeline)",
            "Which platforms should I search? GitHub, HuggingFace, Kaggle, or all?",
            "Any specific programming language preference?",
            "Should I prioritize popular projects (more stars) or recent ones?",
        ]

        # Pick most relevant question based on what's missing
        if "python" not in user_input.lower() and "javascript" not in user_input.lower():
            return questions[2]
        if "github" not in user_input.lower() and "huggingface" not in user_input.lower():
            return questions[1]
        return questions[0]

    def _get_build_clarification(self, user_input: str) -> str:
        """Get clarification question for build requests."""
        input_lower = user_input.lower()

        if "chatbot" in input_lower or "chat" in input_lower:
            return "What platform should the chatbot work on? (Discord, Telegram, Web, CLI)"
        if "api" in input_lower:
            return "What should the API do? What data or functionality should it expose?"
        if "ml" in input_lower or "machine learning" in input_lower:
            return "What kind of ML task? (classification, generation, analysis, etc.)"

        return "Can you describe what you want to build in more detail? What problem should it solve?"

    async def _execute_action(self, intent: Dict[str, Any]) -> str:
        """Execute an action based on intent."""
        action = intent["action"]

        if action == "search":
            return await self._do_search(intent["query"])
        elif action == "analyze":
            return await self._do_analyze(intent["query"])

        return "I'm not sure how to help with that. Can you rephrase?"

    async def _do_search(self, query: str) -> str:
        """Execute a search and format results."""
        self.state = AssistantState.EXECUTING
        self._notify_state_change()

        search = await self._get_search()

        # Determine platforms from query
        platforms = []
        query_lower = query.lower()
        if "github" in query_lower:
            platforms.append("github")
        if "huggingface" in query_lower or "model" in query_lower:
            platforms.append("huggingface")
        if "kaggle" in query_lower or "dataset" in query_lower:
            platforms.append("kaggle")

        if not platforms:
            platforms = None  # Search all

        # Extract search terms (remove platform names)
        search_terms = query
        for word in ["github", "huggingface", "kaggle", "find", "search", "look for"]:
            search_terms = search_terms.lower().replace(word, "").strip()

        result = await search.search(
            query=search_terms,
            platforms=platforms,
            max_results=10,
        )

        if not result.repositories:
            return f"I couldn't find any projects matching '{search_terms}'. Would you like me to try a different search?"

        # Format results
        response = f"I found {len(result.repositories)} projects for '{search_terms}':\n\n"

        for i, repo in enumerate(result.repositories[:5], 1):
            response += f"**{i}. {repo.full_name}** ({repo.platform})\n"
            response += f"   ⭐ {repo.stars:,} stars\n"
            if repo.description:
                desc = repo.description[:100] + "..." if len(repo.description) > 100 else repo.description
                response += f"   {desc}\n"
            response += f"   🔗 {repo.url}\n\n"

        response += "\nWould you like me to:\n"
        response += "- Analyze any of these in detail?\n"
        response += "- Search for something more specific?\n"
        response += "- Find complementary projects to combine with these?"

        return response

    async def _do_analyze(self, query: str) -> str:
        """Analyze a repository."""
        # Extract URL from query
        import re
        url_match = re.search(r'https?://[^\s]+', query)

        if not url_match:
            return "Please provide a repository URL to analyze."

        url = url_match.group()

        return f"I'll analyze {url} for you. This feature is coming soon!\n\nIn the meantime, I can search for similar projects or help you understand what to look for in a repository."

    async def _generate_basic_response(self, user_input: str) -> str:
        """Generate basic response without LLM."""
        input_lower = user_input.lower()

        if any(word in input_lower for word in ["hello", "hi", "hey"]):
            return "Hello! I'm your AI assistant. I can help you find, analyze, and combine code projects. What would you like to do?"

        if "help" in input_lower:
            return """I can help you with:

• **Search** - Find projects on GitHub, HuggingFace, and Kaggle
• **Analyze** - Review a repository's quality and structure
• **Synthesize** - Combine multiple projects into one
• **Generate** - Create new code or documentation

What would you like to do?"""

        if any(word in input_lower for word in ["search", "find"]):
            return await self._do_search(user_input)

        return "I'm here to help! You can ask me to search for projects, analyze repositories, or help you build something. What do you need?"

    async def _generate_voice(self, text: str) -> Optional[bytes]:
        """Generate voice audio for text."""
        voice = await self._get_voice()

        if voice is None:
            return None

        try:
            self.state = AssistantState.SPEAKING
            self._notify_state_change()

            # Clean text for speech (remove markdown)
            clean_text = self._clean_for_speech(text)

            audio = await voice.text_to_speech(
                clean_text,
                voice=self.config.voice_id,
            )

            return audio

        except Exception as e:
            secure_logger.error(f"Voice generation error: {e}")
            return None

    def _clean_for_speech(self, text: str) -> str:
        """Clean text for speech synthesis."""
        import re

        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic
        text = re.sub(r'`([^`]+)`', r'\1', text)        # Code
        text = re.sub(r'#{1,6}\s*', '', text)           # Headers
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
        text = re.sub(r'[•\-]\s*', '', text)            # Bullets
        text = re.sub(r'🔗|⭐|📊', '', text)            # Emojis

        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()

        return text

    def _get_task_info(self) -> Optional[Dict[str, Any]]:
        """Get current task information."""
        if self.current_task is None:
            return None

        return {
            "type": self.current_task.task_type.value,
            "description": self.current_task.description,
            "completed": self.current_task.completed,
            "clarifications_needed": self.current_task.clarifications_needed,
        }

    def _get_suggested_actions(self) -> List[str]:
        """Get suggested next actions."""
        if not self.conversation:
            return ["Search for projects", "Analyze a repository", "Help me build something"]

        last_msg = self.conversation[-1].content.lower()

        if "search" in last_msg or "found" in last_msg:
            return ["Analyze top result", "Search more specifically", "Find complementary projects"]

        if "analyze" in last_msg:
            return ["Search for similar projects", "Generate documentation", "Find alternatives"]

        return ["Search", "Analyze", "Build"]

    def _notify_state_change(self):
        """Notify listeners of state change."""
        if self._on_state_change:
            self._on_state_change(self.state)

    def on_state_change(self, callback: Callable):
        """Register state change callback."""
        self._on_state_change = callback

    def on_message(self, callback: Callable):
        """Register message callback."""
        self._on_message = callback

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "has_audio": msg.voice_audio is not None,
            }
            for msg in self.conversation
        ]

    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation = []
        self.current_task = None


# Singleton instance
_assistant: Optional[ConversationalAssistant] = None


def get_assistant() -> ConversationalAssistant:
    """Get or create the assistant singleton."""
    global _assistant
    if _assistant is None:
        _assistant = ConversationalAssistant()
    return _assistant
