# TransLLM - Universal Code Translator

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/rokoss21/TransLLM.svg)](https://github.com/rokoss21/TransLLM/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/rokoss21/TransLLM.svg)](https://github.com/rokoss21/TransLLM/issues)
[![GitHub Release](https://img.shields.io/github/release/rokoss21/TransLLM.svg)](https://github.com/rokoss21/TransLLM/releases)

**🌍 Intelligent code translation that preserves structure while translating human-readable content**

*Supports 20+ programming languages • Multiple LLM providers • Structure-preserving translation*

[🚀 Quick Start](#-quick-start) • [📖 Documentation](docs/) • [⭐ Features](#-features) • [🤝 Contributing](#-contributing)

</div>

---

🚀 **TransLLM** is a powerful universal code translation system that preserves code structure while translating comments, docstrings, and user-facing strings using various LLM providers.

## ✨ Features

- **Universal Language Support**: Works with Python, JavaScript, TypeScript, Go, Java, C++, C#, PHP, Ruby, Rust, Swift, Kotlin, Dart, Vue, Svelte
- **Multiple LLM Providers**: Groq, OpenAI, Anthropic
- **Structure Preservation**: Maintains exact code structure, syntax, indentation, and formatting
- **Chunk Boundary Markers**: Innovative approach to ensure perfect code merging
- **Concurrent Processing**: Parallel translation with configurable concurrency limits
- **Validation System**: Built-in integrity checks for translated code
- **Backup & Recovery**: Automatic project backups before translation

## 🎯 Key Innovation: Chunk Boundary Markers

Our system uses special markers (`---CHUNK_START_XXXX---` and `---CHUNK_END_XXXX---`) to ensure perfect merging of translated code chunks, eliminating syntax errors that occur when joining translated segments.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/rokoss21/TransLLM.git
cd TransLLM

# Install dependencies
pip install -r requirements.txt
```

### Setup API Keys

1. Copy the example config:
   ```bash
   cp config.json.example config.json
   ```

2. Edit `config.json` and add your API key:
   ```json
   {
     "llm_provider": "groq",
     "api_key": "your-actual-api-key-here",
     "model_name": "llama-3.1-70b-versatile"
   }
   ```

3. Or set environment variable:
   ```bash
   export GROQ_API_KEY='your-api-key-here'
   ```

### Basic Usage

```bash
# Translate a project
python3 project_translator.py /path/to/your/project

# Quick translation with specific model
python3 quick_translate.py /path/to/your/project --model llama-3.1-70b-versatile
```

### Advanced Usage

```bash
# Custom configuration
python3 quick_translate.py /path/to/project \
  --lang French \
  --provider openai \
  --model gpt-4 \
  --chunk-size 100 \
  --concurrent 5 \
  --formal
```

## 📋 Command Line Options

- `--lang` / `-l`: Target language (default: English)
- `--provider` / `-p`: LLM provider (groq, openai, anthropic)
- `--model` / `-m`: Model name
- `--concurrent` / `-c`: Max concurrent requests (default: 10)
- `--chunk-size`: Lines per chunk (default: 150)
- `--dry-run`: Analyze only, no translation
- `--chinese`: Preserve Chinese characters
- `--formal`: Use formal tone

## 🔧 Configuration

Create `translation_config.json` for project defaults:

```json
{
  "default_config": {
    "target_language": "English",
    "llm_provider": "groq",
    "chunk_size": 150,
    "max_concurrent_requests": 10
  },
  "llm_providers": {
    "groq": {
      "models": ["openai/gpt-oss-120b", "mixtral-8x7b-32768"]
    },
    "openai": {
      "models": ["gpt-4", "gpt-3.5-turbo"]
    }
  },
  "custom_instructions_templates": {
    "preserve_chinese": "保留所有中文字符和表达方式",
    "formal_tone": "Use formal and professional tone"
  }
}
```

## 🔬 How It Works

**TransLLM** employs a sophisticated multi-stage translation algorithm that ensures code structure preservation while translating human-readable content. Here's the core algorithm:

<div align="center">

### 🧠 Translation Algorithm

```pseudocode
FUNCTION translate_project(project_path, target_language):
    // Stage 1: Project Discovery & Analysis
    discovered_files = scan_directory(project_path)
    translatable_files = filter_supported_extensions(discovered_files)
    total_chunks = estimate_chunk_count(translatable_files)
    
    // Stage 2: Smart File Chunking
    FOR EACH file IN translatable_files:
        chunks = split_into_chunks(file, chunk_size)
        FOR EACH chunk:
            chunk.add_boundary_markers(unique_id)
            chunk.preserve_structure_metadata()
    
    // Stage 3: Concurrent LLM Translation  
    translation_pool = create_thread_pool(max_concurrent)
    FOR EACH chunk IN parallel:
        translated_chunk = llm_translate(
            chunk.content,
            source_lang,
            target_lang,
            preserve_code_structure=True
        )
        validate_chunk_integrity(translated_chunk)
    
    // Stage 4: Intelligent Chunk Reconstruction
    FOR EACH file:
        merged_content = merge_chunks_by_boundary_markers()
        validate_structure_preservation(original, merged_content)
        validate_syntax_correctness(merged_content)
    
    // Stage 5: Quality Assurance
    validation_report = run_comprehensive_validation()
    RETURN translation_results, validation_report
END FUNCTION
```

</div>

### 🎯 Key Algorithm Features

| Stage | Innovation | Benefit |
|-------|------------|----------|
| **Discovery** | Smart file filtering | Only processes translatable content |
| **Chunking** | Boundary marker injection | Perfect chunk reconstruction |
| **Translation** | Structure-aware prompting | Preserves code syntax & formatting |
| **Reconstruction** | Marker-based merging | Eliminates join errors |
| **Validation** | Multi-layer integrity checks | Ensures translation quality |

## 📊 Translation Process

1. **Project Analysis**: Scans supported files and estimates chunks
2. **File Chunking**: Splits files with boundary markers
3. **LLM Translation**: Parallel processing with structure preservation
4. **Chunk Merging**: Intelligent reconstruction using boundary markers
5. **Validation**: Structure and syntax integrity checks
6. **Report Generation**: Detailed translation statistics

## 🎯 What Gets Translated

✅ **Translated:**
- Comments (`// comment`, `# comment`)
- Docstrings (`"""docstring"""`, `/* docstring */`)
- String literals with natural language
- Error messages and user-facing text

❌ **Preserved:**
- Variable names, function names, class names
- Technical keywords and syntax
- File paths, URLs, configuration keys
- Regular expressions and SQL queries
- Special symbols and patterns

## 🔍 Validation Features

- **Line Count Verification**: Ensures exact line count preservation
- **Structure Analysis**: Checks code structure integrity
- **Compilation Testing**: Validates that translated code compiles
- **Detailed Reporting**: Shows success rates and error details

## 📈 Performance

- **Concurrent Processing**: Up to 10 simultaneous API requests
- **Chunk Optimization**: Intelligent file segmentation
- **Error Recovery**: Graceful handling of API failures
- **Progress Tracking**: Real-time translation progress

## 🛠 Supported File Types

- `.py` - Python
- `.js`, `.ts`, `.jsx`, `.tsx` - JavaScript/TypeScript
- `.go` - Go
- `.java` - Java
- `.cpp`, `.c`, `.h` - C/C++
- `.cs` - C#
- `.php` - PHP
- `.rb` - Ruby
- `.rs` - Rust
- `.swift` - Swift
- `.kt` - Kotlin
- `.dart` - Dart
- `.vue` - Vue.js
- `.svelte` - Svelte
- `.html`, `.css`, `.scss` - Web technologies

## 📝 Example Output

```
🎯 Translation Configuration:
   Project: my-awesome-project
   Target Language: English
   Provider: groq
   Model: openai/gpt-oss-120b
   Chunk Size: 150
   Concurrent Requests: 10

🚀 Starting project translation...
📊 Analyzing project structure...
Found files: 124
Files for translation: 67
Expected chunks: 203

✂️ Splitting files into chunks...
Created 203 chunks

🌐 Starting chunk translation...
Translated 203/203 chunks in 45.2 seconds

🔗 Merging translated chunks...
Successfully merged 65/67 files

✅ Translation completed! Result saved to: my-awesome-project_translated
📊 Report saved: my-awesome-project_translated/TRANSLATION_REPORT.json
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```bash
   export GROQ_API_KEY='your-key-here'
   ```

2. **Line Count Mismatches**
   - Usually cosmetic, check if code compiles
   - LLM may slightly adjust comment formatting

3. **Structure Changes**
   - Validation system detects but may be overly strict
   - Compiled code indicates successful translation

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
git clone https://github.com/rokoss21/TransLLM.git
cd TransLLM
pip install -r requirements.txt
```

### Contributing Guidelines

- Fork the repository
- Create your feature branch (`git checkout -b feature/AmazingFeature`)
- Commit your changes (`git commit -m 'Add some AmazingFeature'`)
- Push to the branch (`git push origin feature/AmazingFeature`)
- Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Author

**Created by [Emil Rokossovskiy](https://github.com/rokoss21)**

If you find this project useful, please consider giving it a ⭐!

---

<div align="center">

**TransLLM** - Making code translation seamless and structure-preserving! 🌍✨

[![GitHub](https://img.shields.io/badge/GitHub-rokoss21-181717?logo=github)](https://github.com/rokoss21)
[![Stars](https://img.shields.io/github/stars/rokoss21/TransLLM?style=social)](https://github.com/rokoss21/TransLLM/stargazers)

*Built with ❤️ for the global developer community*

</div>
