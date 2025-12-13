"""
Code Analyzer - Extracts functions, classes, and signatures for test generation.
Uses AST parsing with multi-threaded file processing.
"""

import ast
import os
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from enum import Enum
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FunctionType(str, Enum):
    SYNC = "sync"
    ASYNC = "async"
    CLASSMETHOD = "classmethod"
    STATICMETHOD = "staticmethod"
    PROPERTY = "property"


class Complexity(str, Enum):
    LOW = "low"        # 1-5 branches
    MEDIUM = "medium"  # 6-15 branches
    HIGH = "high"      # 16+ branches


@dataclass
class Parameter:
    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None
    is_args: bool = False
    is_kwargs: bool = False


@dataclass
class FunctionInfo:
    name: str
    module_path: str
    class_name: Optional[str]
    function_type: FunctionType
    parameters: List[Parameter]
    return_annotation: Optional[str]
    docstring: Optional[str]
    decorators: List[str]
    line_number: int
    end_line: int
    complexity: Complexity
    raises: List[str]
    calls: List[str]
    imports_needed: List[str]
    is_private: bool
    is_dunder: bool
    source_hash: str
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['function_type'] = self.function_type.value
        d['complexity'] = self.complexity.value
        return d


@dataclass
class ClassInfo:
    name: str
    module_path: str
    bases: List[str]
    docstring: Optional[str]
    decorators: List[str]
    methods: List[FunctionInfo]
    class_variables: List[str]
    line_number: int
    end_line: int
    is_dataclass: bool
    is_enum: bool
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['methods'] = [m.to_dict() for m in self.methods]
        return d


@dataclass
class ModuleInfo:
    path: str
    relative_path: str
    imports: List[str]
    from_imports: List[Tuple[str, List[str]]]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    global_variables: List[str]
    docstring: Optional[str]
    
    def to_dict(self) -> Dict:
        return {
            'path': self.path,
            'relative_path': self.relative_path,
            'imports': self.imports,
            'from_imports': self.from_imports,
            'classes': [c.to_dict() for c in self.classes],
            'functions': [f.to_dict() for f in self.functions],
            'global_variables': self.global_variables,
            'docstring': self.docstring,
        }


