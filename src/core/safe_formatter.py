"""
Safe template formatter to prevent injection attacks.
"""

import re
from html import escape
from string import Template
from typing import Any


class SafeTemplateFormatter:
    """
    Safe template formatter that only allows whitelisted placeholders.

    Prevents template injection attacks by:
    - Only allowing specific placeholder names
    - Escaping HTML in values
    - Validating template structure
    """

    def __init__(self, allowed_placeholders: list[str]):
        """
        Initialize formatter with allowed placeholders.

        Args:
            allowed_placeholders: List of allowed placeholder names
        """
        self.allowed_placeholders = set(allowed_placeholders)
        self.placeholder_pattern = re.compile(
            r"\{(" + "|".join(allowed_placeholders) + r")\}"
        )

    def format(self, template: str, context: dict[str, Any]) -> str:
        """
        Safely format a template with context.

        Args:
            template: Template string with {placeholder} format
            context: Dictionary of values to substitute

        Returns:
            Formatted string with escaped values

        Raises:
            ValueError: If template contains invalid placeholders
        """
        # Validate template only contains allowed placeholders
        all_placeholders = re.findall(r"\{([^{}]+)\}", template)

        for placeholder in all_placeholders:
            if placeholder not in self.allowed_placeholders:
                raise ValueError(f"Placeholder '{placeholder}' not allowed in template")

        # Sanitize context values
        sanitized_context = {}
        for key, value in context.items():
            if key in self.allowed_placeholders:
                # Convert to string and escape HTML
                if value is None:
                    sanitized_context[key] = ""
                else:
                    sanitized_context[key] = escape(str(value))

        # Use string.Template for safer formatting
        # Convert {placeholder} to $placeholder
        template_safe = template.replace("{", "${").replace("}", "}")

        try:
            result = Template(template_safe).safe_substitute(sanitized_context)
            return result
        except Exception as e:
            raise ValueError(f"Template formatting failed: {e}")

    def format_markdown(self, template: str, context: dict[str, Any]) -> str:
        """
        Format template for markdown (preserves markdown formatting).

        Args:
            template: Template string
            context: Dictionary of values

        Returns:
            Formatted string with values (not HTML escaped)
        """
        # Validate template
        all_placeholders = re.findall(r"\{([^{}]+)\}", template)

        for placeholder in all_placeholders:
            if placeholder not in self.allowed_placeholders:
                raise ValueError(f"Placeholder '{placeholder}' not allowed in template")

        # Sanitize context values for markdown
        sanitized_context = {}
        for key, value in context.items():
            if key in self.allowed_placeholders:
                if value is None:
                    sanitized_context[key] = ""
                else:
                    # For markdown, we don't HTML escape but we do sanitize
                    str_value = str(value)
                    # Remove dangerous format specifiers
                    str_value = re.sub(r"\{.*?\}", "", str_value)
                    # Limit length
                    if len(str_value) > 10000:
                        str_value = str_value[:10000] + "..."
                    sanitized_context[key] = str_value

        # Use Python's format with limited context
        try:
            result = template.format(**sanitized_context)
            return result
        except Exception as e:
            raise ValueError(f"Template formatting failed: {e}")


# Predefined formatters for common use cases
MR_FORMATTER = SafeTemplateFormatter(
    [
        "feature_name",
        "description",
        "changes",
        "testing",
        "author",
        "branch",
        "ticket_id",
        "reviewer",
    ]
)

ISSUE_FORMATTER = SafeTemplateFormatter(
    [
        "error_type",
        "error_message",
        "file_path",
        "line_number",
        "stack_trace",
        "context",
        "author",
    ]
)
