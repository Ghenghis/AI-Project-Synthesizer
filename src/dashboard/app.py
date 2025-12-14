"""
AI Project Synthesizer - Web Dashboard Application

FastAPI-based web dashboard for visual project management.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.core.cache import get_cache
from src.core.health import check_health
from src.core.plugins import get_plugin_manager
from src.core.security import get_secure_logger
from src.core.version import get_build_info, get_version

secure_logger = get_secure_logger(__name__)


# Request/Response models
class SearchRequest(BaseModel):
    query: str
    platforms: list[str] = ["github", "huggingface", "kaggle"]
    max_results: int = 10


class AssembleRequest(BaseModel):
    idea: str
    name: str | None = None
    output_dir: str = "G:/"
    create_github: bool = True


def create_app() -> FastAPI:
    """Create FastAPI application."""

    app = FastAPI(
        title="AI Project Synthesizer",
        description="Visual dashboard for intelligent project synthesis",
        version=get_version(),
    )

    # CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include settings routes
    from src.dashboard.settings_routes import router as settings_router

    app.include_router(settings_router)

    # Include agent routes
    from src.dashboard.agent_routes import router as agent_router

    app.include_router(agent_router)

    # Include memory routes
    from src.dashboard.memory_routes import router as memory_router

    app.include_router(memory_router)

    # Include webhook routes
    from src.dashboard.webhook_routes import router as webhook_router

    app.include_router(webhook_router)

    # API Routes
    @app.get("/")
    async def root():
        """Dashboard home page."""
        return HTMLResponse(content=get_dashboard_html(), status_code=200)

    @app.get("/api/health")
    async def health():
        """Get system health status."""
        health_status = await check_health()
        return health_status.to_dict()

    @app.get("/api/version")
    async def version():
        """Get version info."""
        return get_build_info()

    @app.get("/api/cache/stats")
    async def cache_stats():
        """Get cache statistics."""
        cache = get_cache()
        return await cache.stats()

    @app.post("/api/cache/clear")
    async def cache_clear():
        """Clear cache."""
        cache = get_cache()
        count = await cache.clear()
        return {"cleared": count}

    @app.get("/api/plugins")
    async def list_plugins():
        """List installed plugins."""
        manager = get_plugin_manager()
        return {"plugins": manager.list_plugins()}

    @app.post("/api/search")
    async def search(request: SearchRequest):
        """Search across platforms."""
        try:
            from src.discovery.unified_search import create_unified_search

            search = create_unified_search()
            results = await search.search(
                query=request.query,
                platforms=request.platforms,
                max_results=request.max_results,
            )

            return {
                "query": request.query,
                "total": len(results.repositories),
                "results": [
                    {
                        "name": r.name,
                        "full_name": r.full_name,
                        "platform": r.platform,
                        "url": r.url,
                        "description": r.description,
                        "stars": r.stars,
                    }
                    for r in results.repositories
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/assemble")
    async def assemble(request: AssembleRequest):
        """Assemble a project."""
        try:
            from src.synthesis.project_assembler import (
                AssemblerConfig,
                ProjectAssembler,
            )

            config = AssemblerConfig(
                base_output_dir=Path(request.output_dir),
                create_github_repo=request.create_github,
            )

            assembler = ProjectAssembler(config)
            project = await assembler.assemble(request.idea, request.name)

            return {
                "success": True,
                "project": {
                    "name": project.name,
                    "path": str(project.base_path),
                    "github_url": project.github_repo_url,
                },
                "resources": {
                    "code_repos": len(project.code_repos),
                    "models": len(project.models),
                    "datasets": len(project.datasets),
                    "papers": len(project.papers),
                },
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/projects")
    async def list_projects():
        """List assembled projects."""
        projects = []
        base_dir = Path("G:/")

        if base_dir.exists():
            for item in base_dir.iterdir():
                manifest = item / "project-manifest.json"
                if manifest.exists():
                    try:
                        data = json.loads(manifest.read_text())
                        projects.append(
                            {
                                "name": data.get("name"),
                                "path": str(item),
                                "created_at": data.get("created_at"),
                                "github_url": data.get("github_repo_url"),
                            }
                        )
                    except Exception:
                        pass

        return {"projects": projects}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket for real-time updates."""
        await websocket.accept()

        try:
            while True:
                # Send health updates every 10 seconds
                health_status = await check_health()
                await websocket.send_json(
                    {
                        "type": "health",
                        "data": health_status.to_dict(),
                    }
                )
                await asyncio.sleep(10)
        except WebSocketDisconnect:
            pass

    # ============================================
    # Metrics & Monitoring Endpoints (for n8n)
    # ============================================

    @app.get("/api/metrics")
    async def get_metrics():
        """Get system metrics."""
        from src.automation.metrics import get_metrics_collector

        collector = get_metrics_collector()
        return collector.get_summary()

    @app.post("/api/metrics")
    async def record_metrics(data: dict[str, Any]):
        """Record metrics from n8n workflows."""
        import time

        from src.automation.metrics import TimingRecord, get_metrics_collector

        collector = get_metrics_collector()

        # Record workflow timing
        if "workflow" in data and "timings" in data:
            timings = data["timings"]
            if isinstance(timings, str):
                timings = json.loads(timings)

            for action, duration in timings.items():
                record = TimingRecord(
                    action=f"n8n_{data['workflow']}_{action}",
                    start_time=time.time() - (duration / 1000),
                    end_time=time.time(),
                    duration_ms=duration,
                    success=data.get("success", True),
                )
                collector.record(record)

        return {"status": "recorded"}

    @app.post("/api/metrics/health")
    async def record_health_metrics(data: dict[str, Any]):
        """Record health check metrics."""
        import time

        from src.automation.metrics import TimingRecord, get_metrics_collector

        collector = get_metrics_collector()
        record = TimingRecord(
            action="health_check",
            start_time=time.time(),
            end_time=time.time(),
            duration_ms=0,
            success=data.get("status") == "healthy",
            metadata={"status": data.get("status")},
        )
        collector.record(record)

        return {"status": "recorded"}

    @app.post("/api/metrics/tests")
    async def record_test_metrics(data: dict[str, Any]):
        """Record test run metrics."""
        import time

        from src.automation.metrics import TimingRecord, get_metrics_collector

        collector = get_metrics_collector()
        summary = data.get("summary", {})
        if isinstance(summary, str):
            summary = json.loads(summary)

        record = TimingRecord(
            action="integration_tests",
            start_time=time.time(),
            end_time=time.time(),
            duration_ms=summary.get("total_duration_ms", 0),
            success=summary.get("failed", 0) == 0,
            metadata=summary,
        )
        collector.record(record)

        return {"status": "recorded"}

    # ============================================
    # Alerts Endpoint (for n8n)
    # ============================================

    @app.post("/api/alerts")
    async def receive_alert(data: dict[str, Any]):
        """Receive alerts from n8n workflows."""
        alert_type = data.get("type", "unknown")

        secure_logger.warning(
            f"Alert received: {alert_type}", extra={"alert_data": data}
        )

        # Could integrate with notification systems here
        # e.g., Slack, Discord, email, etc.

        return {"status": "received", "type": alert_type}

    # ============================================
    # Recovery Endpoint (for n8n)
    # ============================================

    @app.post("/api/recovery/attempt")
    async def attempt_recovery(data: dict[str, Any]):
        """Attempt to recover unhealthy components."""
        components = data.get("components", [])
        if isinstance(components, str):
            components = json.loads(components)

        results = {}
        for component in components:
            # Implement component-specific recovery
            results[component] = "recovery_attempted"
            secure_logger.info(f"Recovery attempted for: {component}")

        return {"status": "attempted", "results": results}

    # ============================================
    # Voice Endpoints (for n8n)
    # ============================================

    @app.post("/api/voice/speak")
    async def speak(data: dict[str, Any]):
        """Generate speech from text."""
        text = data.get("text", "")
        voice = data.get("voice", "rachel")

        if not text:
            raise HTTPException(status_code=400, detail="Missing text")

        try:
            from src.voice.elevenlabs_client import ElevenLabsClient

            client = ElevenLabsClient()
            audio_path = await client.generate_speech(text, voice=voice)

            return {
                "success": True,
                "audio_path": str(audio_path),
                "text": text,
                "voice": voice,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ============================================
    # Research Topics Endpoint (for n8n)
    # ============================================

    @app.get("/api/research/topics")
    async def get_research_topics():
        """Get current research topics."""
        # Could be stored in cache or database
        default_topics = [
            {"topic": "RAG chatbot local LLM"},
            {"topic": "AI code generation"},
            {"topic": "voice assistant python"},
            {"topic": "machine learning automation"},
        ]
        return default_topics

    @app.post("/api/research/save")
    async def save_research(data: dict[str, Any]):
        """Save research results."""
        results = data.get("results", [])
        timestamp = data.get("timestamp", "")

        # Save to cache
        cache = get_cache()
        await cache.set(f"research_{timestamp}", results, ttl_seconds=86400)

        return {
            "status": "saved",
            "count": len(results) if isinstance(results, list) else 0,
        }

    # ============================================
    # Test Endpoints (for n8n)
    # ============================================

    @app.get("/api/test/search")
    async def test_search():
        """Test search functionality."""
        try:
            from src.discovery.unified_search import create_unified_search

            search = create_unified_search()
            results = await search.search("test", platforms=["github"], max_results=1)
            return {"status": "pass", "results": len(results.repositories)}
        except Exception as e:
            return {"status": "fail", "error": str(e)}

    @app.get("/api/test/cache")
    async def test_cache():
        """Test cache functionality."""
        try:
            cache = get_cache()
            await cache.set("test_key", "test_value")
            result = await cache.get("test_key")
            await cache.delete("test_key")
            return {"status": "pass" if result == "test_value" else "fail"}
        except Exception as e:
            return {"status": "fail", "error": str(e)}

    @app.get("/api/health/{component}")
    async def health_component(component: str):
        """Check health of specific component."""
        health_status = await check_health()

        for c in health_status.components:
            if c.name == component:
                return {
                    "component": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "latency_ms": c.latency_ms,
                }

        raise HTTPException(status_code=404, detail=f"Component not found: {component}")

    # ============================================
    # Automation Status Endpoint
    # ============================================

    @app.get("/api/automation/status")
    async def automation_status():
        """Get automation coordinator status."""
        try:
            from src.automation.coordinator import get_coordinator

            coordinator = get_coordinator()
            return coordinator.get_status()
        except Exception as e:
            return {"error": str(e), "running": False}

    @app.post("/api/automation/tests")
    async def run_automation_tests(data: dict[str, Any] = None):
        """Run integration tests."""
        try:
            from src.automation.coordinator import get_coordinator

            coordinator = get_coordinator()

            category = data.get("category") if data else None
            result = await coordinator.run_tests(category)

            return result.to_dict()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


def get_dashboard_html() -> str:
    """Generate dashboard HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Project Synthesizer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    </style>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <!-- Header -->
    <header class="gradient-bg p-4 shadow-lg">
        <div class="container mx-auto flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                    <span class="text-2xl">🧬</span>
                </div>
                <div>
                    <h1 class="text-xl font-bold">AI Project Synthesizer</h1>
                    <p class="text-sm opacity-75">Intelligent Project Assembly</p>
                </div>
            </div>
            <div id="health-status" class="flex items-center space-x-2">
                <span class="w-3 h-3 bg-green-400 rounded-full animate-pulse"></span>
                <span class="text-sm">Loading...</span>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="container mx-auto p-6">
        <!-- Search Section -->
        <section class="mb-8">
            <div class="bg-gray-800 rounded-xl p-6 shadow-xl">
                <h2 class="text-lg font-semibold mb-4">🔍 Search Projects</h2>
                <div class="flex space-x-4">
                    <input
                        type="text"
                        id="search-input"
                        placeholder="Enter project idea (e.g., RAG chatbot with local LLM)"
                        class="flex-1 bg-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                    <button
                        onclick="searchProjects()"
                        class="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-semibold transition"
                    >
                        Search
                    </button>
                    <button
                        onclick="assembleProject()"
                        class="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold transition"
                    >
                        🚀 Assemble
                    </button>
                </div>
                <div class="flex space-x-4 mt-4">
                    <label class="flex items-center space-x-2">
                        <input type="checkbox" id="platform-github" checked class="rounded">
                        <span>GitHub</span>
                    </label>
                    <label class="flex items-center space-x-2">
                        <input type="checkbox" id="platform-huggingface" checked class="rounded">
                        <span>HuggingFace</span>
                    </label>
                    <label class="flex items-center space-x-2">
                        <input type="checkbox" id="platform-kaggle" checked class="rounded">
                        <span>Kaggle</span>
                    </label>
                </div>
            </div>
        </section>

        <!-- Results Section -->
        <section id="results-section" class="mb-8 hidden">
            <div class="bg-gray-800 rounded-xl p-6 shadow-xl">
                <h2 class="text-lg font-semibold mb-4">📦 Search Results</h2>
                <div id="results-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                </div>
            </div>
        </section>

        <!-- Projects Section -->
        <section class="mb-8">
            <div class="bg-gray-800 rounded-xl p-6 shadow-xl">
                <h2 class="text-lg font-semibold mb-4">📁 Assembled Projects</h2>
                <div id="projects-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <p class="text-gray-400">Loading projects...</p>
                </div>
            </div>
        </section>

        <!-- Health Section -->
        <section>
            <div class="bg-gray-800 rounded-xl p-6 shadow-xl">
                <h2 class="text-lg font-semibold mb-4">💚 System Health</h2>
                <div id="health-container" class="grid grid-cols-2 md:grid-cols-4 gap-4">
                </div>
            </div>
        </section>
    </main>

    <script>
        // Load initial data
        document.addEventListener('DOMContentLoaded', () => {
            loadHealth();
            loadProjects();
            setInterval(loadHealth, 30000);
        });

        async function loadHealth() {
            try {
                const res = await fetch('/api/health');
                const data = await res.json();

                document.getElementById('health-status').innerHTML = `
                    <span class="w-3 h-3 ${data.status === 'healthy' ? 'bg-green-400' : 'bg-yellow-400'} rounded-full animate-pulse"></span>
                    <span class="text-sm">${data.status} | v${data.version}</span>
                `;

                const container = document.getElementById('health-container');
                container.innerHTML = data.components.map(c => `
                    <div class="bg-gray-700 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <span class="font-medium">${c.name}</span>
                            <span class="w-2 h-2 ${c.status === 'healthy' ? 'bg-green-400' : c.status === 'degraded' ? 'bg-yellow-400' : 'bg-gray-400'} rounded-full"></span>
                        </div>
                        <p class="text-sm text-gray-400">${c.message}</p>
                    </div>
                `).join('');
            } catch (e) {
                console.error('Health check failed:', e);
            }
        }

        async function loadProjects() {
            try {
                const res = await fetch('/api/projects');
                const data = await res.json();

                const container = document.getElementById('projects-container');
                if (data.projects.length === 0) {
                    container.innerHTML = '<p class="text-gray-400">No projects assembled yet. Try assembling one!</p>';
                } else {
                    container.innerHTML = data.projects.map(p => `
                        <div class="bg-gray-700 rounded-lg p-4">
                            <h3 class="font-semibold">${p.name}</h3>
                            <p class="text-sm text-gray-400 truncate">${p.path}</p>
                            ${p.github_url ? `<a href="${p.github_url}" target="_blank" class="text-purple-400 text-sm hover:underline">GitHub →</a>` : ''}
                        </div>
                    `).join('');
                }
            } catch (e) {
                console.error('Failed to load projects:', e);
            }
        }

        async function searchProjects() {
            const query = document.getElementById('search-input').value;
            if (!query) return;

            const platforms = [];
            if (document.getElementById('platform-github').checked) platforms.push('github');
            if (document.getElementById('platform-huggingface').checked) platforms.push('huggingface');
            if (document.getElementById('platform-kaggle').checked) platforms.push('kaggle');

            try {
                const res = await fetch('/api/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query, platforms, max_results: 12})
                });
                const data = await res.json();

                document.getElementById('results-section').classList.remove('hidden');
                document.getElementById('results-container').innerHTML = data.results.map(r => `
                    <div class="bg-gray-700 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs px-2 py-1 bg-purple-600 rounded">${r.platform}</span>
                            <span class="text-sm">⭐ ${r.stars || 0}</span>
                        </div>
                        <h3 class="font-semibold truncate">${r.name}</h3>
                        <p class="text-sm text-gray-400 line-clamp-2">${r.description || 'No description'}</p>
                        <a href="${r.url}" target="_blank" class="text-purple-400 text-sm hover:underline mt-2 inline-block">View →</a>
                    </div>
                `).join('');
            } catch (e) {
                console.error('Search failed:', e);
            }
        }

        async function assembleProject() {
            const idea = document.getElementById('search-input').value;
            if (!idea) {
                alert('Please enter a project idea');
                return;
            }

            if (!confirm(`Assemble project: "${idea}"?`)) return;

            try {
                const res = await fetch('/api/assemble', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({idea})
                });
                const data = await res.json();

                if (data.success) {
                    alert(`Project assembled!\\n\\nPath: ${data.project.path}\\nGitHub: ${data.project.github_url || 'N/A'}`);
                    loadProjects();
                }
            } catch (e) {
                alert('Assembly failed: ' + e.message);
            }
        }
    </script>
</body>
</html>
"""


def run_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Run the dashboard server."""
    import uvicorn

    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_dashboard()
