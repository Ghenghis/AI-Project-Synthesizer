"""
Context Manager for VIBE MCP

Tracks state across task phases:
- Phase state persistence
- Checkpoint creation and restoration
- Progress tracking
- Context inheritance between phases
- Integration with Mem0 for long-term storage

Provides reliable state management for structured processes.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from src.memory.mem0_integration import MemorySystem
from src.vibe.task_decomposer import TaskPhase, TaskPlan
from src.core.config import get_settings


class PhaseStatus(Enum):
    """Status of a phase in the task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseState:
    """State information for a single phase."""
    phase_id: str
    status: PhaseStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    artifacts: Dict[str, Any] = None  # Files created, outputs, etc.
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TaskContext:
    """Complete context for a task execution."""
    task_id: str
    plan: TaskPlan
    current_phase: Optional[str] = None
    phase_states: Dict[str, PhaseState] = None
    global_context: Dict[str, Any] = None
    checkpoints: List[str] = None  # Checkpoint IDs
    created_at: datetime = None
    
    def __post_init__(self):
        if self.phase_states is None:
            self.phase_states = {}
        if self.global_context is None:
            self.global_context = {}
        if self.checkpoints is None:
            self.checkpoints = []
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Checkpoint:
    """A saved state that can be restored."""
    checkpoint_id: str
    task_id: str
    phase_id: str
    timestamp: datetime
    context_snapshot: Dict[str, Any]
    artifacts: Dict[str, Any]


