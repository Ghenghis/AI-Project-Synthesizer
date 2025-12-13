#!/usr/bin/env python3
"""
VIBE MCP Quick Start Script

Gets you up and running with VIBE MCP in minutes.
"""

import asyncio
import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional


def print_banner():
    """Print welcome banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    VIBE MCP - Visual Intelligence Builder Environment       ║
║                                                              ║
║    Quick Start Script                                       ║
║    Gets you running in minutes                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


def check_python_version():
    """Check Python version requirement."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_system_requirements():
    """Check system requirements."""
    print("\n🔍 Checking system requirements...")
    
    # Check OS
    system = platform.system()
    print(f"✅ Operating System: {system}")
    
    # Check memory
    try:
        if system == "Linux":
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        mem_kb = int(line.split()[1])
                        mem_gb = mem_kb / 1024 / 1024
                        if mem_gb < 8:
                            print(f"⚠️  Warning: Only {mem_gb:.1f}GB RAM detected (8GB+ recommended)")
                        else:
                            print(f"✅ Memory: {mem_gb:.1f}GB RAM")
                        break
    except:
        print("⚠️  Could not check memory")
    
    # Check disk space
    try:
        home = Path.home()
        disk_usage = os.statvfs(home)
        free_gb = (disk_usage.f_frsize * disk_usage.f_bavail) / 1024 / 1024 / 1024
        if free_gb < 10:
            print(f"⚠️  Warning: Only {free_gb:.1f}GB free disk space (10GB+ recommended)")
        else:
            print(f"✅ Disk Space: {free_gb:.1f}GB free")
    except:
        print("⚠️  Could not check disk space")
    
    return True


def create_virtual_environment():
    """Create Python virtual environment."""
    print("\n🐍 Setting up Python environment...")
    
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
    else:
        print("Creating virtual environment...")
        result = subprocess.run([sys.executable, "-m", "venv", ".venv"])
        if result.returncode != 0:
            print("❌ Failed to create virtual environment")
            return False
        print("✅ Virtual environment created")
    
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing dependencies...")
    
    # Determine pip path
    if platform.system() == "Windows":
        pip_path = ".venv\\Scripts\\pip"
        python_path = ".venv\\Scripts\\python"
    else:
        pip_path = ".venv/bin/pip"
        python_path = ".venv/bin/python"
    
    # Upgrade pip
    print("Upgrading pip...")
    subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], 
                   capture_output=True)
    
    # Install requirements
    print("Installing Python packages...")
    result = subprocess.run([pip_path, "install", "-r", "requirements.txt"])
    if result.returncode != 0:
        print("❌ Failed to install dependencies")
        return False
    
    # Install Playwright browsers
    print("Installing Playwright browsers...")
    result = subprocess.run([pip_path, "install", "playwright"])
    if result.returncode == 0:
        subprocess.run([python_path, "-m", "playwright", "install"], 
                      capture_output=True)
    
    print("✅ Dependencies installed")
    return True


