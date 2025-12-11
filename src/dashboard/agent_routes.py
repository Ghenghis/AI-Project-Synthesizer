"""
AI Project Synthesizer - Agent API Routes

API endpoints for agent management:
- Research agent
- Synthesis agent
- Voice agent
- Automation agent
- Code agent
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


# Request models
class ResearchRequest(BaseModel):
    topic: str
    max_results: int = 10


class SynthesisRequest(BaseModel):
    idea: str
    output_dir: str = "G:/"
    name: Optional[str] = None


class VoiceRequest(BaseModel):
    text: str
    voice: Optional[str] = None


class CodeRequest(BaseModel):
    description: str
    language: str = "python"
    style: str = "production"


class FixCodeRequest(BaseModel):
    code: str
    error: str
    language: str = "python"


class AutomationRequest(BaseModel):
    task: str


# ============================================
# Agent Status
# ============================================

@router.get("/status")
async def get_agents_status() -> Dict[str, Any]:
    """Get status of all agents."""
    from src.agents import (
        ResearchAgent,
        SynthesisAgent,
        VoiceAgent,
        AutomationAgent,
        CodeAgent,
    )
    
    return {
        "agents": [
            {"name": "research", "status": "available", "description": "Discovers resources"},
            {"name": "synthesis", "status": "available", "description": "Assembles projects"},
            {"name": "voice", "status": "available", "description": "Voice interactions"},
            {"name": "automation", "status": "available", "description": "Workflow automation"},
            {"name": "code", "status": "available", "description": "Code generation"},
        ]
    }


# ============================================
# Research Agent
# ============================================

@router.post("/research")
async def run_research(request: ResearchRequest) -> Dict[str, Any]:
    """Run research agent."""
    try:
        from src.agents import ResearchAgent
        
        agent = ResearchAgent()
        result = await agent.research(request.topic)
        
        return {
            "success": result.get("success", False),
            "agent": "research",
            "topic": request.topic,
            "result": result,
        }
    except Exception as e:
        secure_logger.error(f"Research agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Synthesis Agent
# ============================================

@router.post("/synthesis")
async def run_synthesis(request: SynthesisRequest) -> Dict[str, Any]:
    """Run synthesis agent."""
    try:
        from src.agents import SynthesisAgent
        
        agent = SynthesisAgent()
        result = await agent.synthesize(request.idea, request.output_dir)
        
        return {
            "success": result.get("success", False),
            "agent": "synthesis",
            "idea": request.idea,
            "result": result,
        }
    except Exception as e:
        secure_logger.error(f"Synthesis agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Voice Agent
# ============================================

@router.post("/voice/speak")
async def voice_speak(request: VoiceRequest) -> Dict[str, Any]:
    """Speak text using voice agent."""
    try:
        from src.agents.voice_agent import get_voice_agent
        
        agent = get_voice_agent()
        result = await agent._speak(request.text, request.voice)
        
        return {
            "success": result.get("success", False),
            "agent": "voice",
            "text": request.text,
            "result": result,
        }
    except Exception as e:
        secure_logger.error(f"Voice agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/process")
async def voice_process(request: VoiceRequest) -> Dict[str, Any]:
    """Process text with voice agent."""
    try:
        from src.agents.voice_agent import get_voice_agent
        
        agent = get_voice_agent()
        response = await agent.process_text(request.text)
        
        return {
            "success": True,
            "agent": "voice",
            "input": request.text,
            "response": response,
        }
    except Exception as e:
        secure_logger.error(f"Voice agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/state")
async def voice_state() -> Dict[str, Any]:
    """Get voice agent state."""
    try:
        from src.agents.voice_agent import get_voice_agent
        
        agent = get_voice_agent()
        return agent.get_state()
    except Exception as e:
        return {"error": str(e)}


@router.post("/voice/start")
async def voice_start() -> Dict[str, Any]:
    """Start voice listening."""
    try:
        from src.agents.voice_agent import get_voice_agent
        
        agent = get_voice_agent()
        await agent.start_listening()
        
        return {"success": True, "listening": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/stop")
async def voice_stop() -> Dict[str, Any]:
    """Stop voice listening."""
    try:
        from src.agents.voice_agent import get_voice_agent
        
        agent = get_voice_agent()
        await agent.stop_listening()
        
        return {"success": True, "listening": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Automation Agent
# ============================================

@router.post("/automation")
async def run_automation(request: AutomationRequest) -> Dict[str, Any]:
    """Run automation agent."""
    try:
        from src.agents import AutomationAgent
        
        agent = AutomationAgent()
        result = await agent.automate(request.task)
        
        return {
            "success": result.get("success", False),
            "agent": "automation",
            "task": request.task,
            "result": result,
        }
    except Exception as e:
        secure_logger.error(f"Automation agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/health-check")
async def automation_health_check() -> Dict[str, Any]:
    """Run health check via automation agent."""
    try:
        from src.agents import AutomationAgent
        
        agent = AutomationAgent()
        result = await agent._check_health()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Code Agent
# ============================================

@router.post("/code/generate")
async def code_generate(request: CodeRequest) -> Dict[str, Any]:
    """Generate code using code agent."""
    try:
        from src.agents import CodeAgent
        
        agent = CodeAgent()
        code = await agent.generate(request.description, request.language)
        
        return {
            "success": True,
            "agent": "code",
            "description": request.description,
            "language": request.language,
            "code": code,
        }
    except Exception as e:
        secure_logger.error(f"Code agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/fix")
async def code_fix(request: FixCodeRequest) -> Dict[str, Any]:
    """Fix code using code agent."""
    try:
        from src.agents import CodeAgent
        
        agent = CodeAgent()
        fixed = await agent.fix(request.code, request.error)
        
        return {
            "success": True,
            "agent": "code",
            "original": request.code,
            "fixed": fixed,
            "error": request.error,
        }
    except Exception as e:
        secure_logger.error(f"Code agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/review")
async def code_review(request: CodeRequest) -> Dict[str, Any]:
    """Review code using code agent."""
    try:
        from src.agents import CodeAgent
        
        agent = CodeAgent()
        result = await agent._review_code(request.description, request.language)
        
        return {
            "success": True,
            "agent": "code",
            "review": result,
        }
    except Exception as e:
        secure_logger.error(f"Code agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