class ContextManager:
    """
    Manages context and state across task phases.
    
    Features:
    - Phase state tracking
    - Checkpoint/restore functionality
    - Mem0 integration for persistence
    - Progress monitoring
    - Error recovery
    """
    
    def __init__(self):
        self.config = get_settings()
        self.memory = MemorySystem()
        
        # Active contexts (in-memory)
        self._active_contexts: Dict[str, TaskContext] = {}
        
        # Checkpoint storage
        self._checkpoints: Dict[str, Checkpoint] = {}
        
        # Configuration
        self.max_checkpoints = 10
        self.auto_checkpoint = True
        self.persistence_ttl = timedelta(days=7)
    
    async def create_context(self, plan: TaskPlan, initial_context: Optional[Dict[str, Any]] = None) -> TaskContext:
        """
        Create a new task context.
        
        Args:
            plan: The task plan
            initial_context: Initial global context
            
        Returns:
            Created TaskContext
        """
        context = TaskContext(
            task_id=plan.task_id,
            plan=plan,
            global_context=initial_context or {},
            created_at=datetime.now()
        )
        
        # Initialize phase states
        for phase in plan.phases:
            context.phase_states[phase.id] = PhaseState(
                phase_id=phase.id,
                status=PhaseStatus.PENDING
            )
        
        # Store in memory
        self._active_contexts[context.task_id] = context
        
        # Persist to Mem0
        await self._save_context(context)
        
        return context
    
    async def get_context(self, task_id: str) -> Optional[TaskContext]:
        """
        Get task context, loading from persistence if needed.
        
        Args:
            task_id: The task ID
            
        Returns:
            TaskContext if found
        """
        # Check memory first
        if task_id in self._active_contexts:
            return self._active_contexts[task_id]
        
        # Load from persistence
        context = await self._load_context(task_id)
        if context:
            self._active_contexts[task_id] = context
            return context
        
        return None
    
    async def start_phase(self, task_id: str, phase_id: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Start a phase in the task.
        
        Args:
            task_id: The task ID
            phase_id: The phase ID to start
            context: Additional context for this phase
            
        Returns:
            True if phase started successfully
        """
        task_context = await self.get_context(task_id)
        if not task_context:
            return False
        
        # Check dependencies
        phase = next((p for p in task_context.plan.phases if p.id == phase_id), None)
        if not phase:
            return False
        
        for dep_id in phase.dependencies:
            dep_state = task_context.phase_states.get(dep_id)
            if not dep_state or dep_state.status != PhaseStatus.COMPLETED:
                return False
        
        # Update phase state
        phase_state = task_context.phase_states[phase_id]
        phase_state.status = PhaseStatus.IN_PROGRESS
        phase_state.started_at = datetime.now()
        
        # Update current phase
        task_context.current_phase = phase_id
        
        # Add context
        if context:
            task_context.global_context.update(context)
        
        # Create checkpoint if enabled
        if self.auto_checkpoint:
            await self.create_checkpoint(task_id, phase_id, "phase_start")
        
        # Save state
        await self._save_context(task_context)
        
        return True
    
    async def complete_phase(self, task_id: str, phase_id: str, 
                           artifacts: Optional[Dict[str, Any]] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark a phase as completed.
        
        Args:
            task_id: The task ID
            phase_id: The phase ID
            artifacts: Artifacts created by the phase
            metadata: Additional metadata
            
        Returns:
            True if phase completed successfully
        """
        task_context = await self.get_context(task_id)
        if not task_context:
            return False
        
        # Update phase state
        phase_state = task_context.phase_states[phase_id]
        phase_state.status = PhaseStatus.COMPLETED
        phase_state.completed_at = datetime.now()
        
        if artifacts:
            phase_state.artifacts.update(artifacts)
        if metadata:
            phase_state.metadata.update(metadata)
        
        # Create checkpoint
        if self.auto_checkpoint:
            await self.create_checkpoint(task_id, phase_id, "phase_complete")
        
        # Save state
        await self._save_context(task_context)
        
        return True
    
    async def fail_phase(self, task_id: str, phase_id: str, error_message: str) -> bool:
        """
        Mark a phase as failed.
        
        Args:
            task_id: The task ID
            phase_id: The phase ID
            error_message: Error description
            
        Returns:
            True if phase failed successfully
        """
        task_context = await self.get_context(task_id)
        if not task_context:
            return False
        
        # Update phase state
        phase_state = task_context.phase_states[phase_id]
        phase_state.status = PhaseStatus.FAILED
        phase_state.error_message = error_message
        
        # Save state
        await self._save_context(task_context)
        
        return True
    
    async def create_checkpoint(self, task_id: str, phase_id: str, checkpoint_name: str) -> str:
        """
        Create a checkpoint of the current state.
        
        Args:
            task_id: The task ID
            phase_id: The current phase ID
            checkpoint_name: Descriptive name for the checkpoint
            
        Returns:
            Checkpoint ID
        """
        task_context = await self.get_context(task_id)
        if not task_context:
            raise ValueError(f"Task {task_id} not found")
        
        # Create checkpoint
        checkpoint_id = f"ckpt_{uuid.uuid4().hex[:8]}"
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            task_id=task_id,
            phase_id=phase_id,
            timestamp=datetime.now(),
            context_snapshot={
                "global_context": task_context.global_context.copy(),
                "phase_states": {
                    pid: asdict(state) for pid, state in task_context.phase_states.items()
                }
            },
            artifacts={
                pid: state.artifacts.copy() 
                for pid, state in task_context.phase_states.items()
                if state.artifacts
            }
        )
        
        # Store checkpoint
        self._checkpoints[checkpoint_id] = checkpoint
        task_context.checkpoints.append(checkpoint_id)
        
        # Limit checkpoints
        if len(task_context.checkpoints) > self.max_checkpoints:
            # Remove oldest
            old_checkpoint_id = task_context.checkpoints.pop(0)
            self._checkpoints.pop(old_checkpoint_id, None)
        
        # Persist
        await self._save_checkpoint(checkpoint)
        await self._save_context(task_context)
        
        return checkpoint_id
    
    async def restore_checkpoint(self, task_id: str, checkpoint_id: str) -> bool:
        """
        Restore task to a previous checkpoint.
        
        Args:
            task_id: The task ID
            checkpoint_id: The checkpoint to restore
            
        Returns:
            True if restored successfully
        """
        # Get checkpoint
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            checkpoint = await self._load_checkpoint(checkpoint_id)
            if not checkpoint:
                return False
            self._checkpoints[checkpoint_id] = checkpoint
        
        # Verify it belongs to the task
        if checkpoint.task_id != task_id:
            return False
        
        # Restore context
        task_context = await self.get_context(task_id)
        if not task_context:
            return False
        
        # Restore snapshot
        task_context.global_context = checkpoint.context_snapshot["global_context"]
        
        # Restore phase states
        for pid, state_data in checkpoint.context_snapshot["phase_states"].items():
            if pid in task_context.phase_states:
                # Update existing state
                state = task_context.phase_states[pid]
                state.status = PhaseStatus(state_data["status"])
                state.started_at = datetime.fromisoformat(state_data["started_at"]) if state_data.get("started_at") else None
                state.completed_at = datetime.fromisoformat(state_data["completed_at"]) if state_data.get("completed_at") else None
                state.error_message = state_data.get("error_message")
                state.metadata = state_data.get("metadata", {})
        
        # Restore artifacts
        for pid, artifacts in checkpoint.artifacts.items():
            if pid in task_context.phase_states:
                task_context.phase_states[pid].artifacts = artifacts
        
        # Set current phase
        task_context.current_phase = checkpoint.phase_id
        
        # Save restored state
        await self._save_context(task_context)
        
        return True
    
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """
        Get progress information for a task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Progress information
        """
        task_context = self._active_contexts.get(task_id)
        if not task_context:
            return {}
        
        total_phases = len(task_context.plan.phases)
        completed = sum(
            1 for state in task_context.phase_states.values()
            if state.status == PhaseStatus.COMPLETED
        )
        failed = sum(
            1 for state in task_context.phase_states.values()
            if state.status == PhaseStatus.FAILED
        )
        in_progress = sum(
            1 for state in task_context.phase_states.values()
            if state.status == PhaseStatus.IN_PROGRESS
        )
        
        return {
            "task_id": task_id,
            "total_phases": total_phases,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": total_phases - completed - failed - in_progress,
            "progress_percentage": (completed / total_phases * 100) if total_phases > 0 else 0,
            "current_phase": task_context.current_phase,
            "estimated_completion": self._estimate_completion(task_context)
        }
    
    def _estimate_completion(self, context: TaskContext) -> Optional[str]:
        """Estimate task completion time."""
        if not context.current_phase:
            return None
        
        # Simple estimation based on completed phases
        completed_phases = [
            p for p in context.phase_states.values()
            if p.status == PhaseStatus.COMPLETED and p.started_at and p.completed_at
        ]
        
        if not completed_phases:
            return None
        
        # Calculate average phase duration
        total_duration = sum(
            (p.completed_at - p.started_at).total_seconds()
            for p in completed_phases
        )
        avg_duration = total_duration / len(completed_phases)
        
        # Estimate remaining time
        remaining = sum(
            1 for p in context.phase_states.values()
            if p.status in [PhaseStatus.PENDING, PhaseStatus.IN_PROGRESS]
        )
        
        estimated_seconds = avg_duration * remaining
        completion_time = datetime.now() + timedelta(seconds=estimated_seconds)
        
        return completion_time.isoformat()
    
    async def _save_context(self, context: TaskContext) -> None:
        """Save context to Mem0."""
        # Convert to serializable format
        data = {
            "task_id": context.task_id,
            "plan": asdict(context.plan),
            "current_phase": context.current_phase,
            "global_context": context.global_context,
            "checkpoints": context.checkpoints,
            "created_at": context.created_at.isoformat(),
            "phase_states": {
                pid: asdict(state) for pid, state in context.phase_states.items()
            }
        }
        
        # Convert datetime objects
        for state_data in data["phase_states"].values():
            if state_data.get("started_at"):
                state_data["started_at"] = datetime.fromisoformat(state_data["started_at"]).isoformat()
            if state_data.get("completed_at"):
                state_data["completed_at"] = datetime.fromisoformat(state_data["completed_at"]).isoformat()
        
        await self.memory.add(
            content=json.dumps(data),
            category="CONTEXT",
            tags=["task", context.task_id],
            importance=0.9
        )
    
    async def _load_context(self, task_id: str) -> Optional[TaskContext]:
        """Load context from Mem0."""
        try:
            results = await self.memory.search(
                query=task_id,
                category="CONTEXT",
                limit=1
            )
            
            if not results:
                return None
            
            data = json.loads(results[0]["content"])
            
            # Reconstruct plan
            from src.vibe.task_decomposer import TaskComplexity, PhaseType, TaskPhase, TaskPlan
            
            plan_data = data["plan"]
            phases = []
            for phase_data in plan_data["phases"]:
                phase = TaskPhase(
                    id=phase_data["id"],
                    name=phase_data["name"],
                    type=PhaseType(phase_data["type"]),
                    description=phase_data["description"],
                    prompt=phase_data["prompt"],
                    dependencies=phase_data["dependencies"],
                    estimated_effort=phase_data["estimated_effort"],
                    files_to_create=phase_data["files_to_create"],
                    files_to_modify=phase_data["files_to_modify"],
                    success_criteria=phase_data["success_criteria"]
                )
                phases.append(phase)
            
            plan = TaskPlan(
                task_id=plan_data["task_id"],
                original_request=plan_data["original_request"],
                complexity=TaskComplexity(plan_data["complexity"]),
                phases=phases,
                total_effort=plan_data["total_effort"],
                estimated_duration=plan_data["estimated_duration"],
                metadata=plan_data["metadata"]
            )
            
            # Reconstruct context
            context = TaskContext(
                task_id=data["task_id"],
                plan=plan,
                current_phase=data.get("current_phase"),
                global_context=data.get("global_context", {}),
                checkpoints=data.get("checkpoints", []),
                created_at=datetime.fromisoformat(data["created_at"])
            )
            
            # Reconstruct phase states
            for pid, state_data in data["phase_states"].items():
                state = PhaseState(
                    phase_id=state_data["phase_id"],
                    status=PhaseStatus(state_data["status"]),
                    started_at=datetime.fromisoformat(state_data["started_at"]) if state_data.get("started_at") else None,
                    completed_at=datetime.fromisoformat(state_data["completed_at"]) if state_data.get("completed_at") else None,
                    artifacts=state_data.get("artifacts", {}),
                    metadata=state_data.get("metadata", {}),
                    error_message=state_data.get("error_message")
                )
                context.phase_states[pid] = state
            
            return context
            
        except Exception as e:
            print(f"Failed to load context: {e}")
            return None
    
    async def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to Mem0."""
        data = asdict(checkpoint)
        data["timestamp"] = checkpoint.timestamp.isoformat()
        
        await self.memory.add(
            content=json.dumps(data),
            category="CHECKPOINT",
            tags=["checkpoint", checkpoint.task_id, checkpoint.phase_id],
            importance=0.7
        )
    
    async def _load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from Mem0."""
        try:
            results = await self.memory.search(
                query=checkpoint_id,
                category="CHECKPOINT",
                limit=1
            )
            
            if not results:
                return None
            
            data = json.loads(results[0]["content"])
            
            return Checkpoint(
                checkpoint_id=data["checkpoint_id"],
                task_id=data["task_id"],
                phase_id=data["phase_id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                context_snapshot=data["context_snapshot"],
                artifacts=data["artifacts"]
            )
            
        except Exception as e:
            print(f"Failed to load checkpoint: {e}")
            return None
    
    async def cleanup(self, task_id: str) -> None:
        """Clean up task context and checkpoints."""
        # Remove from memory
        self._active_contexts.pop(task_id, None)
        
        # Remove checkpoints
        to_remove = [
            cid for cid, ckpt in self._checkpoints.items()
            if ckpt.task_id == task_id
        ]
        for cid in to_remove:
            self._checkpoints.pop(cid, None)


# CLI interface for testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        manager = ContextManager()
        
        # Create a demo task plan
        from src.vibe.task_decomposer import TaskPlan, TaskPhase, PhaseType, TaskComplexity
        
        plan = TaskPlan(
            task_id="demo_task",
            original_request="Create a simple API",
            complexity=TaskComplexity.MODERATE,
            phases=[
                TaskPhase(
                    id="phase_1",
                    name="Setup",
                    type=PhaseType.SETUP,
                    description="Setup project structure",
                    prompt="Create project structure",
                    dependencies=[],
                    estimated_effort=2,
                    files_to_create=["main.py"],
                    files_to_modify=[],
                    success_criteria=["Structure created"]
                ),
                TaskPhase(
                    id="phase_2",
                    name="Implementation",
                    type=PhaseType.IMPLEMENTATION,
                    description="Implement API",
                    prompt="Create API endpoints",
                    dependencies=["phase_1"],
                    estimated_effort=5,
                    files_to_create=["api.py"],
                    files_to_modify=["main.py"],
                    success_criteria=["API working"]
                )
            ],
            total_effort=7,
            estimated_duration="3 hours",
            metadata={}
        )
        
        # Create context
        context = await manager.create_context(plan, {"tech": "Python"})
        print(f"Created context for task: {context.task_id}")
        
        # Start phase 1
        success = await manager.start_phase(context.task_id, "phase_1")
        print(f"Started phase 1: {success}")
        
        # Complete phase 1
        await manager.complete_phase(
            context.task_id, 
            "phase_1",
            artifacts={"main.py": "created"},
            metadata={"lines": 50}
        )
        
        # Check progress
        progress = manager.get_progress(context.task_id)
        print(f"Progress: {progress['progress_percentage']:.1f}%")
        
        # Create checkpoint
        checkpoint_id = await manager.create_checkpoint(
            context.task_id,
            "phase_1",
            "after_phase_1"
        )
        print(f"Created checkpoint: {checkpoint_id}")
    
    asyncio.run(main())