class CodeAnalyzer:
    """Multi-threaded code analyzer for extracting testable components."""
    
    def __init__(self, project_root: str, max_workers: int = 16):
        self.project_root = Path(project_root)
        self.max_workers = max_workers
        self.modules: Dict[str, ModuleInfo] = {}
        self.all_functions: List[FunctionInfo] = []
        self.all_classes: List[ClassInfo] = []
        
    def analyze_project(self, src_dirs: List[str] = None) -> Dict[str, Any]:
        """Analyze entire project with multi-threading."""
        if src_dirs is None:
            src_dirs = ['src']
        
        python_files = []
        for src_dir in src_dirs:
            src_path = self.project_root / src_dir
            if src_path.exists():
                python_files.extend(src_path.rglob('*.py'))
        
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        # Multi-threaded file analysis
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._analyze_file, f): f 
                for f in python_files
            }
            
            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    module_info = future.result()
                    if module_info:
                        self.modules[module_info.relative_path] = module_info
                        self.all_functions.extend(module_info.functions)
                        for cls in module_info.classes:
                            self.all_classes.append(cls)
                            self.all_functions.extend(cls.methods)
                except Exception as e:
                    logger.warning(f"Error analyzing {file_path}: {e}")
        
        return self._generate_summary()
    
    def _analyze_file(self, file_path: Path) -> Optional[ModuleInfo]:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            relative_path = str(file_path.relative_to(self.project_root))
            
            # Extract module-level info
            imports = []
            from_imports = []
            classes = []
            functions = []
            global_vars = []
            docstring = ast.get_docstring(tree)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        names = [alias.name for alias in node.names]
                        from_imports.append((node.module, names))
            
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_info = self._analyze_class(node, relative_path, source)
                    classes.append(class_info)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_info = self._analyze_function(node, relative_path, None, source)
                    functions.append(func_info)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            global_vars.append(target.id)
            
            return ModuleInfo(
                path=str(file_path),
                relative_path=relative_path,
                imports=imports,
                from_imports=from_imports,
                classes=classes,
                functions=functions,
                global_variables=global_vars,
                docstring=docstring,
            )
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
            return None
    
    def _analyze_class(self, node: ast.ClassDef, module_path: str, source: str) -> ClassInfo:
        """Analyze a class definition."""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._get_attribute_name(base)}")
        
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        is_dataclass = 'dataclass' in decorators
        is_enum = any('Enum' in b for b in bases)
        
        methods = []
        class_vars = []
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._analyze_function(item, module_path, node.name, source)
                methods.append(func_info)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_vars.append(target.id)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                class_vars.append(item.target.id)
        
        return ClassInfo(
            name=node.name,
            module_path=module_path,
            bases=bases,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            methods=methods,
            class_variables=class_vars,
            line_number=node.lineno,
            end_line=node.end_lineno or node.lineno,
            is_dataclass=is_dataclass,
            is_enum=is_enum,
        )
    
    def _analyze_function(
        self, 
        node: ast.FunctionDef | ast.AsyncFunctionDef, 
        module_path: str, 
        class_name: Optional[str],
        source: str
    ) -> FunctionInfo:
        """Analyze a function definition."""
        # Determine function type
        func_type = FunctionType.ASYNC if isinstance(node, ast.AsyncFunctionDef) else FunctionType.SYNC
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        if 'classmethod' in decorators:
            func_type = FunctionType.CLASSMETHOD
        elif 'staticmethod' in decorators:
            func_type = FunctionType.STATICMETHOD
        elif 'property' in decorators:
            func_type = FunctionType.PROPERTY
        
        # Extract parameters
        parameters = self._extract_parameters(node.args)
        
        # Return annotation
        return_annotation = None
        if node.returns:
            return_annotation = self._get_annotation_string(node.returns)
        
        # Analyze complexity (count branches)
        complexity = self._calculate_complexity(node)
        
        # Find raised exceptions
        raises = self._find_raises(node)
        
        # Find function calls
        calls = self._find_calls(node)
        
        # Calculate source hash for change detection
        source_lines = source.split('\n')
        func_source = '\n'.join(source_lines[node.lineno-1:node.end_lineno or node.lineno])
        source_hash = hashlib.md5(func_source.encode()).hexdigest()[:8]
        
        # Determine imports needed for testing
        imports_needed = self._determine_imports_needed(node, module_path)
        
        return FunctionInfo(
            name=node.name,
            module_path=module_path,
            class_name=class_name,
            function_type=func_type,
            parameters=parameters,
            return_annotation=return_annotation,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            line_number=node.lineno,
            end_line=node.end_lineno or node.lineno,
            complexity=complexity,
            raises=raises,
            calls=calls,
            imports_needed=imports_needed,
            is_private=node.name.startswith('_') and not node.name.startswith('__'),
            is_dunder=node.name.startswith('__') and node.name.endswith('__'),
            source_hash=source_hash,
        )
    
    def _extract_parameters(self, args: ast.arguments) -> List[Parameter]:
        """Extract function parameters."""
        parameters = []
        
        # Regular args
        defaults_offset = len(args.args) - len(args.defaults)
        for i, arg in enumerate(args.args):
            default = None
            if i >= defaults_offset:
                default_node = args.defaults[i - defaults_offset]
                default = self._get_default_value(default_node)
            
            parameters.append(Parameter(
                name=arg.arg,
                annotation=self._get_annotation_string(arg.annotation) if arg.annotation else None,
                default=default,
            ))
        
        # *args
        if args.vararg:
            parameters.append(Parameter(
                name=args.vararg.arg,
                annotation=self._get_annotation_string(args.vararg.annotation) if args.vararg.annotation else None,
                is_args=True,
            ))
        
        # **kwargs
        if args.kwarg:
            parameters.append(Parameter(
                name=args.kwarg.arg,
                annotation=self._get_annotation_string(args.kwarg.annotation) if args.kwarg.annotation else None,
                is_kwargs=True,
            ))
        
        return parameters
    
    def _calculate_complexity(self, node: ast.AST) -> Complexity:
        """Calculate cyclomatic complexity."""
        branches = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                  ast.With, ast.Assert, ast.comprehension)):
                branches += 1
            elif isinstance(child, ast.BoolOp):
                branches += len(child.values) - 1
            elif isinstance(child, ast.Try):
                branches += len(child.handlers) + (1 if child.orelse else 0)
        
        if branches <= 5:
            return Complexity.LOW
        elif branches <= 15:
            return Complexity.MEDIUM
        else:
            return Complexity.HIGH
    
    def _find_raises(self, node: ast.AST) -> List[str]:
        """Find all exceptions raised in a function."""
        raises = []
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc:
                    if isinstance(child.exc, ast.Call):
                        if isinstance(child.exc.func, ast.Name):
                            raises.append(child.exc.func.id)
                        elif isinstance(child.exc.func, ast.Attribute):
                            raises.append(child.exc.func.attr)
                    elif isinstance(child.exc, ast.Name):
                        raises.append(child.exc.id)
        return list(set(raises))
    
    def _find_calls(self, node: ast.AST) -> List[str]:
        """Find all function calls in a function."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return list(set(calls))
    
    def _determine_imports_needed(self, node: ast.AST, module_path: str) -> List[str]:
        """Determine what imports are needed to test this function."""
        imports = []
        module_name = module_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        imports.append(module_name)
        
        # Add pytest
        imports.append('pytest')
        
        # Check for async
        if isinstance(node, ast.AsyncFunctionDef):
            imports.append('pytest_asyncio')
        
        return imports
    
    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get decorator name as string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        elif isinstance(node, ast.Attribute):
            return node.attr
        return str(node)
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr
    
    def _get_annotation_string(self, node: ast.expr) -> Optional[str]:
        """Convert annotation AST to string."""
        if node is None:
            return None
        try:
            return ast.unparse(node)
        except:
            return None
    
    def _get_default_value(self, node: ast.expr) -> Optional[str]:
        """Get default value as string."""
        try:
            return ast.unparse(node)
        except:
            return None
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate analysis summary."""
        return {
            'total_modules': len(self.modules),
            'total_classes': len(self.all_classes),
            'total_functions': len(self.all_functions),
            'functions_by_complexity': {
                'low': len([f for f in self.all_functions if f.complexity == Complexity.LOW]),
                'medium': len([f for f in self.all_functions if f.complexity == Complexity.MEDIUM]),
                'high': len([f for f in self.all_functions if f.complexity == Complexity.HIGH]),
            },
            'async_functions': len([f for f in self.all_functions if f.function_type == FunctionType.ASYNC]),
            'private_functions': len([f for f in self.all_functions if f.is_private]),
            'functions_with_exceptions': len([f for f in self.all_functions if f.raises]),
        }
    
    def save_analysis(self, output_path: str):
        """Save analysis to JSON file."""
        data = {
            'summary': self._generate_summary(),
            'modules': {k: v.to_dict() for k, v in self.modules.items()},
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Analysis saved to {output_path}")


if __name__ == "__main__":
    import sys
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    analyzer = CodeAnalyzer(project_root)
    summary = analyzer.analyze_project()
    print(json.dumps(summary, indent=2))
    analyzer.save_analysis("code_analysis.json")
