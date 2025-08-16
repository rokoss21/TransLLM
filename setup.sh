#!/bin/bash

# TransLLM Setup Script
echo "🚀 Setting up TransLLM - Universal Code Translator"
echo "=================================================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip

# Install Groq by default
echo "Installing Groq provider..."
pip install groq

echo ""
echo "✅ TransLLM setup completed!"
echo ""
echo "🔑 To get started, set your API key:"
echo "   export GROQ_API_KEY='your-api-key-here'"
echo ""
echo "📋 Basic usage:"
echo "   python3 quick_translate.py /path/to/project --model openai/gpt-oss-120b"
echo ""
echo "📚 For more providers, install:"
echo "   pip install openai      # For OpenAI"
echo "   pip install anthropic   # For Anthropic"
echo ""
echo "🎯 Ready to translate! 🌍✨"
