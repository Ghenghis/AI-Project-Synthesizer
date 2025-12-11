"""
AI Project Synthesizer - Voice Agent

AI-powered voice agent for:
- Continuous voice interaction (no pause limits)
- Speech-to-text processing
- Text-to-speech responses
- Voice command execution
- Auto-continue conversations
"""

from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from src.agents.base import BaseAgent, AgentConfig, AgentTool
from src.core.security import get_secure_logger
from src.core.settings_manager import get_settings_manager

secure_logger = get_secure_logger(__name__)


@dataclass
class VoiceState:
    """Voice agent state."""
    is_listening: bool = False
    is_speaking: bool = False
    is_processing: bool = False
    current_text: str = ""
    last_response: str = ""
    auto_continue: bool = True


class VoiceAgent(BaseAgent):
    """
    Voice agent for speech interactions.

    Features:
    - No pause limits (continuous listening)
    - Hotkey activation
    - Auto-speak responses
    - Voice command execution
    - Multi-voice support
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        config = config or AgentConfig(
            name="voice_agent",
            description="Handles voice interactions without pause limits",
            auto_continue=True,
            max_iterations=100,  # High for continuous conversation
            enable_voice=True,
        )
        super().__init__(config)
        self._state = VoiceState()
        self._voice_manager = None
        self._on_transcription: Optional[Callable] = None
        self._on_response: Optional[Callable] = None
        self._setup_tools()

    def _setup_tools(self):
        """Set up voice tools."""
        self.register_tool(AgentTool(
            name="speak",
            description="Speak text aloud",
            func=self._speak,
            parameters={
                "text": {"type": "string", "description": "Text to speak"},
                "voice": {"type": "string", "description": "Voice to use"},
            },
        ))

        self.register_tool(AgentTool(
            name="listen",
            description="Listen for voice input",
            func=self._listen,
            parameters={
                "timeout": {"type": "integer", "description": "Listen timeout (0=unlimited)"},
            },
        ))

        self.register_tool(AgentTool(
            name="execute_command",
            description="Execute a voice command",
            func=self._execute_command,
            parameters={
                "command": {"type": "string", "description": "Command to execute"},
            },
        ))

    async def _get_voice_manager(self):
        """Get voice manager."""
        if self._voice_manager is None:
            from src.voice import get_voice_manager
            self._voice_manager = get_voice_manager()
        return self._voice_manager

    async def _speak(self, text: str, voice: Optional[str] = None) -> Dict[str, Any]:
        """Speak text aloud."""
        self._state.is_speaking = True

        try:
            manager = await self._get_voice_manager()
            settings = get_settings_manager().settings.voice

            voice = voice or settings.voice_id

            if settings.stream_audio:
                await manager.speak_fast(text, voice)
            else:
                await manager.speak(text, voice)

            self._state.last_response = text

            return {"success": True, "text": text, "voice": voice}

        except Exception as e:
            secure_logger.error(f"Speech failed: {e}")
            return {"success": False, "error": str(e)}

        finally:
            self._state.is_speaking = False

    async def _listen(self, timeout: int = 0) -> Dict[str, Any]:
        """Listen for voice input (no pause limits when timeout=0)."""
        self._state.is_listening = True

        try:
            # Get settings
            settings = get_settings_manager().settings.voice

            # Use configured timeout or unlimited
            actual_timeout = timeout if timeout > 0 else settings.max_recording_duration

            # For now, return placeholder - would integrate with speech recognition
            # In production, this would use whisper, vosk, or cloud STT

            return {
                "success": True,
                "listening": True,
                "timeout": actual_timeout,
                "pause_detection": settings.pause_detection,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

        finally:
            self._state.is_listening = False

    async def _execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a voice command."""
        command_lower = command.lower().strip()

        # Built-in commands
        if command_lower in ["stop", "cancel", "nevermind"]:
            return {"action": "cancel", "success": True}

        if command_lower in ["pause", "wait"]:
            return {"action": "pause", "success": True}

        if command_lower in ["continue", "go on", "resume"]:
            return {"action": "continue", "success": True}

        if command_lower.startswith("search for "):
            query = command_lower.replace("search for ", "")
            return {"action": "search", "query": query, "success": True}

        if command_lower.startswith("create ") or command_lower.startswith("build "):
            idea = command_lower.replace("create ", "").replace("build ", "")
            return {"action": "synthesize", "idea": idea, "success": True}

        # Default: treat as chat
        return {"action": "chat", "message": command, "success": True}

    async def _execute_step(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a voice interaction step."""
        llm = await self._get_llm()
        settings = get_settings_manager().settings.voice

        # Build conversation context
        history = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in self._memory[-10:]  # Last 10 messages
        ])

        prompt = f"""You are a helpful voice assistant. Respond naturally and concisely.

Conversation history:
{history}

User said: {task}

Respond in a conversational way. Keep responses brief for voice output.
If the user wants to perform an action (search, create project, etc.),
indicate the action clearly.

Response:"""

        response = await llm.complete(prompt)
        response = response.strip()

        # Add to memory
        self.add_memory("user", task)
        self.add_memory("assistant", response)

        # Speak response if enabled
        if settings.auto_speak_responses:
            await self._speak(response)

        # Notify callback
        if self._on_response:
            try:
                self._on_response(response)
            except Exception:
                pass

        # Check for action commands in response
        action = None
        if "search" in task.lower():
            action = "search"
        elif "create" in task.lower() or "build" in task.lower():
            action = "synthesize"

        return {
            "action": action or "chat",
            "input": task,
            "output": response,
            "spoken": settings.auto_speak_responses,
            "complete": not self._state.auto_continue,
        }

    def _should_continue(self, step_result: Dict[str, Any]) -> bool:
        """Check if should continue conversation."""
        # Continue if auto-continue is enabled and not explicitly completed
        return self._state.auto_continue and not step_result.get("complete", False)

    def on_transcription(self, callback: Callable):
        """Set callback for transcription events."""
        self._on_transcription = callback

    def on_response(self, callback: Callable):
        """Set callback for response events."""
        self._on_response = callback

    async def start_listening(self):
        """Start continuous listening mode."""
        self._state.is_listening = True
        self._state.auto_continue = True
        secure_logger.info("Voice agent: Started listening")

    async def stop_listening(self):
        """Stop listening mode."""
        self._state.is_listening = False
        self._state.auto_continue = False
        secure_logger.info("Voice agent: Stopped listening")

    async def process_text(self, text: str) -> str:
        """
        Process text input and return response.

        Args:
            text: User input text

        Returns:
            Agent response
        """
        self._state.is_processing = True
        self._state.current_text = text

        try:
            result = await self.run(text)
            return result.output or ""
        finally:
            self._state.is_processing = False

    async def speak_and_wait(self, text: str) -> bool:
        """Speak text and wait for completion."""
        result = await self._speak(text)
        return result.get("success", False)

    def get_state(self) -> Dict[str, Any]:
        """Get current voice state."""
        return {
            "is_listening": self._state.is_listening,
            "is_speaking": self._state.is_speaking,
            "is_processing": self._state.is_processing,
            "auto_continue": self._state.auto_continue,
            "last_response": self._state.last_response,
        }


# Global voice agent
_voice_agent: Optional[VoiceAgent] = None


def get_voice_agent() -> VoiceAgent:
    """Get or create voice agent."""
    global _voice_agent
    if _voice_agent is None:
        _voice_agent = VoiceAgent()
    return _voice_agent
