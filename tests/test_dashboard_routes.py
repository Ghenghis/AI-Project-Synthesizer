"""
Tests for Dashboard API Routes

Full coverage tests for:
- Settings routes
- Agent routes
- Memory routes
- Webhook routes
"""


import pytest
from fastapi.testclient import TestClient

from src.dashboard.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestVersionEndpoint:
    """Tests for version endpoint."""

    def test_version(self, client):
        response = client.get("/api/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data


class TestSettingsRoutes:
    """Tests for settings API routes."""

    def test_get_all_settings(self, client):
        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert "general" in data
        assert "voice" in data
        assert "automation" in data

    def test_get_tabs(self, client):
        response = client.get("/api/settings/tabs")
        assert response.status_code == 200
        data = response.json()
        assert "tabs" in data
        assert len(data["tabs"]) == 7

    def test_get_general_settings(self, client):
        response = client.get("/api/settings/general")
        assert response.status_code == 200
        data = response.json()
        assert "theme" in data
        assert "language" in data

    def test_get_voice_settings(self, client):
        response = client.get("/api/settings/voice")
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert "hotkey" in data

    def test_get_automation_settings(self, client):
        response = client.get("/api/settings/automation")
        assert response.status_code == 200
        data = response.json()
        assert "auto_continue_mode" in data

    def test_get_invalid_tab(self, client):
        response = client.get("/api/settings/invalid_tab")
        assert response.status_code == 404

    def test_update_settings(self, client):
        response = client.put(
            "/api/settings/general",
            json={"updates": {"theme": "light"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_toggle_feature(self, client):
        response = client.post(
            "/api/settings/general/toggle",
            json={"feature": "auto_save"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data

    def test_get_all_toggles(self, client):
        response = client.get("/api/settings/toggles/all")
        assert response.status_code == 200
        data = response.json()
        assert "general" in data
        assert "voice" in data

    def test_reset_settings(self, client):
        response = client.post("/api/settings/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_export_settings(self, client):
        response = client.post("/api/settings/export")
        assert response.status_code == 200
        data = response.json()
        assert "settings" in data

    def test_get_hotkey_bindings(self, client):
        response = client.get("/api/settings/hotkeys/bindings")
        assert response.status_code == 200
        data = response.json()
        assert "bindings" in data

    def test_voice_quick_settings(self, client):
        response = client.get("/api/settings/voice/quick")
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert "pause_detection" in data

    def test_automation_quick_settings(self, client):
        response = client.get("/api/settings/automation/quick")
        assert response.status_code == 200
        data = response.json()
        assert "auto_continue_mode" in data


class TestAgentRoutes:
    """Tests for agent API routes."""

    def test_get_agents_status(self, client):
        response = client.get("/api/agents/status")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 5

    def test_voice_state(self, client):
        response = client.get("/api/agents/voice/state")
        assert response.status_code == 200
        data = response.json()
        assert "is_listening" in data


class TestMemoryRoutes:
    """Tests for memory API routes."""

    def test_get_memories(self, client):
        response = client.get("/api/memory")
        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
        assert "count" in data

    def test_save_memory(self, client):
        response = client.post("/api/memory", json={
            "type": "note",
            "content": {"text": "test note"},
            "tags": ["test"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data

    def test_save_memory_invalid_type(self, client):
        response = client.post("/api/memory", json={
            "type": "invalid_type",
            "content": {},
        })
        assert response.status_code == 400

    def test_get_search_history(self, client):
        response = client.get("/api/search-history")
        assert response.status_code == 200
        data = response.json()
        assert "searches" in data

    def test_save_search_history(self, client):
        response = client.post("/api/search-history", json={
            "query": "test query",
            "platforms": ["github"],
            "results_count": 10,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_bookmarks(self, client):
        response = client.get("/api/bookmarks")
        assert response.status_code == 200
        data = response.json()
        assert "bookmarks" in data

    def test_save_bookmark(self, client):
        response = client.post("/api/bookmarks", json={
            "name": "Test Repo",
            "url": "https://github.com/test/repo",
            "type": "repo",
            "tags": ["test"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_save_conversation_message(self, client):
        response = client.post("/api/conversations/message", json={
            "session_id": "test_session",
            "role": "user",
            "content": "Hello",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_conversation(self, client):
        # First save a message
        client.post("/api/conversations/message", json={
            "session_id": "conv_test",
            "role": "user",
            "content": "Test message",
        })

        response = client.get("/api/conversations/conv_test")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data

    def test_get_event_history(self, client):
        response = client.get("/api/events/history")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    def test_emit_event(self, client):
        response = client.post("/api/events/emit", json={
            "type": "notification",
            "data": {"message": "test"},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_save_workflow_state(self, client):
        response = client.post(
            "/api/workflow-state/test_workflow",
            json={"step": 1, "status": "running"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_workflow_state(self, client):
        # First save state
        client.post(
            "/api/workflow-state/get_test",
            json={"step": 2}
        )

        response = client.get("/api/workflow-state/get_test")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data


class TestWebhookRoutes:
    """Tests for webhook API routes."""

    def test_list_webhooks(self, client):
        response = client.get("/api/webhooks/list")
        assert response.status_code == 200
        data = response.json()
        assert "webhooks" in data
        assert len(data["webhooks"]) > 0

    def test_github_webhook(self, client):
        response = client.post(
            "/api/webhooks/github",
            json={
                "action": "opened",
                "repository": {"full_name": "test/repo"},
                "sender": {"login": "testuser"},
            },
            headers={"X-GitHub-Event": "push"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"

    def test_n8n_webhook(self, client):
        response = client.post(
            "/api/webhooks/n8n/test_workflow",
            json={
                "status": "completed",
                "result": {"success": True},
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert data["workflow"] == "test_workflow"

    def test_custom_webhook(self, client):
        response = client.post(
            "/api/webhooks/custom/my_hook",
            json={
                "message": "Custom event",
                "level": "info",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hook_id"] == "my_hook"

    def test_slack_webhook(self, client):
        response = client.post(
            "/api/webhooks/slack",
            data={
                "command": "/synth-status",
                "text": "",
                "user_name": "testuser",
            }
        )
        assert response.status_code == 200

    def test_discord_webhook_ping(self, client):
        response = client.post(
            "/api/webhooks/discord",
            json={"type": 1}  # Ping
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == 1

    def test_test_webhook(self, client):
        response = client.post(
            "/api/webhooks/test",
            json={"test": "data"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert data["echo"]["test"] == "data"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
