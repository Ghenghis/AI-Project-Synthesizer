"""
Unit tests for safe template formatter.
"""

import pytest

from src.core.safe_formatter import ISSUE_FORMATTER, MR_FORMATTER, SafeTemplateFormatter


class TestSafeTemplateFormatter:
    """Test safe template formatter."""

    def test_init_with_placeholders(self):
        """Should initialize with allowed placeholders."""
        formatter = SafeTemplateFormatter(["name", "email"])
        assert formatter.allowed_placeholders == {"name", "email"}
        assert "name" in formatter.placeholder_pattern.pattern
        assert "email" in formatter.placeholder_pattern.pattern

    def test_format_valid_template(self):
        """Valid templates should format correctly."""
        formatter = SafeTemplateFormatter(["name", "email"])
        template = "Hello {name}, email: {email}"
        context = {"name": "John", "email": "john@example.com"}

        result = formatter.format(template, context)
        assert "Hello John" in result
        assert "john@example.com" in result

    def test_format_html_escapes_values(self):
        """Values should be HTML escaped in format mode."""
        formatter = SafeTemplateFormatter(["name"])
        template = "Hello {name}"
        context = {"name": "<script>alert('xss')</script>"}

        result = formatter.format(template, context)
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_format_markdown_preserves_content(self):
        """Markdown format should preserve markdown syntax."""
        formatter = SafeTemplateFormatter(["content"])
        template = "# {content}\n\n**Bold text**"
        context = {"content": "Title\n\nBold text"}

        result = formatter.format_markdown(template, context)
        assert "# Title" in result
        assert "**Bold text**" in result

    def test_blocks_invalid_placeholders(self):
        """Templates with invalid placeholders should raise error."""
        formatter = SafeTemplateFormatter(["name"])
        template = "Hello {name} and {email}"
        context = {"name": "John", "email": "john@example.com"}

        with pytest.raises(ValueError, match="not allowed"):
            formatter.format(template, context)

    def test_sanitizes_dangerous_values(self):
        """Dangerous format specifiers should be removed from values."""
        formatter = SafeTemplateFormatter(["name"])
        template = "Hello {name}"
        context = {"name": "Test {__import__('os').system('ls')}"}

        result = formatter.format_markdown(template, context)
        assert "__import__" not in result
        assert "system" not in result

    def test_limits_value_length(self):
        """Values too long should be truncated."""
        formatter = SafeTemplateFormatter(["content"])
        template = "Content: {content}"
        long_content = "a" * 15000
        context = {"content": long_content}

        result = formatter.format_markdown(template, context)
        assert len(result) < len(template) + 10010  # Should be truncated
        assert "..." in result

    def test_handles_none_values(self):
        """None values should become empty strings."""
        formatter = SafeTemplateFormatter(["name"])
        template = "Hello {name}"
        context = {"name": None}

        result = formatter.format(template, context)
        assert result == "Hello "

    def test_missing_placeholder_in_context(self):
        """Missing placeholders should not raise error."""
        formatter = SafeTemplateFormatter(["name", "email"])
        template = "Hello {name}"
        context = {"name": "John"}  # email missing

        result = formatter.format(template, context)
        assert result == "Hello John"

    def test_empty_template(self):
        """Empty templates should work."""
        formatter = SafeTemplateFormatter(["name"])
        template = ""
        context = {"name": "John"}

        result = formatter.format(template, context)
        assert result == ""


class TestMRFormatter:
    """Test MR formatter presets."""

    def test_mr_formatter_placeholders(self):
        """MR formatter should have correct placeholders."""
        expected = {
            "feature_name",
            "description",
            "changes",
            "testing",
            "author",
            "branch",
            "ticket_id",
            "reviewer",
        }
        assert MR_FORMATTER.allowed_placeholders == expected

    def test_mr_formatter_valid_template(self):
        """Should format valid MR templates."""
        template = "feat: {feature_name}\n\n{description}\n\nChanges:\n{changes}"
        context = {
            "feature_name": "Add login",
            "description": "User authentication",
            "changes": "- Added login endpoint",
        }

        result = MR_FORMATTER.format_markdown(template, context)
        assert "feat: Add login" in result
        assert "User authentication" in result
        assert "- Added login endpoint" in result

    def test_mr_formatter_blocks_invalid(self):
        """Should block invalid placeholders."""
        template = "feat: {feature_name}\n\n{system_info}"
        context = {"feature_name": "Test", "system_info": "Linux"}

        with pytest.raises(ValueError, match="not allowed"):
            MR_FORMATTER.format_markdown(template, context)


class TestIssueFormatter:
    """Test issue formatter presets."""

    def test_issue_formatter_placeholders(self):
        """Issue formatter should have correct placeholders."""
        expected = {
            "error_type",
            "error_message",
            "file_path",
            "line_number",
            "stack_trace",
            "context",
            "author",
        }
        assert ISSUE_FORMATTER.allowed_placeholders == expected

    def test_issue_formatter_valid_template(self):
        """Should format valid issue templates."""
        template = (
            "Error: {error_type}\n\n{error_message}\n\nFile: {file_path}:{line_number}"
        )
        context = {
            "error_type": "ValueError",
            "error_message": "Invalid input",
            "file_path": "src/main.py",
            "line_number": "42",
        }

        result = ISSUE_FORMATTER.format_markdown(template, context)
        assert "Error: ValueError" in result
        assert "Invalid input" in result
        assert "src/main.py:42" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
