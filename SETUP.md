# TransLLM Setup Guide

## Quick Setup

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/rokoss21/TransLLM.git
cd TransLLM
pip install -r requirements.txt
```

### 2. Configure API Key

#### Option A: Using config.json (Recommended)

```bash
# Copy example config
cp config.json.example config.json

# Edit config.json and add your API key:
# Replace "YOUR_GROQ_API_KEY_HERE" with your actual API key
```

#### Option B: Environment Variable

```bash
export GROQ_API_KEY='your-actual-api-key-here'
```

### 3. Get API Keys

#### Groq (Recommended - Fast & Free)
1. Visit [https://console.groq.com/](https://console.groq.com/)
2. Sign up for free
3. Create an API key
4. Use models: `llama-3.1-70b-versatile`, `mixtral-8x7b-32768`

#### OpenAI (Premium)
1. Visit [https://platform.openai.com/](https://platform.openai.com/)
2. Create account and add billing
3. Generate API key
4. Use models: `gpt-4`, `gpt-3.5-turbo`

#### Anthropic (Premium)
1. Visit [https://console.anthropic.com/](https://console.anthropic.com/)
2. Create account and add credits
3. Generate API key  
4. Use models: `claude-3-sonnet-20240229`

### 4. Test Your Setup

```bash
# Check if everything works
python3 project_translator.py --help

# Test with example (dry run)
python3 quick_translate.py examples/ --dry-run
```

## Configuration Options

### Basic config.json

```json
{
  "llm_provider": "groq",
  "model_name": "llama-3.1-70b-versatile", 
  "api_key": "your-actual-api-key-here",
  "target_language": "English",
  "source_language": "Russian",
  "chunk_size": 100,
  "temperature": 0.0,
  "max_concurrent_requests": 5
}
```

### Recommended Models

| Provider | Model | Speed | Quality | Cost |
|----------|-------|-------|---------|------|
| Groq | `llama-3.1-70b-versatile` | ⚡ Fast | 🟢 Good | 🟢 Free |
| Groq | `mixtral-8x7b-32768` | ⚡ Fast | 🟢 Good | 🟢 Free |
| OpenAI | `gpt-4` | 🟡 Slow | 🔵 Excellent | 🔴 Expensive |
| OpenAI | `gpt-3.5-turbo` | 🟢 Medium | 🟢 Good | 🟡 Moderate |

## First Translation

```bash
# Translate a small project
python3 project_translator.py /path/to/your/project

# With custom settings
python3 quick_translate.py /path/to/project \
  --lang English \
  --provider groq \
  --model llama-3.1-70b-versatile \
  --chunk-size 150 \
  --concurrent 10
```

## Troubleshooting

### "API key not set" Error
```bash
# Check your config.json has the real API key
cat config.json | grep api_key

# Or set environment variable
export GROQ_API_KEY='your-key-here'
```

### Rate Limiting
```bash
# Reduce concurrent requests
python3 project_translator.py /path/to/project --max-concurrent 1
```

### Large Projects
```bash
# Use larger chunks to reduce API calls
python3 project_translator.py /path/to/project --chunk-size 200
```

## Security Notes

- Never commit `config.json` with real API keys to git
- Use `config.json.example` as template  
- The `.gitignore` excludes `config.json` automatically
- Keep your API keys secure and rotate them periodically

## Next Steps

1. ✅ Setup complete - try translating a small test project
2. 📖 Read [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) for advanced usage
3. 🚀 See [docs/ENHANCED_FEATURES.md](docs/ENHANCED_FEATURES.md) for all features

Happy translating! 🌍✨
