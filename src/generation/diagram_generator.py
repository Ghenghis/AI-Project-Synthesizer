"""
AI Project Synthesizer - Diagram Generator

Generates Mermaid diagrams for architecture visualization.
"""

import logging
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DiagramConfig:
    """Configuration for diagram generation."""
    project_name: str
    components: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    diagram_types: List[str] = field(default_factory=lambda: ["architecture", "flow"])


class DiagramGenerator:
    """
    Generates Mermaid diagrams for documentation.
    
    Diagram types:
    - architecture: High-level system overview
    - flow: Data flow diagram
    - class: Class relationships
    - sequence: Interaction sequences
    
    Usage:
        generator = DiagramGenerator()
        diagrams = generator.generate(config)
        for name, content in diagrams.items():
            Path(f"docs/{name}.mermaid").write_text(content)
    """

    def generate(
        self,
        config: DiagramConfig,
    ) -> Dict[str, str]:
        """
        Generate diagrams based on configuration.
        
        Args:
            config: Diagram configuration
            
        Returns:
            Dictionary of diagram_name -> mermaid_content
        """
        diagrams = {}

        if "architecture" in config.diagram_types:
            diagrams["architecture"] = self._generate_architecture(config)

        if "flow" in config.diagram_types:
            diagrams["data_flow"] = self._generate_flow(config)

        if "component" in config.diagram_types:
            diagrams["components"] = self._generate_components(config)

        return diagrams

    def _generate_architecture(self, config: DiagramConfig) -> str:
        """Generate architecture diagram."""
        diagram = f"""graph TB
    subgraph {config.project_name}["🏗️ {config.project_name}"]
"""

        # Add components
        for i, component in enumerate(config.components):
            safe_id = component.replace(" ", "_").replace("-", "_")
            diagram += f"        {safe_id}[\"{component}\"]\n"

        diagram += "    end\n"

        # Add dependency connections
        for source, targets in config.dependencies.items():
            source_id = source.replace(" ", "_").replace("-", "_")
            for target in targets:
                target_id = target.replace(" ", "_").replace("-", "_")
                diagram += f"    {source_id} --> {target_id}\n"

        # Add styling
        diagram += """
    style """ + config.project_name.replace(" ", "_") + """ fill:#e1f5fe
"""

        return diagram

    def _generate_flow(self, config: DiagramConfig) -> str:
        """Generate data flow diagram."""
        diagram = """flowchart LR
    subgraph Input["📥 Input"]
        USER[User Request]
    end
    
    subgraph Processing["⚙️ Processing"]
"""

        # Add components as processing steps
        prev_id = "USER"
        for i, component in enumerate(config.components):
            safe_id = f"PROC_{i}"
            diagram += f"        {safe_id}[\"{component}\"]\n"
            diagram += f"    {prev_id} --> {safe_id}\n"
            prev_id = safe_id

        diagram += """    end
    
    subgraph Output["📤 Output"]
        RESULT[Result]
    end
    
"""
        diagram += f"    {prev_id} --> RESULT\n"

        return diagram

    def _generate_components(self, config: DiagramConfig) -> str:
        """Generate component diagram."""
        diagram = f"""graph TB
    subgraph System["{config.project_name}"]
        direction TB
"""

        for i, component in enumerate(config.components):
            safe_id = component.replace(" ", "_").replace("-", "_")
            diagram += f"        {safe_id}[[\"{component}\"]]\n"

        diagram += "    end\n"

        return diagram

    def generate_from_codebase(
        self,
        project_path: Path,
    ) -> Dict[str, str]:
        """
        Auto-generate diagrams by analyzing codebase.
        
        Args:
            project_path: Path to project
            
        Returns:
            Generated diagrams
        """
        # Discover components
        components = []
        dependencies = {}

        src_path = project_path / "src"
        if src_path.exists():
            for item in src_path.iterdir():
                if item.is_dir() and not item.name.startswith("_"):
                    components.append(item.name)

        # Create config
        config = DiagramConfig(
            project_name=project_path.name,
            components=components,
            dependencies=dependencies,
            diagram_types=["architecture", "flow", "component"],
        )

        return self.generate(config)

    def save_diagrams(
        self,
        diagrams: Dict[str, str],
        output_dir: Path,
    ) -> List[Path]:
        """
        Save diagrams to files.
        
        Args:
            diagrams: Diagram content by name
            output_dir: Output directory
            
        Returns:
            List of created file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        created = []

        for name, content in diagrams.items():
            file_path = output_dir / f"{name}.mermaid"
            file_path.write_text(content)
            created.append(file_path)
            logger.info(f"Created diagram: {file_path}")

        return created
