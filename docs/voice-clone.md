# Building an Enterprise-Grade GPU-Accelerated Voice Dataset System

**Your RTX 3090 Ti (24GB) and RTX 3060 (12GB) can process hundreds of thousands of audio files for voice cloning when architected correctly.** This comprehensive guide covers the complete technology stack—from GPU-accelerated audio processing and speaker embedding extraction to rare dataset sources and production system architecture. The key insight is task-based GPU distribution: use the 3090 Ti for computationally intensive embedding models while the 3060 handles preprocessing, with modern libraries like NVIDIA NeMo, pyannote-audio, and FAISS enabling real-time voice fingerprint databases at scale.

---

## GPU-accelerated audio processing with CUDA 12

Modern voice cloning pipelines benefit enormously from GPU acceleration, particularly for spectrogram computation, pitch detection, and batch embedding extraction. The CUDA 12 ecosystem now offers mature, production-ready libraries that can achieve **10-500x speedups** over CPU-based processing.

### Core libraries for GPU audio processing

**NVIDIA NeMo** (github.com/NVIDIA-NeMo/NeMo) provides the most comprehensive GPU-accelerated speech toolkit. Installation for CUDA 12 requires PyTorch 2.x with the cu124 index:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install nemo_toolkit['all']
```

NeMo delivers up to **2000-6000x real-time factor** for ASR inference with CUDA Graphs and bfloat16 autocasting. Its TitaNet speaker embedding model achieves **0.66% EER** on VoxCeleb1, making it the current NVIDIA-native best for voice fingerprinting.

**torchaudio** (github.com/pytorch/audio) integrates seamlessly with PyTorch and provides GPU-accelerated transforms including Spectrogram, MelSpectrogram, MFCC, and SpecAugment. The GPU pipeline pattern enables end-to-end processing:

```python
import torch
import torchaudio.transforms as T

class AudioPipeline(torch.nn.Module):
    def __init__(self, input_freq=16000, n_fft=1024, n_mels=128):
        super().__init__()
        self.spec = T.MelSpectrogram(sample_rate=input_freq, n_fft=n_fft, n_mels=n_mels)
        self.spec_aug = torch.nn.Sequential(
            T.FrequencyMasking(freq_mask_param=15),
            T.TimeMasking(time_mask_param=35)
        )
    
    def forward(self, waveform):
        return self.spec_aug(self.spec(waveform))

pipeline = AudioPipeline().to('cuda:0')
```

**nnAudio** (github.com/KinWaiCheuk/nnAudio) offers trainable spectrogram layers using 1D CNNs, enabling millisecond-level spectrogram generation versus seconds with librosa. Its unique feature is **trainable Fourier kernels** for task-specific optimization during end-to-end training.

**cuSignal** (github.com/rapidsai/cusignal) provides GPU-accelerated SciPy Signal compatibility with **170x-500x speedups** for spectral analysis. Note: it's migrating to CuPy's `cupyx.scipy.signal` module. For polyphase resampling and spectrogram computation, it remains the fastest option.

### Multi-GPU architecture for asymmetric GPUs

Your RTX 3090 Ti (24GB) and RTX 3060 (12GB) require task-based distribution rather than traditional DataParallel. The optimal pattern is **pipeline parallelism**:

| GPU | Memory | Role | Batch Size |
|-----|--------|------|------------|
| RTX 3090 Ti | 24GB | Embedding extraction, large models | 64-128 |
| RTX 3060 | 12GB | Preprocessing, mel-spectrograms, pitch | 32-48 |

```python
class VoicePipeline:
    def __init__(self):
        self.mel_extractor = MelSpectrogram().to('cuda:1')  # 3060
        self.voice_encoder = TitaNet().to('cuda:0')  # 3090 Ti
    
    def forward(self, audio):
        mel = self.mel_extractor(audio.to('cuda:1'))
        embedding = self.voice_encoder(mel.to('cuda:0'))
        return embedding
