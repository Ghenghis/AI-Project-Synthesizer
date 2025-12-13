#!/usr/bin/env python3
"""
VIBE MCP - Project Status Health Check

Validates current phase dependencies and key files exist.
Run this script before starting new work to ensure project is ready.

Usage:
    python scripts/check_project_status.py
"""

import sys
from pathlib import Path
import importlib.util
from typing import Dict, List, Tuple


class ProjectHealthChecker:
    """Validates project status and dependencies."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.current_phase = "Phase 3: Agent Framework Integration"
        self.errors = []
        self.warnings = []
        
    def check_all(self) -> bool:
        """Run all health checks."""
        print("🔍 VIBE MCP Project Health Check")
        print("=" * 50)
        
        checks = [
            self.check_current_plan,
            self.check_phase2_completion,
            self.check_dependencies,
            self.check_key_files,
            self.check_voice_system,
            self.check_storage_usage,
            self.check_phase3_readiness
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.errors.append(f"Health check failed: {e}")
        
        self.print_results()
        return len(self.errors) == 0
    
    def check_current_plan(self):
        """Check CURRENT_PLAN.md exists and is readable."""
        plan_file = self.project_root / "CURRENT_PLAN.md"
        
        if not plan_file.exists():
            self.errors.append("CURRENT_PLAN.md not found - project tracking lost!")
            return
        
        content = plan_file.read_text()
        if "v1.0 - December 11, 2025" not in content:
            self.warnings.append("CURRENT_PLAN.md version outdated")
        
        if "Phase 3: Agent Framework Integration" not in content:
            self.errors.append("CURRENT_PLAN.md doesn't show current phase")
        
        print("✅ Project plan tracking verified")
    
    def check_phase2_completion(self):
        """Verify Phase 2 (Voice System) is completed."""
        required_files = [
            "src/voice/tts/piper_client.py",
            "src/voice/asr/glm_asr_client.py", 
            "src/voice/manager.py",
            "tools/voice_cloning_pipeline.py",
            "tools/voice_cloning_minimal.py"
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.errors.append(f"Phase 2 file missing: {file_path}")
        
        print("✅ Phase 2 voice system files verified")
    
    def check_dependencies(self):
        """Check critical dependencies are installed."""
        critical_deps = [
            ("librosa", "Audio processing"),
            ("soundfile", "Audio file I/O"),
            ("transformers", "GLM-ASR ML framework"),
            ("torch", "PyTorch for GLM-ASR")
        ]
        
        for dep, description in critical_deps:
            try:
                spec = importlib.util.find_spec(dep)
                if spec is None:
                    self.warnings.append(f"{dep} not installed ({description})")
                else:
                    print(f"✅ {dep} installed ({description})")
            except ImportError:
                self.warnings.append(f"{dep} not available ({description})")
    
    def check_key_files(self):
        """Verify key project files exist."""
        key_files = [
            "src/cli.py",
            "src/core/config.py", 
            "src/mcp_server/server.py",
            "requirements.txt",
            ".env.example"
        ]
        
        for file_path in key_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.errors.append(f"Key project file missing: {file_path}")
        
        print("✅ Key project files verified")
    
    def check_voice_system(self):
        """Check voice system emergency backups."""
        models_dir = self.project_root / "models" / "cloned"
        
        if not models_dir.exists():
            self.errors.append("Voice backup directory missing")
            return
        
        emergency_backups = list(models_dir.glob("*_emergency"))
        if len(emergency_backups) < 20:
            self.warnings.append(f"Only {len(emergency_backups)}/20 emergency voice backups found")
        
        # Check backup integrity
        valid_backups = 0
        for backup_dir in emergency_backups:
            profile_file = backup_dir / "emergency_profile.json"
            if profile_file.exists():
                valid_backups += 1
        
        if valid_backups < 20:
            self.warnings.append(f"Only {valid_backups}/20 emergency backups have valid profiles")
        
        print(f"✅ Voice system: {valid_backups}/20 emergency backups ready")
    
    def check_storage_usage(self):
        """Check storage usage of voice backups."""
        models_dir = self.project_root / "models" / "cloned"
        
        if models_dir.exists():
            total_size = sum(f.stat().st_size for f in models_dir.rglob("*") if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            if size_mb > 50:
                self.warnings.append(f"Voice backups use {size_mb:.1f}MB - consider cleanup")
            else:
                print(f"✅ Storage usage: {size_mb:.1f}MB (within limits)")
    
    def check_phase3_readiness(self):
        """Check readiness for Phase 3 (Agent Framework Integration)."""
        agents_dir = self.project_root / "src" / "agents"
        
        if not agents_dir.exists():
            self.warnings.append("src/agents directory not created yet")
        else:
            print("✅ Agents directory ready for Phase 3")
        
        # Check if AutoGen is available (next dependency)
        try:
            spec = importlib.util.find_spec("autogen")
            if spec is None:
                self.warnings.append("AutoGen not installed - needed for Phase 3.1")
            else:
                print("✅ AutoGen available for Phase 3.1")
        except ImportError:
            self.warnings.append("AutoGen not available - needed for Phase 3.1")
    
    def print_results(self):
        """Print health check results."""
        print("\n" + "=" * 50)
        print("HEALTH CHECK RESULTS")
        print("=" * 50)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.errors and not self.warnings:
            print("\n🎉 All checks passed! Project is healthy.")
        
        if not self.errors:
            print(f"\n✅ Ready for {self.current_phase}")
            print("\n📋 Next Steps:")
            print("   1. Install AutoGen: pip install pyautogen")
            print("   2. Create src/agents/autogen_integration.py")
            print("   3. Implement multi-agent conversations")
        else:
            print(f"\n🚧 Fix issues before starting {self.current_phase}")
        
        print(f"\n📖 Reference: CURRENT_PLAN.md")


def main():
    """Run project health check."""
    checker = ProjectHealthChecker()
    success = checker.check_all()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
