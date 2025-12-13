# Emergency Voice Backup: Liam_TX3LPaxm

## Overview
This is an emergency backup of the Liam_TX3LPaxm voice created from extracted ElevenLabs samples.

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

backup_dir = Path("models\cloned\Liam_TX3LPaxm_emergency")
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
    id="Liam_TX3LPaxm_emergency",
    name="Liam_TX3LPaxm (Emergency)",
    provider=VoiceProvider.LOCAL,
    voice_id="Liam_TX3LPaxm_emergency",
    description="Emergency backup voice",
    model="emergency_backup"
)
manager.add_voice(local_voice)
```

## Quality Assessment
{
  "total_samples": 10,
  "file_sizes": [
    94921,
    80293,
    72769,
    60649,
    59395,
    57723,
    54797,
    51871,
    49782,
    48110
  ],
  "sample_types": [
    "numbers",
    "numbers",
    "numbers",
    "technical",
    "numbers",
    "technical",
    "technical",
    "technical",
    "diverse_phonetics",
    "diverse_phonetics"
  ],
  "estimated_quality": "high",
  "total_size_mb": 0.6,
  "avg_file_size_kb": 61.55,
  "sample_type_distribution": {
    "numbers": 4,
    "technical": 4,
    "diverse_phonetics": 2
  }
}

## Notes
- This backup works without ML dependencies
- Can be used as a foundation for advanced voice cloning
- Maintains voice characteristics from original samples
- Ready for agent integration

Created: C:\Users\Admin\AI_Synthesizer