```

For GPU pitch detection, **torchcrepe** (github.com/maxrmorrison/torchcrepe) and **FCPE** (github.com/CNChTu/FCPE) offer real-time performance. FCPE achieves **RTF 0.0062 on RTX 4090** with 96.79% accuracy on MIR-1K—significantly faster than CREPE while maintaining accuracy.

---

## Speaker embedding and voice fingerprinting models

Speaker embeddings form the foundation of voice cloning dataset organization, enabling similarity search, clustering, and uniqueness detection across hundreds of thousands of voices.

### State-of-the-art embedding models

**ECAPA-TDNN** remains the gold standard for speaker verification, achieving **0.80% EER** on VoxCeleb1-test. The architecture combines 1D Res2Net modules with Squeeze-Excitation blocks and attentive statistical pooling:

```python
from speechbrain.inference.speaker import EncoderClassifier
classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
embeddings = classifier.encode_batch(signal)  # 192-dim embedding
```

**TitaNet** (NVIDIA) uses depth-wise separable convolutions with channel attention, achieving **0.66% EER**—the current state-of-the-art. Available in NeMo:

```python
import nemo.collections.asr as nemo_asr
speaker_model = nemo_asr.models.EncDecSpeakerLabelModel.from_pretrained(
    "nvidia/speakerverification_en_titanet_large"
)
embeddings = speaker_model.get_embedding('audio.wav')
```

**WavLM** (Microsoft) excels for general speech representation but requires fine-tuning for speaker verification. Best results come from combining WavLM features with ECAPA-TDNN backends, achieving **0.39% EER** on Vox1-O according to ESPnet-SPK benchmarks.

| Model | Embedding Dim | EER (VoxCeleb1) | Framework | Best For |
|-------|--------------|-----------------|-----------|----------|
| TitaNet-L | 192 | 0.66% | NeMo | NVIDIA ecosystem |
| ECAPA-TDNN | 192 | 0.80% | SpeechBrain | General purpose |
| Resemblyzer | 256 | ~5% | PyTorch | Voice cloning |
| WavLM-SV | 512 | ~10% | Transformers | Multi-task |

### Building searchable voice fingerprint databases

**FAISS** (github.com/facebookresearch/faiss) enables billion-scale similarity search. For voice databases, use **IndexIVFFlat** for 100K-1M embeddings or **IndexHNSWFlat** for optimal recall/speed:

```python
import faiss
dimension = 192  # ECAPA-TDNN embedding size
index = faiss.IndexHNSWFlat(dimension, 32)  # 32 neighbors per node
index.hnsw.efConstruction = 64
index.add(embeddings.astype('float32'))

# Search for similar voices
distances, indices = index.search(query.reshape(1, -1), k=10)
```

For production deployments, **pgvector** with PostgreSQL combines metadata storage with vector search:

```sql
CREATE EXTENSION vector;
CREATE TABLE voice_embeddings (
    id UUID PRIMARY KEY,
    embedding vector(192),
    speaker_id VARCHAR(64),
    quality_score FLOAT
);
CREATE INDEX ON voice_embeddings USING hnsw (embedding vector_cosine_ops);
```

### Voice uniqueness detection

Measure voice distinctiveness using outlier detection in embedding space:

```python
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

# Isolation Forest for uniqueness scoring
detector = IsolationForest(contamination=0.1)
outlier_scores = detector.fit_predict(all_embeddings)
# -1 indicates potentially unique voice

# Mean similarity approach
def compute_uniqueness(target_emb, database_embs):
    similarities = cosine_similarity(target_emb, database_embs)
    return 1 - similarities.mean()  # Lower similarity = more unique
```

---

## Speaker diarization and voice separation

Extracting clean single-speaker segments from mixed audio is essential for voice cloning dataset preparation. Modern neural diarization achieves near-human performance.

**pyannote-audio 3.1** (github.com/pyannote/pyannote-audio) provides end-to-end speaker diarization with overlap detection:

```python
from pyannote.audio import Pipeline
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
pipeline.to(torch.device("cuda"))

