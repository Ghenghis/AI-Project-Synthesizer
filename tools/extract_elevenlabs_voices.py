"""
VIBE MCP - ElevenLabs Voice Extraction Tool

URGENT: Extract voice samples from ElevenLabs before subscription ends.
Generates comprehensive voice samples for local cloning with Piper TTS or other open-source TTS.

Usage:
    python tools/extract_elevenlabs_voices.py --voice-ids all --output-dir voice_samples/
    python tools/extract_elevenlabs_voices.py --voice-ids 21m00Tcm4TlvDq8ikWAM --samples comprehensive

Features:
- Bulk voice sample generation
- Diverse phonetic coverage for better cloning
- Metadata export for voice characteristics
- Progress tracking and resume capability
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config import get_settings
from src.voice.elevenlabs_client import ElevenLabsClient, create_elevenlabs_client

logger = logging.getLogger(__name__)


class VoiceExtractor:
    """Extracts voice samples from ElevenLabs for local cloning."""
    
    def __init__(self, dry_run: bool = False):
        """Initialize the voice extractor."""
        self.settings = get_settings()
        self.client: Optional[ElevenLabsClient] = None
        self.output_dir = Path("voices")  # Changed to "voices" folder
        self.metadata = {}
        self.dry_run = dry_run
        
        # Language mapping from ElevenLabs labels
        self.language_mapping = {
            "english": "english",
            "en": "english", 
            "spanish": "spanish",
            "es": "spanish",
            "french": "french",
            "fr": "french",
            "german": "german",
            "de": "german",
            "italian": "italian",
            "it": "italian",
            "portuguese": "portuguese",
            "pt": "portuguese",
            "chinese": "chinese",
            "zh": "chinese",
            "japanese": "japanese",
            "ja": "japanese",
        }
        
        # English dialect mapping
        self.english_dialect_mapping = {
            "american": "american",
            "us": "american",
            "usa": "american",
            "british": "british",
            "uk": "british",
            "australian": "australian",
            "au": "australian",
            "indian": "indian",
            "irish": "irish",
            "scottish": "scottish",
            "canadian": "canadian",
        }
        
        # Comprehensive test phrases for voice cloning
        self.test_phrases = {
            "basic": [
                "Hello, this is a test of my voice.",
                "The quick brown fox jumps over the lazy dog.",
                "I enjoy speaking in different tones and styles.",
                "This voice will be used for local text-to-speech.",
            ],
            "emotional": [
                "I'm excited to help you with your projects!",
                "This is concerning and needs attention.",
                "What a wonderful achievement this is.",
                "I'm curious about how this will work out.",
                "This makes me happy to see.",
            ],
            "technical": [
                "The API endpoint returns JSON data with status codes.",
                "Initialize the database connection before executing queries.",
                "Deploy the container using Docker Compose configuration.",
                "The neural network processes audio in real-time.",
            ],
            "diverse_phonetics": [
                "Peter Piper picked a peck of pickled peppers.",
                "How much wood would a woodchuck chuck?",
                "Sally sells seashells by the seashore.",
                "The sixth sick sheikh's sixth sheep's sick.",
                "Unique New York, you know you need unique New York.",
            ],
            "numbers_and_symbols": [
                "The price is $19.99, with a 20% discount.",
                "Call me at 555-123-4567 or email user@example.com.",
                "Version 2.0.1-beta was released on 12/11/2025.",
                "The ratio is 3.14159:1, approximately.",
            ]
        }
    
    async def initialize(self):
        """Initialize the ElevenLabs client."""
        try:
            self.client = create_elevenlabs_client()
            if self.client:
                print(f"✅ ElevenLabs client initialized")
                return True
            else:
                print(f"❌ ElevenLabs API key not configured")
                return False
        except Exception as e:
            print(f"❌ Failed to initialize ElevenLabs client: {e}")
            return False
    
    def get_voice_language_dialect(self, voice) -> tuple[str, str]:
        """Extract language and dialect from voice metadata."""
        # Default to english/american if no metadata found
        language = "english"
        dialect = "american"
        
        # Check voice labels for language info
        if hasattr(voice, 'labels') and voice.labels:
            labels = voice.labels
            
            # Extract language
            for key, value in labels.items():
                key_lower = key.lower()
                value_lower = value.lower()
                
                # Check for language
                if 'language' in key_lower or 'accent' in key_lower:
                    for lang_key, lang_value in self.language_mapping.items():
                        if lang_key in value_lower or lang_key in key_lower:
                            language = lang_value
                            break
                
                # Check for English dialects specifically
                if language == "english":
                    for dialect_key, dialect_value in self.english_dialect_mapping.items():
                        if dialect_key in value_lower or dialect_key in key_lower:
                            dialect = dialect_value
                            break
        
        # Fallback: check description for language clues
        if hasattr(voice, 'description') and voice.description:
            desc_lower = voice.description.lower()
            
            # Language detection from description
            for lang_key, lang_value in self.language_mapping.items():
                if lang_key in desc_lower:
                    language = lang_value
                    break
            
            # English dialect detection from description
            if language == "english":
                for dialect_key, dialect_value in self.english_dialect_mapping.items():
                    if dialect_key in desc_lower:
                        dialect = dialect_value
                        break
        
        return language, dialect
    
    async def get_available_voices(self) -> List[Dict]:
        """Get list of available ElevenLabs voices."""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        try:
            voices = await self.client.get_voices()
            
            # Group voices by language and dialect for reporting
            language_groups = {}
            for voice in voices:
                lang, dialect = self.get_voice_language_dialect(voice)
                if lang not in language_groups:
                    language_groups[lang] = {}
                if dialect not in language_groups[lang]:
                    language_groups[lang][dialect] = []
                language_groups[lang][dialect].append(voice)
            
            print(f"📋 Found {len(voices)} available voices:")
            for lang, dialects in sorted(language_groups.items()):
                print(f"   {lang.title()}:")
                for dialect, voices_list in sorted(dialects.items()):
                    print(f"     {dialect.title()}: {len(voices_list)} voices")
            
            return voices
        except Exception as e:
            print(f"❌ Failed to get voices: {e}")
            return []
    
    async def generate_voice_samples(self, voice) -> bool:
        """Generate comprehensive samples for a specific voice."""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        voice_id = voice.voice_id
        voice_name = voice.name
        
        # Get language and dialect for folder organization
        language, dialect = self.get_voice_language_dialect(voice)
        
        # Create organized folder structure: voices/language/dialect/voice_name/
        voice_dir = self.output_dir / language / dialect / f"{voice_name.replace(' ', '_')}_{voice_id[:8]}"
        voice_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🎤 Generating samples for {voice_name} ({voice_id})")
        print(f"   📂 Organized as: {language.title()}/{dialect.title()}/")
        
        voice_metadata = {
            "voice_id": voice_id,
            "voice_name": voice_name,
            "extraction_date": datetime.now().isoformat(),
            "samples": {},
            "settings": {}
        }
        
        try:
            # Get voice settings if available
            # Note: This would need to be implemented in ElevenLabsClient
            # voice_metadata["settings"] = await self.client.get_voice_settings(voice_id)
            
            success_count = 0
            total_count = 0
            
            for category, phrases in self.test_phrases.items():
                print(f"   📝 Generating {category} samples...")
                category_samples = []
                
                for i, phrase in enumerate(phrases):
                    total_count += 1
                    filename = f"{category}_{i+1:02d}.mp3"
                    filepath = voice_dir / filename
                    
                    # Skip if already exists
                    if filepath.exists():
                        print(f"      ✅ {filename} (already exists)")
                        success_count += 1
                        continue
                    
                    try:
                        if self.dry_run:
                            # Dry run - simulate without API call
                            print(f"      🔄 DRY RUN: Would generate {filename}")
                            success_count += 1
                        else:
                            # Generate audio
                            audio_data = await self.client.text_to_speech(
                                text=phrase,
                                voice=voice_id,
                                model="eleven_multilingual_v2"
                            )
                            
                            # Save audio file
                            with open(filepath, "wb") as f:
                                f.write(audio_data)
                            
                            # Save transcript
                            transcript_file = filepath.with_suffix(".txt")
                            with open(transcript_file, "w") as f:
                                f.write(phrase)
                            
                            print(f"      ✅ {filename}")
                            success_count += 1
                            
                            # Rate limiting
                            await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        print(f"      ❌ Failed to generate {filename}: {e}")
                        continue
                    
                    category_samples.append({
                        "filename": filename,
                        "text": phrase,
                        "category": category
                    })
                
                voice_metadata["samples"][category] = category_samples
            
            # Save metadata
            metadata_file = voice_dir / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(voice_metadata, f, indent=2)
            
            print(f"   📊 Generated {success_count}/{total_count} samples")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Failed to generate samples for {voice_name}: {e}")
            return False
    
    async def extract_all_voices(self, voice_ids: Optional[List[str]] = None):
        """Extract samples for specified voices or all voices."""
        if not await self.initialize():
            return
        
        voices = await self.get_available_voices()
        if not voices:
            return
        
        # Filter voices if specified
        if voice_ids and voice_ids != ["all"]:
            # Create mapping of aliases to voice IDs
            alias_map = {
                "rachel": "21m00Tcm4TlvDq8ikWAM",
                "domi": "AZnzlk1XvdvUeBnXmlld",
                "bella": "EXAVITQu4vr4xnSDxMaL",
                "antoni": "ErXwobaYiN019PkySvjV",
                "elli": "MF3mGyEYCl7XYWbV9V6O",
                "josh": "TxGEqnHWrfWFTfGW9XjX",
                "arnold": "VR6AewLTigWG4xSOukaG",
                "adam": "pNInz6obpgDQGcFmaJgB",
                "sam": "yoZ06aMxZJJ28mfd3POQ",
            }
            
            # Convert aliases to voice IDs and names
            target_ids = []
            target_names = []
            for vid in voice_ids:
                if vid in alias_map:
                    target_ids.append(alias_map[vid])
                else:
                    target_ids.append(vid)
                # Also add as lowercase name for matching
                target_names.append(vid.lower())
            
            # Filter by voice ID or name
            voices = [v for v in voices 
                     if v.voice_id in target_ids or 
                     v.name.lower() in target_names]
        
        print(f"\n🎯 Processing {len(voices)} voices")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Process each voice
        results = {}
        for voice in voices:
            voice_id = voice.voice_id
            voice_name = voice.name
            
            success = await self.generate_voice_samples(voice)
            language, dialect = self.get_voice_language_dialect(voice)
            results[voice_id] = {
                "name": voice_name,
                "language": language,
                "dialect": dialect,
                "success": success
            }
        
        # Generate summary report
        await self.generate_summary_report(results)
    
    async def generate_summary_report(self, results: Dict):
        """Generate a summary report of the extraction process."""
        report = {
            "extraction_summary": {
                "date": datetime.now().isoformat(),
                "total_voices": len(results),
                "successful": sum(1 for r in results.values() if r["success"]),
                "failed": sum(1 for r in results.values() if not r["success"])
            },
            "voices": results,
            "next_steps": {
                "voice_cloning": "Use samples with Coqui TTS or RVC for local models",
                "piper_training": "Convert samples to Piper-compatible format",
                "quality_assessment": "Review generated samples for clarity"
            }
        }
        
        report_file = self.output_dir / "extraction_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Extraction Summary:")
        print(f"   Total voices: {report['extraction_summary']['total_voices']}")
        print(f"   Successful: {report['extraction_summary']['successful']}")
        print(f"   Failed: {report['extraction_summary']['failed']}")
        print(f"   Report saved to: {report_file}")


async def main():
    """Main extraction process."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract ElevenLabs voices for local use")
    parser.add_argument("--voice-ids", nargs="+", default=["all"], 
                       help="Voice IDs to extract (default: all)")
    parser.add_argument("--output-dir", default="voice_samples",
                       help="Output directory for voice samples")
    parser.add_argument("--dry-run", action="store_true",
                       help="Test without consuming API quota")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("VIBE MCP - ElevenLabs Voice Extraction")
    print("=" * 60)
    if args.dry_run:
        print("🔄 DRY RUN MODE - No API calls will be made")
    else:
        print("⚠️  URGENT: Extracting voices before subscription ends")
    print("=" * 60)
    
    extractor = VoiceExtractor(dry_run=args.dry_run)
    extractor.output_dir = Path(args.output_dir)
    
    await extractor.extract_all_voices(args.voice_ids)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    asyncio.run(main())