def setup_environment():
    """Setup environment configuration."""
    print("\n⚙️  Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            # Copy example
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Created .env from .env.example")
            print("\n⚠️  Please edit .env file with your API keys:")
            print("   - OPENAI_API_KEY (optional, for cloud LLM)")
            print("   - ELEVENLABS_API_KEY (optional, for premium voice)")
            print("   - GITLAB_TOKEN (optional, for GitLab integration)")
            print("   - FIRECRAWL_API_KEY (optional, for web scraping)")
        else:
            # Create minimal .env
            with open(env_file, "w") as f:
                f.write("""# VIBE MCP Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database (SQLite for quick start)
DATABASE_URL=sqlite:///./vibe_mcp.db

# Voice Configuration
VOICE_DEFAULT_PROVIDER=piper
VOICE_CACHE_DIR=./cache/voice

# Optional: Add your API keys below
# OPENAI_API_KEY=your_key_here
# ELEVENLABS_API_KEY=your_key_here
# GITLAB_TOKEN=your_token_here
# FIRECRAWL_API_KEY=your_key_here
""")
            print("✅ Created minimal .env file")
    else:
        print("✅ .env file already exists")
    
    return True


def download_models():
    """Download required AI models."""
    print("\n🧠 Downloading AI models...")
    
    # Determine python path
    if platform.system() == "Windows":
        python_path = ".venv\\Scripts\\python"
    else:
        python_path = ".venv/bin/python"
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Download voice models
    print("Downloading voice models (this may take a few minutes)...")
    result = subprocess.run([python_path, "scripts/download_voice_models.py"], 
                          capture_output=True)
    
    if result.returncode == 0:
        print("✅ Voice models downloaded")
    else:
        print("⚠️  Voice model download failed, will download on first use")
    
    return True


async def test_system():
    """Test system components."""
    print("\n🧪 Testing system components...")
    
    try:
        # Test imports
        print("Testing imports...")
        from src.voice.manager import VoiceManager
        from src.memory.mem0_integration import MemorySystem
        from src.llm.litellm_router import LiteLLMRouter
        from src.mcp.server import MCPServer
        print("✅ All imports successful")
        
        # Test voice system
        print("Testing voice system...")
        voice_manager = VoiceManager()
        await voice_manager.initialize()
        audio = await voice_manager.synthesize("System test complete")
        if audio is not None and len(audio) > 0:
            print("✅ Voice system working")
        await voice_manager.cleanup()
        
        # Test memory system
        print("Testing memory system...")
        memory = MemorySystem()
        memory_id = await memory.add("Quick start test memory")
        if memory_id:
            print("✅ Memory system working")
        
        # Test LLM router
        print("Testing LLM router...")
        llm_router = LiteLLMRouter()
        models = llm_router.list_models()
        if models:
            print(f"✅ LLM router has {len(models)} models available")
        
        print("\n🎉 All systems operational!")
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        print("\n⚠️  Some components may not work without additional setup")
        return False


def create_desktop_shortcut():
    """Create desktop shortcut (Windows only)."""
    if platform.system() != "Windows":
        return
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "VIBE MCP.lnk")
        target = os.path.join(os.getcwd(), "start_vibe_mcp.py")
        wDir = os.getcwd()
        icon = target
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()
        
        print("✅ Desktop shortcut created")
    except:
        print("⚠️  Could not create desktop shortcut")


def create_start_script():
    """Create start script for easy launching."""
    start_script = Path("start_vibe_mcp.py")
    
    if not start_script.exists():
        with open(start_script, "w") as f:
            f.write('''#!/usr/bin/env python3
"""Start VIBE MCP Server"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server import main

if __name__ == "__main__":
    print("Starting VIBE MCP Server...")
    asyncio.run(main())
''')
        
        # Make executable on Unix
        if platform.system() != "Windows":
            os.chmod(start_script, 0o755)
        
        print("✅ Created start_vibe_mcp.py script")


def print_next_steps():
    """Print next steps for the user."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                      🚀 Ready to Go!                        ║
╚══════════════════════════════════════════════════════════════╝

Next Steps:
1. Edit .env file with your API keys (optional)
2. Start the server:
   python start_vibe_mcp.py
   
3. Or run with voice chat:
   python -m src.voice.realtime_conversation

4. Read the documentation:
   - docs/USER_GUIDE.md - User guide
   - docs/DEVELOPER_GUIDE.md - Developer guide
   - docs/ARCHITECTURE.md - Architecture overview

5. Run tests:
   pytest tests/ -v

Need help?
- Join our Discord community
- Check docs/USER_GUIDE.md
- Report issues on GitHub

Thank you for using VIBE MCP! 🎉
    """)


async def main():
    """Main quick start process."""
    print_banner()
    
    # Check requirements
    if not check_python_version():
        sys.exit(1)
    
    check_system_requirements()
    
    # Setup environment
    if not create_virtual_environment():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    setup_environment()
    download_models()
    
    # Create convenience files
    create_start_script()
    create_desktop_shortcut()
    
    # Test system
    await test_system()
    
    # Show next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        print("\nPlease check the error above and try again.")
        sys.exit(1)
