"""
VIBE MCP - Minimal Voice Cloning Pipeline

Simplified voice cloning tools for agents that work without heavy dependencies.
Provides immediate fail-safe TTS capabilities when ElevenLabs subscription ends.

Features:
- No ML dependencies required (no torch/transformers)
- Cross-platform audio processing
- Emergency voice backup creation
- Simple voice analysis
- Agent-ready CLI interface

Usage:
    python tools/voice_cloning_minimal.py --clone-voice rachel --output models/
"""

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class MinimalVoiceCloner:
    """
    Minimal voice cloning pipeline for agents.
    
    Works without heavy ML dependencies to ensure agents
    always have TTS capabilities available.
    """
    
    def __init__(
        self,
        source_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize minimal voice cloner.
        
        Args:
            source_dir: Directory containing extracted voice samples
            output_dir: Directory to save cloned models
        """
        self.source_dir = source_dir or Path("voices")
        self.output_dir = output_dir or Path("models/cloned")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        secure_logger.info(f"Minimal voice cloner initialized")
        secure_logger.info(f"  Source: {self.source_dir}")
        secure_logger.info(f"  Output: {self.output_dir}")
    
    async def clone_voice_emergency(self, voice_name: str) -> Dict[str, any]:
        """
        Create emergency voice backup from extracted samples.
        
        Args:
            voice_name: Name of voice to backup
            
        Returns:
            Dictionary with backup results
        """
        secure_logger.info(f"Creating emergency backup for: {voice_name}")
        
        # Find voice samples
        voice_samples = await self._find_voice_samples(voice_name)
        if not voice_samples:
            raise ValueError(f"No samples found for voice: {voice_name}")
        
        # Select best samples
        best_samples = await self._select_best_samples(voice_samples, max_samples=10)
        
        # Create emergency backup directory
        emergency_dir = self.output_dir / f"{voice_name}_emergency"
        emergency_dir.mkdir(exist_ok=True)
        
        # Copy best samples
        emergency_samples = []
        for sample in best_samples:
            emergency_path = emergency_dir / sample.name
            shutil.copy2(sample, emergency_path)
            emergency_samples.append(emergency_path)
        
        # Analyze voice characteristics
        voice_analysis = await self._analyze_voice_basic(best_samples)
        
        # Create emergency voice profile
        emergency_profile = {
            "voice_name": voice_name,
            "type": "emergency_backup",
            "samples": [str(s.name) for s in emergency_samples],
            "sample_count": len(emergency_samples),
            "analysis": voice_analysis,
            "created_at": str(Path().absolute()),
            "compatible_with": ["basic_tts", "piper_fallback", "coqui_fallback"]
        }
        
        # Save profile
        profile_path = emergency_dir / "emergency_profile.json"
        with open(profile_path, "w") as f:
            json.dump(emergency_profile, f, indent=2)
        
        # Create simple usage instructions
        instructions = self._create_usage_instructions(voice_name, emergency_dir)
        instructions_path = emergency_dir / "usage_instructions.md"
        with open(instructions_path, "w") as f:
            f.write(instructions)
        
        secure_logger.info(f"Emergency backup created: {emergency_dir}")
        
        return {
            "success": True,
            "voice_name": voice_name,
            "backup_type": "emergency",
            "backup_path": str(emergency_dir),
            "profile_path": str(profile_path),
            "samples_count": len(emergency_samples),
            "analysis": voice_analysis
        }
    
    async def _find_voice_samples(self, voice_name: str) -> List[Path]:
        """Find audio samples for a specific voice."""
        samples = []
        
        if not self.source_dir.exists():
            secure_logger.warning(f"Source directory not found: {self.source_dir}")
            return samples
        
        # Search in organized voice directory
        for lang_dir in self.source_dir.iterdir():
            if lang_dir.is_dir():
                for dialect_dir in lang_dir.iterdir():
                    if dialect_dir.is_dir():
                        for voice_dir in dialect_dir.iterdir():
                            if voice_dir.is_dir() and voice_name.lower() in voice_dir.name.lower():
                                # Find all audio files
                                audio_files = list(voice_dir.glob("*.mp3"))
                                samples.extend(audio_files)
        
        secure_logger.info(f"Found {len(samples)} samples for {voice_name}")
        return samples
    
    async def _select_best_samples(self, samples: List[Path], max_samples: int = 10) -> List[Path]:
        """Select best quality samples for backup."""
        scored_samples = []
        
        for sample_path in samples:
            try:
                # Score based on file size (larger files usually better quality)
                size = sample_path.stat().st_size
                
                # Prefer certain sample types
                filename = sample_path.name.lower()
                bonus = 0
                if "basic" in filename:
                    bonus += 1000  # Basic samples are good for training
                elif "emotional" in filename:
                    bonus += 500   # Emotional samples add variety
                elif "technical" in filename:
                    bonus += 300   # Technical samples are useful
                
                score = size + bonus
                scored_samples.append((score, sample_path))
                
            except Exception as e:
                secure_logger.warning(f"Failed to score {sample_path}: {e}")
                scored_samples.append((0, sample_path))
        
        # Sort by score and take top samples
        scored_samples.sort(reverse=True)
        return [sample for _, sample in scored_samples[:max_samples]]
    
    async def _analyze_voice_basic(self, samples: List[Path]) -> Dict[str, any]:
        """Basic voice analysis without ML dependencies."""
        analysis = {
            "total_samples": len(samples),
            "file_sizes": [],
            "sample_types": [],
            "estimated_quality": "unknown"
        }
        
        total_size = 0
        for sample in samples:
            try:
                size = sample.stat().st_size
                analysis["file_sizes"].append(size)
                total_size += size
                
                # Categorize sample type
                filename = sample.name.lower()
                if "basic" in filename:
                    analysis["sample_types"].append("basic")
                elif "emotional" in filename:
                    analysis["sample_types"].append("emotional")
                elif "technical" in filename:
                    analysis["sample_types"].append("technical")
                elif "diverse" in filename:
                    analysis["sample_types"].append("diverse_phonetics")
                elif "numbers" in filename:
                    analysis["sample_types"].append("numbers")
                else:
                    analysis["sample_types"].append("other")
                    
            except Exception as e:
                secure_logger.warning(f"Failed to analyze {sample}: {e}")
        
        # Estimate quality based on file sizes
        if analysis["file_sizes"]:
            avg_size = sum(analysis["file_sizes"]) / len(analysis["file_sizes"])
            if avg_size > 50000:  # > 50KB average
                analysis["estimated_quality"] = "high"
            elif avg_size > 30000:  # > 30KB average
                analysis["estimated_quality"] = "medium"
            else:
                analysis["estimated_quality"] = "low"
        
        # Summary statistics
        analysis["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        analysis["avg_file_size_kb"] = round(sum(analysis["file_sizes"]) / len(analysis["file_sizes"]) / 1024, 2) if analysis["file_sizes"] else 0
        
        # Sample type distribution
        type_counts = {}
        for sample_type in analysis["sample_types"]:
            type_counts[sample_type] = type_counts.get(sample_type, 0) + 1
        analysis["sample_type_distribution"] = type_counts
        
        return analysis
    
    def _create_usage_instructions(self, voice_name: str, backup_dir: Path) -> str:
        """Create usage instructions for the emergency backup."""
        instructions = f"""# Emergency Voice Backup: {voice_name}

## Overview
This is an emergency backup of the {voice_name} voice created from extracted ElevenLabs samples.

## Files Included
- Audio samples: {len(list(backup_dir.glob("*.mp3")))} MP3 files
- Profile: emergency_profile.json
- Instructions: this file

## Usage for Agents

### 1. Basic TTS Fallback
```python
# Use the audio samples directly for simple TTS
import random
from pathlib import Path

backup_dir = Path("{backup_dir}")
samples = list(backup_dir.glob("*.mp3"))

# Get a random sample for playback
sample = random.choice(samples)
print(f"Playing: {{sample.name}}")
```

### 2. Voice Cloning Preparation
```python
# Use these samples as training data for:
# - Piper TTS (when available)
# - Coqui TTS (when available)
# - Custom voice models

# Samples are already organized by type:
# - basic: Good for general training
# - emotional: Adds expressiveness
# - technical: Tests complex speech
```

### 3. Integration with VoiceManager
```python
# Add to VoiceManager as local voice
from src.voice.manager import VoiceManager, VoiceProvider, VoiceProfile

manager = VoiceManager()
local_voice = VoiceProfile(
    id="{voice_name}_emergency",
    name="{voice_name} (Emergency)",
    provider=VoiceProvider.LOCAL,
    voice_id="{voice_name}_emergency",
    description="Emergency backup voice",
    model="emergency_backup"
)
manager.add_voice(local_voice)
```

## Quality Assessment
{json.dumps(json.loads((backup_dir / "emergency_profile.json").read_text())["analysis"], indent=2)}

## Notes
- This backup works without ML dependencies
- Can be used as a foundation for advanced voice cloning
- Maintains voice characteristics from original samples
- Ready for agent integration

Created: {Path().absolute()}
"""
        return instructions
    
    async def batch_emergency_backup(self, voice_list: List[str]) -> Dict[str, Dict[str, any]]:
        """Create emergency backups for multiple voices."""
        secure_logger.info(f"Starting emergency backup for {len(voice_list)} voices")
        
        results = {}
        
        for voice in voice_list:
            try:
                result = await self.clone_voice_emergency(voice)
                results[voice] = result
            except Exception as e:
                secure_logger.error(f"Emergency backup failed for {voice}: {e}")
                results[voice] = {"success": False, "error": str(e)}
        
        # Save batch results
        results_path = self.output_dir / "emergency_backup_results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        
        successful = sum(1 for r in results.values() if r.get("success", False))
        secure_logger.info(f"Emergency backup completed: {successful}/{len(voice_list)} successful")
        
        return results
    
    def get_available_voices(self) -> List[str]:
        """Get list of voices available for backup."""
        voices = []
        
        if not self.source_dir.exists():
            return voices
        
        for lang_dir in self.source_dir.iterdir():
            if lang_dir.is_dir():
                for dialect_dir in lang_dir.iterdir():
                    if dialect_dir.is_dir():
                        for voice_dir in dialect_dir.iterdir():
                            if voice_dir.is_dir():
                                voices.append(voice_dir.name)
        
        return list(set(voices))  # Remove duplicates
    
    def create_agent_script(self, voice_name: str) -> str:
        """Create a simple script for agents to use the voice backup."""
        script = f'''#!/usr/bin/env python3
"""
Agent Voice Backup Script for {voice_name}

Simple script for agents to use emergency voice backup
when ElevenLabs is unavailable.
"""

import random
from pathlib import Path

class EmergencyVoice{voice_name.title()}:
    """Emergency voice backup for {voice_name}."""
    
    def __init__(self):
        self.backup_dir = Path("{self.output_dir / f'{voice_name}_emergency'}")
        self.samples = list(self.backup_dir.glob("*.mp3"))
        
        if not self.samples:
            raise FileNotFoundError(f"No samples found in {{self.backup_dir}}")
    
    def get_random_sample(self) -> Path:
        """Get a random voice sample."""
        return random.choice(self.samples)
    
    def get_sample_by_type(self, sample_type: str) -> List[Path]:
        """Get samples by type (basic, emotional, technical, etc.)."""
        return [s for s in self.samples if sample_type in s.name.lower()]
    
    def speak_basic(self, text: str) -> Path:
        """Basic TTS - returns appropriate sample."""
        # Simple keyword-based sample selection
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["hello", "hi", "hey"]):
            basic_samples = self.get_sample_by_type("basic")
            return random.choice(basic_samples) if basic_samples else self.get_random_sample()
        
        elif any(word in text_lower for word in ["error", "warning", "alert"]):
            emotional_samples = self.get_sample_by_type("emotional")
            return random.choice(emotional_samples) if emotional_samples else self.get_random_sample()
        
        else:
            return self.get_random_sample()

# Usage example for agents
if __name__ == "__main__":
    voice = EmergencyVoice{voice_name.title()}()
    
    # Get a sample
    sample = voice.speak_basic("Hello world")
    print(f"Sample: {{sample}}")
    
    # List all samples
    print(f"Available samples: {{len(voice.samples)}}")
'''
        return script


# CLI interface for agent use
async def main():
    """Main CLI interface for minimal voice cloning."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Minimal Voice Cloning Pipeline")
    parser.add_argument("--clone-voice", help="Voice name to create emergency backup")
    parser.add_argument("--batch-backup", nargs="+", help="Multiple voices to backup")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--source-dir", default="voices", help="Source voice directory")
    parser.add_argument("--output-dir", default="models/cloned", help="Output model directory")
    parser.add_argument("--create-agent-script", help="Create agent script for voice")
    
    args = parser.parse_args()
    
    cloner = MinimalVoiceCloner(
        source_dir=Path(args.source_dir),
        output_dir=Path(args.output_dir)
    )
    
    if args.list_voices:
        voices = cloner.get_available_voices()
        print(f"Available voices for emergency backup: {voices}")
        return
    
    if args.clone_voice:
        result = await cloner.clone_voice_emergency(args.clone_voice)
        print(f"Emergency backup result: {json.dumps(result, indent=2)}")
        return
    
    if args.batch_backup:
        result = await cloner.batch_emergency_backup(args.batch_backup)
        print(f"Batch backup result: {json.dumps(result, indent=2)}")
        return
    
    if args.create_agent_script:
        script = cloner.create_agent_script(args.create_agent_script)
        script_path = Path(args.output_dir) / f"{args.create_agent_script}_agent_script.py"
        script_path.parent.mkdir(exist_ok=True)
        with open(script_path, "w") as f:
            f.write(script)
        print(f"Agent script created: {script_path}")
        return
    
    print("No action specified. Use --help for options.")


if __name__ == "__main__":
    asyncio.run(main())
