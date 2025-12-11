# Model Configuration Quick Start Guide

## 🚀 Quick Setup for 7B and Smaller Models

This guide helps you configure the AI Project Synthesizer to use optimal 7B and smaller models for the best performance and resource efficiency.

## 📋 Step 1: Choose Your LLM Provider

### Option A: Ollama (Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve
```

### Option B: LM Studio
1. Download and install LM Studio from https://lmstudio.ai/
2. Start LM Studio and load your preferred models
3. Ensure the server is running on localhost:1234

## 📋 Step 2: Pull Recommended Models

### For Ollama Users
```bash
# Pull the recommended 7B model (DEFAULT - best balance)
ollama pull qwen2.5-coder:7b-instruct-q8_0

# Optional: Pull smaller models for faster responses
ollama pull qwen2.5-coder:3b-instruct
ollama pull qwen2.5-coder:1.5b-instruct

# Optional: Pull larger model for complex tasks
ollama pull qwen2.5-coder:14b-instruct-q4_K_M
```

### For LM Studio Users
1. Open LM Studio
2. Search and download your preferred models:
   - **7B models**: `Qwen2.5-Coder-7B-Instruct` (recommended)
   - **3B models**: `Qwen2.5-Coder-3B-Instruct` (faster)
   - **1.5B models**: `Qwen2.5-Coder-1.5B-Instruct` (fastest)

## 📋 Step 3: Configure Your Environment

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

### Basic Configuration (Recommended)
```env
# Use 7B models by default - best performance/resource balance
LLM_MODEL_SIZE_PREFERENCE=medium
LLM_PREFERRED_PROVIDER=ollama

# Enable fallback between providers
LLM_FALLBACK_ENABLED=true
```

### Lightweight Setup (for older computers)
```env
# Use 3B models for faster responses
LLM_MODEL_SIZE_PREFERENCE=small
LLM_PREFERRED_PROVIDER=ollama
```

### Maximum Performance Setup
```env
# Use 14B models for complex tasks
LLM_MODEL_SIZE_PREFERENCE=large
LLM_PREFERRED_PROVIDER=ollama
```

## 📋 Step 4: Verify Your Setup

### Test Ollama
```bash
# Check if Ollama is running
ollama list

# Test a model
ollama run qwen2.5-coder:7b-instruct-q8_0
```

### Test LM Studio
1. Open LM Studio
2. Check that your model is loaded in the "Loaded Models" tab
3. Verify the server is running on localhost:1234

## 🎯 Model Size Guide

| Size | Parameters | Use Case | Performance | Resource Usage |
|------|------------|----------|-------------|----------------|
| **Tiny** | < 2B | Quick formatting, simple questions | ⚡ Fastest | 💚 Lowest |
| **Small** | 2-4B | Code review, basic analysis | ⚡ Fast | 💚 Low |
| **Medium** | 4-7B | **DEFAULT** - Most tasks | 🚀 Balanced | 💛 Medium |
| **Large** | 8-14B | Complex architecture, multi-file | 🐢 Slower | ❤️ High |

## 🔄 Seamless Model Switching

### Change Model Size Instantly
```env
# For speed (1.5B models)
LLM_MODEL_SIZE_PREFERENCE=tiny

# For balanced performance (3B models)  
LLM_MODEL_SIZE_PREFERENCE=small

# For best overall experience (7B models) - RECOMMENDED
LLM_MODEL_SIZE_PREFERENCE=medium

# For complex tasks (14B models)
LLM_MODEL_SIZE_PREFERENCE=large
```

### Switch Between Providers
```env
# Use Ollama
LLM_PREFERRED_PROVIDER=ollama

# Use LM Studio
LLM_PREFERRED_PROVIDER=lmstudio
```

## 🎛️ Advanced Configuration

### Custom Model Names
If you have different model names, update them in `.env`:

```env
# For Ollama
OLLAMA_MODEL_MEDIUM=your-custom-7b-model

# For LM Studio  
LMSTUDIO_MODEL_MEDIUM=Your-Custom-7B-Model-Name
```

### Provider Fallback
Enable automatic fallback between providers:

```env
# Try Ollama first, fall back to LM Studio if unavailable
LLM_PREFERRED_PROVIDER=ollama
LLM_FALLBACK_ENABLED=true
LMSTUDIO_ENABLED=true
```

### Cloud Fallback (Optional)
```env
# Fall back to cloud if local providers are unavailable
CLOUD_LLM_ENABLED=true
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## 🔍 Troubleshooting

### Model Not Found
```bash
# For Ollama: Check available models
ollama list

# For LM Studio: Verify model name matches exactly
# Model names are case-sensitive!
```

### Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check if LM Studio is running  
curl http://localhost:1234/v1/models
```

### Performance Issues
- **Slow responses**: Try smaller model size (`tiny` or `small`)
- **Poor quality**: Try larger model size (`large`)
- **Out of memory**: Reduce model size or close other applications

## 📊 Recommended Configurations

### 🏠 Home/Personal Use
```env
LLM_MODEL_SIZE_PREFERENCE=medium
LLM_PREFERRED_PROVIDER=ollama
LLM_FALLBACK_ENABLED=true
```

### 💼 Laptop/Portable
```env
LLM_MODEL_SIZE_PREFERENCE=small
LLM_PREFERRED_PROVIDER=ollama
LLM_FALLBACK_ENABLED=true
```

### 🖥️ Desktop/Power User
```env
LLM_MODEL_SIZE_PREFERENCE=large
LLM_PREFERRED_PROVIDER=ollama
LLM_FALLBACK_ENABLED=true
```

### 🌐 Multi-Provider Setup
```env
LLM_PREFERRED_PROVIDER=ollama
LLM_MODEL_SIZE_PREFERENCE=medium
LLM_FALLBACK_ENABLED=true
LMSTUDIO_ENABLED=true
CLOUD_LLM_ENABLED=true
```

## 🎉 You're Ready!

Your AI Project Synthesizer is now configured to use optimal 7B and smaller models with intelligent routing and seamless switching. The system will automatically:

- Select the best model based on your preference and task complexity
- Fall back between providers if one is unavailable
- Scale model size up or down based on task requirements
- Provide the best balance of performance and resource usage

Start using the synthesizer and enjoy fast, efficient AI assistance! 🚀
