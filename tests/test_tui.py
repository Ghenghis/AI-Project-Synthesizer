"""
Tests for src/tui/ - Terminal UI

Full coverage tests for:
- SynthesizerTUI
- Menu functions
- View functions
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.tui.app import SynthesizerTUI, run_tui


class TestSynthesizerTUI:
    """Tests for SynthesizerTUI class."""

    @pytest.fixture
    def tui(self):
        return SynthesizerTUI()

    def test_create_tui(self, tui):
        assert tui is not None
        assert tui.running is True
        assert tui.current_view == "main"

    def test_initial_history(self, tui):
        assert tui._history == []

    @patch('src.tui.app.console')
    def test_clear(self, mock_console, tui):
        tui.clear()
        mock_console.clear.assert_called_once()

    @patch('src.tui.app.console')
    def test_header(self, mock_console, tui):
        tui.header()
        mock_console.print.assert_called()


class TestTUIViews:
    """Tests for TUI view methods."""

    @pytest.fixture
    def tui(self):
        return SynthesizerTUI()

    @pytest.mark.asyncio
    @patch('src.tui.app.console')
    @patch('src.tui.app.Prompt')
    async def test_dashboard_view(self, mock_prompt, mock_console, tui):
        mock_prompt.ask.return_value = ""

        with patch('src.core.health.check_health', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = Mock(
                components=[],
                overall_status=Mock(value="healthy")
            )
            await tui.dashboard_view()

    @pytest.mark.asyncio
    @patch('src.tui.app.console')
    @patch('src.tui.app.Prompt')
    @patch('src.tui.app.Confirm')
    async def test_search_view_empty_query(self, mock_confirm, mock_prompt, mock_console, tui):
        mock_prompt.ask.return_value = ""
        await tui.search_view()

    @pytest.mark.asyncio
    @patch('src.tui.app.console')
    @patch('src.tui.app.Prompt')
    @patch('src.tui.app.Confirm')
    async def test_assemble_view_empty_idea(self, mock_confirm, mock_prompt, mock_console, tui):
        mock_prompt.ask.return_value = ""
        await tui.assemble_view()

    @pytest.mark.asyncio
    @patch('src.tui.app.console')
    @patch('src.tui.app.Prompt')
    async def test_agents_view_back(self, mock_prompt, mock_console, tui):
        mock_prompt.ask.return_value = "b"
        await tui.agents_view()

    @pytest.mark.asyncio
    @patch('src.tui.app.console')
    @patch('src.tui.app.Prompt')
    async def test_settings_view_back(self, mock_prompt, mock_console, tui):
        mock_prompt.ask.return_value = "b"
        await tui.settings_view()

    @pytest.mark.asyncio
    @patch('src.tui.app.console')
    @patch('src.tui.app.Prompt')
    async def test_metrics_view(self, mock_prompt, mock_console, tui):
        mock_prompt.ask.return_value = ""
        await tui.metrics_view()

    @pytest.mark.asyncio
    @patch('src.tui.app.console')
    @patch('src.tui.app.Prompt')
    async def test_workflows_view(self, mock_prompt, mock_console, tui):
        mock_prompt.ask.return_value = "b"
        await tui.workflows_view()


class TestRunTUI:
    """Tests for run_tui function."""

    @patch('src.tui.app.SynthesizerTUI')
    @patch('asyncio.run')
    def test_run_tui(self, mock_run, mock_tui_class):
        mock_tui = Mock()
        mock_tui_class.return_value = mock_tui

        run_tui()

        mock_tui_class.assert_called_once()
        mock_run.assert_called_once()
