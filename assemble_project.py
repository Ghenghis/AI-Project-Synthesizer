"""
Assemble a Complete Project

Automatically:
1. Searches GitHub, HuggingFace, Kaggle for compatible resources
2. Downloads code, models (.safetensors), datasets
3. Creates organized folder structure on G:\
4. Generates README, requirements.txt
5. Creates GitHub repo
6. Prepares for Windsurf IDE

Usage:
    python assemble_project.py "RAG chatbot with local LLM"
    python assemble_project.py "image classification with PyTorch" --name my-classifier
    python assemble_project.py "discord bot with AI" --output D:/projects --no-github
"""

import asyncio
import argparse
from pathlib import Path

async def main():
    parser = argparse.ArgumentParser(
        description="Assemble a complete project from an idea",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python assemble_project.py "RAG chatbot with local LLM"
  python assemble_project.py "image classifier" --name my-classifier
  python assemble_project.py "discord bot" --output D:/projects
        """
    )
    
    parser.add_argument("idea", help="Project idea/description")
    parser.add_argument("--name", "-n", help="Project name (auto-generated if not provided)")
    parser.add_argument("--output", "-o", default="G:/", help="Output directory (default: G:/)")
    parser.add_argument("--no-github", action="store_true", help="Don't create GitHub repo")
    parser.add_argument("--no-models", action="store_true", help="Don't download models")
    parser.add_argument("--no-datasets", action="store_true", help="Don't download datasets")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI PROJECT SYNTHESIZER - PROJECT ASSEMBLER")
    print("=" * 60)
    print(f"\nIdea: {args.idea}")
    print(f"Output: {args.output}")
    print(f"Create GitHub: {not args.no_github}")
    print()
    
    from src.synthesis.project_assembler import ProjectAssembler, AssemblerConfig
    
    config = AssemblerConfig(
        base_output_dir=Path(args.output),
        create_github_repo=not args.no_github,
        download_models=not args.no_models,
        download_datasets=not args.no_datasets,
    )
    
    assembler = ProjectAssembler(config)
    
    print("🔍 Searching for resources...")
    project = await assembler.assemble(args.idea, args.name)
    
    print("\n" + "=" * 60)
    print("✅ PROJECT ASSEMBLED!")
    print("=" * 60)
    print(f"\n📁 Location: {project.base_path}")
    
    if project.github_repo_url:
        print(f"🐙 GitHub: {project.github_repo_url}")
    
    print(f"\n📦 Resources:")
    print(f"   - {len(project.code_repos)} code repositories")
    print(f"   - {len(project.models)} AI models")
    print(f"   - {len(project.datasets)} datasets")
    print(f"   - {len(project.papers)} research papers")
    
    print(f"\n📋 Generated files:")
    print(f"   - README.md")
    print(f"   - requirements.txt")
    print(f"   - .gitignore")
    print(f"   - .windsurf/config.json")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. Open {project.base_path} in Windsurf IDE")
    print(f"   2. Review the assembled resources")
    print(f"   3. Let Windsurf help you integrate everything!")
    
    return project

if __name__ == "__main__":
    asyncio.run(main())