diarization = pipeline("audio.wav", min_speakers=2, max_speakers=5)
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"{turn.start:.1f}s - {turn.end:.1f}s: {speaker}")
```

**NVIDIA NeMo** offers clustering-based and neural diarization with TitaNet embeddings integration, achieving **1.73% DER** on AMI with oracle VAD.

For source separation, **SepFormer** (SpeechBrain) provides state-of-the-art 2-3 speaker separation:

```python
from speechbrain.inference.separation import SepformerSeparation
separator = SepformerSeparation.from_hparams(source="speechbrain/sepformer-wsj02mix")
sources = separator.separate_file(path='mixture.wav')  # Returns separated streams
```

**Demucs** (github.com/facebookresearch/demucs) excels at vocal extraction from music, using hybrid Transformer architecture for state-of-the-art separation quality.

---

## Voice quality assessment for dataset curation

Automated quality filtering is essential for large-scale dataset curation. Modern MOS estimators achieve high correlation with human ratings without reference audio.

### MOS estimation models

**UTMOS** (torch.hub.load "tarepan/SpeechMOS") won VoiceMOS Challenge 2022 and provides the simplest high-quality implementation:

```python
import torch
predictor = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)
mos_score = predictor(torch.from_numpy(wave).unsqueeze(0), sr)  # Returns 1-5 scale
```

**NISQA** (github.com/gabrielmittag/NISQA) predicts overall MOS plus four quality dimensions: Noisiness, Coloration, Discontinuity, and Loudness—ideal for detailed quality profiling.

**DNSMOS** (Microsoft) outputs SIG (signal), BAK (background), and OVRL (overall) scores, optimized for noise suppressor evaluation. Available in TorchMetrics:

```python
from torchmetrics.functional.audio.dnsmos import deep_noise_suppression_mean_opinion_score
scores = deep_noise_suppression_mean_opinion_score(audio, 16000)
```

### Voice Activity Detection comparison

| Tool | Speed | GPU | Model Size | Best For |
|------|-------|-----|------------|----------|
| Silero VAD | <1ms/30ms | Limited | 2MB | Production, 6000+ languages |
| pyannote VAD | ~5s/6min | Yes | ~50MB | Integrated diarization |
| NeMo MarbleNet | Fast | Yes | 91.5K params | NVIDIA ecosystem |

**Silero VAD** (github.com/snakers4/silero-vad) is the production choice—**28-30x faster than real-time** with enterprise-grade accuracy:

```python
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
model = load_silero_vad()
wav = read_audio('audio.wav', sampling_rate=16000)
timestamps = get_speech_timestamps(wav, model, return_seconds=True)
```

### Audio enhancement pipeline

**DeepFilterNet** (github.com/Rikorose/DeepFilterNet) provides GPU-accelerated noise reduction for full-band audio:

```python
from df.enhance import enhance, init_df, load_audio, save_audio
model, df_state, _ = init_df()
audio, _ = load_audio("noisy.wav", sr=df_state.sr())
enhanced = enhance(model, df_state, audio)
```

**NARA-WPE** (github.com/fgnt/nara_wpe) handles dereverberation using Weighted Prediction Error algorithm, essential for cleaning room-recorded audio.

---

## Voice characteristic analysis algorithms

Detailed voice profiling enables dataset organization by pitch, timbre, age, gender, accent, and emotional characteristics.

### Pitch tracking comparison

| Algorithm | Speed | Accuracy | GPU | Real-time |
|-----------|-------|----------|-----|-----------|
| FCPE | Very Fast | Excellent | Yes | Yes |
| CREPE | Medium | Excellent | Yes | Limited |
| PYIN | Fast | Very Good | No | Yes |
| Harvest | Slow | Excellent | No | No |

**FCPE** (pip install torchfcpe) offers the best speed/accuracy tradeoff for voice cloning:

```python
from torchfcpe import spawn_bundled_infer_model
model = spawn_bundled_infer_model(device="cuda")
f0 = model.infer(audio_tensor, sr=16000)
```

**pyworld** provides DIO (real-time) and Harvest (accurate) F0 extraction plus the complete WORLD vocoder for analysis-synthesis:

```python
import pyworld as pw
f0, t = pw.harvest(x, fs)  # Accurate F0
sp = pw.cheaptrick(x, f0, t, fs)  # Spectral envelope
ap = pw.d4c(x, f0, t, fs)  # Aperiodicity
```

### Voice quality metrics with Parselmouth

**Parselmouth** (github.com/YannickJadoul/Parselmouth) wraps Praat for jitter, shimmer, HNR, and formant analysis:

```python
import parselmouth
from parselmouth.praat import call

sound = parselmouth.Sound("audio.wav")
pitch = call(sound, "To Pitch (cc)", 0, 75, 15, 'no', 0.03, 0.45, 0.01, 0.35, 0.14, 500)
point_process = call(sound, "To PointProcess (periodic, cc)", 75, 500)

