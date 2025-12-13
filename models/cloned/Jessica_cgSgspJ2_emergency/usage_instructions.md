# Emergency Voice Backup: Jessica_cgSgspJ2

## Overview
This is an emergency backup of the Jessica_cgSgspJ2 voice created from extracted ElevenLabs samples.

## Files Included
- Audio samples: 10 MP3 files
- Profile: emergency_profile.json
- Instructions: this file

## Usage for Agents

### 1. Basic TTS Fallback
```python
# Use the audio samples directly for simple TTS
import random
from pathlib import Path

backup_dir = Path("models\cloned\Jessica_cgSgspJ2_emergency")
samples = list(backup_dir.glob("*.mp3"))

# Get a random sample for playback
sample = random.choice(samples)
print(f"Playing: {sample.name}")
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
    id="Jessica_cgSgspJ2_emergency",
    name="Jessica_cgSgspJ2 (Emergency)",
    provider=VoiceProvider.LOCAL,
    voice_id="Jessica_cgSgspJ2_emergency",
    description="Emergency backup voice",
    model="emergency_backup"
)
manager.add_voice(local_voice)
```

## Quality Assessment
{
  "total_samples": 10,
  "file_sizes": [
    116655,
    97847,
    80711,
    61485,
    57723,
    56469,
    50618,
    47274,
    46856,
    44348
  ],
  "sample_types": [
    "numbers",
    "numbers",
    "numbers",
    "numbers",
    "technical",
    "technical",
    "technical",
    "diverse_phonetics",
    "technical",
    "basic"
  ],
  "estimated_quality": "high",
  "total_size_mb": 0.63,
  "avg_file_size_kb": 64.45,
  "sample_type_distribution": {
    "numbers": 4,
    "technical": 4,
    "diverse_phonetics": 1,
    "basic": 1
  }
}

## Notes
- This backup works without ML dependencies
- Can be used as a foundation for advanced voice cloning
- Maintains voice characteristics from original samples
- Ready for agent integration

Created: C:\Users\Admin\AI_Synthesizer
