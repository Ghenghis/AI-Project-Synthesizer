"""
Unit tests for AST Parser edge cases.

Tests multi-language parsing, regex fallback, and error handling.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.analysis.ast_parser import (
    ASTParser,
)


class TestASTParserLanguageDetection:
    """Test language detection from file extensions."""

    def test_python_extensions(self):
        """Test Python file extension detection."""
        parser = ASTParser()
        assert parser._detect_language(Path("main.py")) == "python"
        assert parser._detect_language(Path("script.pyw")) == "python"

    def test_javascript_extensions(self):
        """Test JavaScript file extension detection."""
        parser = ASTParser()
        assert parser._detect_language(Path("app.js")) == "javascript"
        assert parser._detect_language(Path("module.mjs")) == "javascript"
        assert parser._detect_language(Path("component.jsx")) == "javascript"

    def test_typescript_extensions(self):
        """Test TypeScript file extension detection."""
        parser = ASTParser()
        assert parser._detect_language(Path("app.ts")) == "typescript"
        assert parser._detect_language(Path("component.tsx")) == "typescript"

    def test_other_languages(self):
        """Test other supported language extensions."""
        parser = ASTParser()
        assert parser._detect_language(Path("main.rs")) == "rust"
        assert parser._detect_language(Path("main.go")) == "go"
        assert parser._detect_language(Path("Main.java")) == "java"
        assert parser._detect_language(Path("main.c")) == "c"
        assert parser._detect_language(Path("main.cpp")) == "cpp"
        assert parser._detect_language(Path("main.rb")) == "ruby"
        assert parser._detect_language(Path("main.php")) == "php"

    def test_unknown_extension(self):
        """Test unknown file extension returns 'unknown'."""
        parser = ASTParser()
        assert parser._detect_language(Path("file.xyz")) == "unknown"
        assert parser._detect_language(Path("README.md")) == "unknown"
        assert parser._detect_language(Path("Makefile")) == "unknown"


class TestASTParserSkipDirectories:
    """Test directory skip logic."""

    def test_skip_node_modules(self):
        """Test node_modules is skipped."""
        parser = ASTParser()
        assert parser._should_skip(Path("node_modules/package/index.js"))

    def test_skip_venv(self):
        """Test virtual environment directories are skipped."""
        parser = ASTParser()
        assert parser._should_skip(Path("venv/lib/python3.11/site.py"))
        assert parser._should_skip(Path(".venv/bin/activate.py"))

    def test_skip_pycache(self):
        """Test __pycache__ is skipped."""
        parser = ASTParser()
        assert parser._should_skip(Path("src/__pycache__/module.cpython-311.pyc"))

    def test_skip_git(self):
        """Test .git directory is skipped."""
        parser = ASTParser()
        assert parser._should_skip(Path(".git/objects/pack/file"))

    def test_skip_egg_info(self):
        """Test egg-info directories are skipped."""
        parser = ASTParser()
        assert parser._should_skip(Path("mypackage.egg-info/PKG-INFO"))

    def test_allow_normal_paths(self):
        """Test normal source paths are not skipped."""
        parser = ASTParser()
        assert not parser._should_skip(Path("src/main.py"))
        assert not parser._should_skip(Path("tests/test_main.py"))
        assert not parser._should_skip(Path("lib/utils/helpers.py"))


class TestASTParserPythonParsing:
    """Test Python file parsing."""

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        parser = ASTParser()
        result = await parser.parse_file(Path("/nonexistent/file.py"))

        assert result.language == "unknown"
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_parse_unsupported_extension(self):
        """Test parsing a file with unsupported extension."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"some content")
            temp_path = Path(f.name)

        try:
            parser = ASTParser()
            result = await parser.parse_file(temp_path)

            assert result.language == "unknown"
            assert "Unsupported file type" in result.errors
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_parse_simple_python(self):
        """Test parsing simple Python code."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write('''
import os
from pathlib import Path

def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"

class Greeter:
    """A greeter class."""
    def greet(self):
        pass
''')
            temp_path = Path(f.name)

        try:
            parser = ASTParser()
            result = await parser.parse_file(temp_path)

            assert result.language == "python"
            assert len(result.errors) == 0
            assert len(result.imports) == 2  # os and Path
            assert len(result.functions) >= 1
            assert any(f.name == "hello" for f in result.functions)
            assert len(result.classes) == 1
            assert result.classes[0].name == "Greeter"
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_parse_python_syntax_error(self):
        """Test parsing Python code with syntax errors."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
def broken(
    # Missing closing parenthesis and colon
""")
            temp_path = Path(f.name)

        try:
            parser = ASTParser()
            result = await parser.parse_file(temp_path)

            # Should still return a ParsedFile with basic metrics
            assert result.language == "python"
            assert result.loc > 0
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_parse_async_functions(self):
        """Test parsing async functions."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
async def fetch_data(url):
    pass

async def process():
    await fetch_data("http://example.com")
""")
            temp_path = Path(f.name)

        try:
            parser = ASTParser()
            result = await parser.parse_file(temp_path)

            assert len(result.functions) >= 2
            async_funcs = [f for f in result.functions if f.is_async]
            assert len(async_funcs) >= 2
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_parse_decorators(self):
        """Test parsing functions with decorators."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
@staticmethod
def static_func():
    pass

@property
def prop(self):
    return self._value

@app.route("/")
def handler():
    pass
""")
            temp_path = Path(f.name)

        try:
            parser = ASTParser()
            result = await parser.parse_file(temp_path)

            # Should find functions with decorators
            decorated = [f for f in result.functions if f.decorators]
            assert len(decorated) >= 2
        finally:
            temp_path.unlink()


class TestASTParserJavaScriptParsing:
    """Test JavaScript/TypeScript file parsing."""

    @pytest.mark.asyncio
    async def test_parse_es6_imports(self):
        """Test parsing ES6 import statements."""
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w") as f:
            f.write("""
import React from 'react';
import { useState, useEffect } from 'react';
import * as utils from './utils';
""")
            temp_path = Path(f.name)

        try:
            parser = ASTParser()
            result = await parser.parse_file(temp_path)

            assert result.language == "javascript"
            assert len(result.imports) >= 2
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_parse_arrow_functions(self):
        """Test parsing arrow functions."""
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w") as f:
            f.write("""
const add = (a, b) => a + b;
const greet = async (name) => {
    return `Hello, ${name}`;
};
let multiply = (x, y) => x * y;
""")
            temp_path = Path(f.name)

        try:
            parser = ASTParser()
            result = await parser.parse_file(temp_path)

            assert len(result.functions) >= 3
            assert any(f.name == "add" for f in result.functions)
            assert any(f.name == "greet" for f in result.functions)
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_parse_js_classes(self):
        """Test parsing JavaScript classes."""
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w") as f:
            f.write("""
class Animal {
    constructor(name) {
        this.name = name;
    }
}

class Dog extends Animal {
    bark() {
        console.log("Woof!");
    }
}
""")
            temp_path = Path(f.name)

        try:
            parser = ASTParser()
            result = await parser.parse_file(temp_path)

            assert len(result.classes) == 2
            dog_class = next(c for c in result.classes if c.name == "Dog")
            assert "Animal" in dog_class.bases
        finally:
            temp_path.unlink()