# Voice quality measures
harmonicity = call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
hnr = call(harmonicity, "Get mean", 0, 0)  # >12 dB = clear voice
jitter = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)  # <1.04% = stable
shimmer = call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
```

### Speaker attribute detection

**Age/Gender detection** achieves ~94% accuracy using x-vector embeddings with classification heads. **Accent detection** using ECAPA-TDNN reaches 75-87% accuracy:

```python
from speechbrain.pretrained import EncoderClassifier
classifier = EncoderClassifier.from_hparams(source="Jzuluaga/accent-id-commonaccent_ecapa")
prob, score, index, label = classifier.classify_file('audio.wav')
# Supports 16 English accents
```

**openSMILE** (pip install opensmile) extracts the ComParE 2016 feature set (6,373 features) or eGeMAPS (88 features) for comprehensive paralinguistic analysis.

---

## Comprehensive voice dataset catalog

The following datasets are suitable for voice cloning, ranked by quality and use case.

### High-quality single-speaker datasets

| Dataset | Hours | Format | License | Notes |
|---------|-------|--------|---------|-------|
| **LJSpeech** | 24 | WAV 22.05kHz | Public Domain | Gold standard format |
| **Hi-Fi TTS** | 292 | WAV 44.1kHz | CC BY 4.0 | 10 speakers, 17+ hrs each |
| **LibriTTS-R** | 585 | WAV 24kHz | CC BY 4.0 | Restored audio quality |

**LJSpeech** (keithito.com/LJ-Speech-Dataset) remains the reference format for single-speaker TTS training—13,100 clips of 1-10 seconds each.

### Multi-speaker and multilingual datasets

| Dataset | Hours | Speakers | Languages | License |
|---------|-------|----------|-----------|---------|
| **VCTK** | 44 | 110 | English (multi-accent) | ODC-By |
| **Emilia** | 101,654 | Many | 6 languages | Research |
| **Common Voice** | 17,000+ | Crowd | 104 languages | CC0 |
| **CSS10** | ~100 | 10 | 10 languages | CC BY 4.0 |

**Emilia** (emilia-dataset.github.io) is the largest available dataset for spontaneous speech—**101,654 hours** across English, Chinese, German, French, Japanese, and Korean with diverse speaking styles.

### Emotional speech datasets

| Dataset | Hours | Speakers | Emotions | License |
|---------|-------|----------|----------|---------|
| **ESD** | 29 | 20 | 5 | Research only |
| **RAVDESS** | 1,440 clips | 24 actors | 8 | CC BY-NC-SA 4.0 |
| **CREMA-D** | 7,442 clips | 91 | 6 | Open research |

### Archive sources for rare voices

**LibriVox** API (librivox.org/api/feed/audiobooks) provides access to public domain audiobooks. Query parameters include author, title, genre, with extended=1 for full metadata. Download MP3s from Archive.org using item identifiers.

**Archive.org collections** of interest:
- Old Time Radio: archive.org/details/oldtimeradio
- Greatest Speeches of 20th Century: archive.org/details/Greatest_Speeches_of_the_20th_Century
- American Archive of Public Broadcasting: americanarchive.org (40,000+ digitized recordings)

---

## Audio format specifications for voice cloning

### Optimal recording and training specifications

| Parameter | Recording | Training | Notes |
|-----------|-----------|----------|-------|
| Sample Rate | 44.1-48 kHz | 22.05-24 kHz | Downsample for training |
| Bit Depth | 24-bit | 16-bit | Converts without loss |
| Channels | Mono | Mono | Stereo wastes resources |
| Format | WAV/FLAC | WAV | Lossless always |

### Format conversion best practices

```bash
# Optimal conversion to training format (22.05kHz mono 16-bit WAV)
ffmpeg -i input.mp3 -acodec pcm_s16le -ac 1 -ar 22050 output.wav

# High-quality resampling with SoX
sox input.wav -r 22050 output.wav

# Batch conversion
for i in *.mp3; do ffmpeg -i "$i" -acodec pcm_s16le -ac 1 -ar 22050 "${i%.mp3}.wav"; done
```

**Critical rule**: Never re-encode lossy files (MP3→MP3 degrades quality). Always convert from lossless source when available. For unavoidable lossy sources, minimum acceptable is **MP3 192kbps** or **AAC 128kbps**.

---

## Large-scale scraping and collection architecture

### Audio fingerprinting for deduplication

**Chromaprint** (pyacoustid) generates perceptual fingerprints for near-duplicate detection:

```python
import acoustid
import chromaprint

def generate_fingerprint(audio_file):
    duration, fp_encoded = acoustid.fingerprint_file(audio_file)
    fingerprint, version = chromaprint.decode_fingerprint(fp_encoded)
    return fingerprint, duration

# Deduplication check using fingerprint hash buckets
class AudioDeduplicator:
    def __init__(self, threshold=0.85):
        self.fingerprints = {}
        self.threshold = threshold
    
    def is_duplicate(self, audio_path):
        fp, duration = generate_fingerprint(audio_path)
        fp_hash = hash(tuple(fp[:100]))  # Quick initial check
        if fp_hash in self.fingerprints:
            for stored_fp in self.fingerprints[fp_hash]:
                if compare_fingerprints(fp, stored_fp) > self.threshold:
                    return True
        self.fingerprints.setdefault(fp_hash, []).append(fp)
        return False
