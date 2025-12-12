#!/usr/bin/env python3
"""
Feature Inventory Script for AI Project Synthesizer
Automatically scans the codebase to catalog all modules, classes, and functions.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class FeatureScanner(ast.NodeVisitor):
    """AST visitor to extract features from Python files."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.features = {
            'file': filepath,
            'module': '',
            'docstring': '',
            'classes': [],
            'functions': [],
            'imports': [],
            'constants': [],
            'enums': [],
            'dataclasses': []
        }
    
    def visit_Module(self, node):
        """Visit module node."""
        if ast.get_docstring(node):
            self.features['docstring'] = ast.get_docstring(node) or ''
        
        # Extract module name from path
        parts = Path(self.filepath).parts
        if 'src' in parts:
            src_idx = parts.index('src')
            self.features['module'] = '.'.join(parts[src_idx+1:]).replace('.py', '')
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Visit class definition."""
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'bases': [base.id if hasattr(base, 'id') else str(base) for base in node.bases],
            'methods': [],
            'properties': [],
            'decorators': []
        }
        
        # Check for special class types
        for decorator in node.decorator_list:
            if hasattr(decorator, 'id'):
                class_info['decorators'].append(decorator.id)
                if decorator.id == 'dataclass':
                    self.features['dataclasses'].append(node.name)
                elif decorator.id in ['enum', 'Enum']:
                    self.features['enums'].append(node.name)
        
        # Visit methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = {
                    'name': item.name,
                    'docstring': ast.get_docstring(item) or '',
                    'args': [arg.arg for arg in item.args.args],
                    'is_async': isinstance(item, ast.AsyncFunctionDef),
                    'decorators': []
                }
                
                for decorator in item.decorator_list:
                    if hasattr(decorator, 'id'):
                        method_info['decorators'].append(decorator.id)
                
                class_info['methods'].append(method_info)
        
        self.features['classes'].append(class_info)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Visit function definition."""
        if not hasattr(self, 'current_class'):
            func_info = {
                'name': node.name,
                'docstring': ast.get_docstring(node) or '',
                'args': [arg.arg for arg in node.args.args],
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'decorators': []
            }
            
            for decorator in node.decorator_list:
                if hasattr(decorator, 'id'):
                    func_info['decorators'].append(decorator.id)
            
            self.features['functions'].append(func_info)
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
    
    def visit_Import(self, node):
        """Visit import statement."""
        for alias in node.names:
            self.features['imports'].append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visit from import statement."""
        if node.module:
            for alias in node.names:
                self.features['imports'].append(f"{node.module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Visit assignment to find constants."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id.isupper():
                self.features['constants'].append(node.targets[0].id)
        self.generic_visit(node)


def scan_directory(directory: Path) -> Dict[str, Any]:
    """Scan directory for Python files and extract features."""
    inventory = {
        'scan_date': datetime.now().isoformat(),
        'total_files': 0,
        'modules': {},
        'summary': {
            'total_classes': 0,
            'total_functions': 0,
            'total_enums': 0,
            'total_dataclasses': 0,
            'categories': {}
        }
    }
    
    for py_file in directory.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        inventory['total_files'] += 1
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            scanner = FeatureScanner(str(py_file))
            scanner.visit(tree)
            
            # Categorize by module
            category = 'other'
            parts = py_file.parts
            if 'src' in parts:
                src_idx = parts.index('src')
                if src_idx + 1 < len(parts):
                    category = parts[src_idx + 1]
            
            if category not in inventory['summary']['categories']:
                inventory['summary']['categories'][category] = {
                    'files': 0,
                    'classes': 0,
                    'functions': 0
                }
            
            inventory['summary']['categories'][category]['files'] += 1
            inventory['summary']['total_classes'] += len(scanner.features['classes'])
            inventory['summary']['total_functions'] += len(scanner.features['functions'])
            inventory['summary']['total_enums'] += len(scanner.features['enums'])
            inventory['summary']['total_dataclasses'] += len(scanner.features['dataclasses'])
            inventory['summary']['categories'][category]['classes'] += len(scanner.features['classes'])
            inventory['summary']['categories'][category]['functions'] += len(scanner.features['functions'])
            
            inventory['modules'][scanner.features['module']] = scanner.features
            
        except Exception as e:
            print(f"Error scanning {py_file}: {e}")
    
    return inventory


def generate_markdown_summary(inventory: Dict[str, Any]) -> str:
    """Generate markdown summary of the inventory."""
    md = []
    md.append("# AI Project Synthesizer - Feature Inventory\n")
    md.append(f"**Scan Date:** {inventory['scan_date']}\n")
    md.append(f"**Total Files:** {inventory['total_files']}\n")
    md.append(f"**Total Classes:** {inventory['summary']['total_classes']}\n")
    md.append(f"**Total Functions:** {inventory['summary']['total_functions']}\n")
    md.append(f"**Total Enums:** {inventory['summary']['total_enums']}\n")
    md.append(f"**Total Dataclasses:** {inventory['summary']['total_dataclasses']}\n\n")
    
    md.append("## Module Categories\n")
    for category, stats in inventory['summary']['categories'].items():
        md.append(f"### {category.title()}\n")
        md.append(f"- Files: {stats['files']}\n")
        md.append(f"- Classes: {stats['classes']}\n")
        md.append(f"- Functions: {stats['functions']}\n\n")
    
    md.append("## Detailed Module List\n")
    for module, features in inventory['modules'].items():
        md.append(f"### {module}\n")
        if features['docstring']:
            md.append(f"{features['docstring']}\n\n")
        
        if features['classes']:
            md.append("**Classes:**\n")
            for cls in features['classes']:
                md.append(f"- `{cls['name']}`")
                if cls['docstring']:
                    md.append(f": {cls['docstring'].split('.')[0]}")
                md.append("\n")
        
        if features['functions']:
            md.append("**Functions:**\n")
            for func in features['functions']:
                md.append(f"- `{func['name']}`")
                if func['docstring']:
                    md.append(f": {func['docstring'].split('.')[0]}")
                md.append("\n")
        
        md.append("\n")
    
    return ''.join(md)


if __name__ == "__main__":
    # Scan the src directory
    src_dir = Path(__file__).parent.parent / "src"
    inventory = scan_directory(src_dir)
    
    # Save JSON inventory
    output_file = Path(__file__).parent / "feature_inventory.json"
    with open(output_file, 'w') as f:
        json.dump(inventory, f, indent=2)
    
    # Generate markdown summary
    md_summary = generate_markdown_summary(inventory)
    md_file = Path(__file__).parent / "feature_inventory.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_summary)
    
    print(f"Inventory saved to {output_file}")
    print(f"Summary saved to {md_file}")
