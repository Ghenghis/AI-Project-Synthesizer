# Emergency Voice Backup: Will_bIHbv24M

## Overview
This is an emergency backup of the Will_bIHbv24M voice created from extracted ElevenLabs samples.

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

backup_dir = Path("models\cloned\Will_bIHbv24M_emergency")
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
    id="Will_bIHbv24M_emergency",
    name="Will_bIHbv24M (Emergency)",
    provider=VoiceProvider.LOCAL,
    voice_id="Will_bIHbv24M_emergency",
    description="Emergency backup voice",
    model="emergency_backup"
)
manager.add_voice(local_voice)
```

## Quality Assessment
{
  "total_samples": 10,
  "file_sizes": [
    84472,
    76531,
    63992,
    58559,
    58559,
    54797,
    52707,
    49782,
    48110,
    46020
  ],
  "sample_types": [
    "numbers",
    "numbers",
    "numbers",
    "technical",
    "numbers",
    "technical",
    "technical",
    "diverse_phonetics",
    "technical",
    "basic"
  ],
  "estimated_quality": "high",
  "total_size_mb": 0.57,
  "avg_file_size_kb": 57.96,
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