```

### Content-addressable storage

Store files by SHA-256 hash for automatic deduplication:

```python
class ContentAddressableStorage:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
    
    def store(self, file_path):
        content_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
        storage_path = self.base_path / content_hash[:2] / content_hash[2:4] / content_hash
        if not storage_path.exists():
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, storage_path)
        return content_hash
```

---

## Key research papers

### Speaker embedding fundamentals
- **ECAPA-TDNN** (Interspeech 2020, arXiv:2005.07143): Introduced channel attention and aggregation for speaker verification
- **TitaNet** (ICASSP 2022, arXiv:2110.04410): NVIDIA's depth-wise separable convolution approach achieving 0.66% EER
- **X-Vectors** (ICASSP 2018): Foundational TDNN architecture with statistics pooling

### Self-supervised speech representations
- **Wav2Vec 2.0** (NeurIPS 2020, arXiv:2006.11477): Contrastive learning breakthrough for speech
- **HuBERT** (arXiv:2106.07447): BERT-like masked prediction over clustered units
- **WavLM** (arXiv:2110.13900): SOTA on SUPERB benchmark with joint denoising

### Voice quality assessment
- **NISQA** (arXiv:2104.09494): CNN-SA-AP architecture predicting MOS + quality dimensions
- **DNSMOS** (arXiv:2010.15258): Microsoft's noise suppression evaluation metric

### Zero-shot voice cloning
- **Transfer Learning to Multispeaker TTS** (Google, arXiv:1806.04558): Seminal three-component architecture
- **CosyVoice** (arXiv:2407.05407): Latest multilingual zero-shot with conditional flow matching

---

## Master system architecture

### Complete pipeline design

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                              │
│  yt-dlp Scrapers → aiohttp Downloads → File Watchers           │
│                         ↓                                       │
│              [Raw Audio Queue - Redis]                          │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│              PREPROCESSING (RTX 3060 - 12GB)                    │
│  FFprobe Metadata → Chromaprint Dedup → Audio Normalization    │
│                         ↓                                       │
│           [Deduplication Check - PostgreSQL]                    │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│           EMBEDDING EXTRACTION (RTX 3090 Ti - 24GB)             │
│  NVIDIA DALI → Mel-Spectrogram → TitaNet/ECAPA-TDNN Embeddings │
│                         ↓                                       │
│  Quality Assessment (UTMOS) → Characteristic Analysis (FCPE)   │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                │
│  Content-Addressable ←→ PostgreSQL + pgvector ←→ FAISS Index  │
│      File Storage          (Metadata)           (Embeddings)   │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    QUERY/API LAYER                              │
│  • Similarity search by voice embedding                         │
│  • Filter by quality, language, speaker attributes             │
│  • Clustering and uniqueness detection                          │
│  • Batch export for training                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Technology stack summary

| Component | Recommended | Alternative |
|-----------|-------------|-------------|
| Audio Scraping | yt-dlp | aria2, gallery-dl |
| Async HTTP | aiohttp | httpx |
| Fingerprinting | Chromaprint/pyacoustid | Dejavu |
| Metadata | FFprobe + Mutagen | TinyTag |
| Speaker Embeddings | TitaNet (NeMo) / ECAPA-TDNN (SpeechBrain) | Resemblyzer |
| MOS Estimation | UTMOS | NISQA, DNSMOS |
| VAD | Silero VAD | pyannote, MarbleNet |
| Diarization | pyannote-audio 3.1 | NeMo Diarizer |
| Noise Reduction | DeepFilterNet | RNNoise |
| Pitch Tracking | FCPE | CREPE, pyworld |
| Vector Database | FAISS + pgvector | Milvus, Qdrant |
| GPU Data Loading | NVIDIA DALI | PyTorch DataLoader |
| File Storage | Content-Addressable (SHA-256) | MinIO/S3 |
| Task Queue | Redis + Celery | RabbitMQ |
| Database | PostgreSQL + pgvector | MongoDB |

### Batch size recommendations

| GPU | Memory | Mel-Spectrogram | Embedding Extraction |
|-----|--------|-----------------|---------------------|
| RTX 3090 Ti | 24GB | 128-256 | 32-64 |
| RTX 3060 | 12GB | 48-96 | 12-24 |

This architecture can process **50,000-100,000 audio files per day** with proper pipelining, producing searchable voice fingerprint databases with quality scores, speaker attributes, and similarity clustering—ready for voice cloning model training.