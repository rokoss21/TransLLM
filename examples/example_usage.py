#!/usr/bin/env python3
"""
TransLLM Example Usage
=====================

This script demonstrates various ways to use TransLLM for code translation.
"""

import os
import sys
sys.path.append('..')

from project_translator import ProjectTranslator, TranslationConfig


def example_basic_translation():
    """Basic translation example using default settings"""
    print("🔥 Basic Translation Example")
    print("=" * 40)
    
    # Configure translation
    config = TranslationConfig(
        source_project_path="./sample_project",  # Your project path here
        target_language="English",
        source_language="Russian", 
        llm_provider="groq",
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="openai/gpt-oss-120b",
        chunk_size=150,
        max_concurrent_requests=10
    )
    
    # Create translator instance
    translator = ProjectTranslator(config)
    
    # Note: This would run the actual translation
    print("Configuration ready for translation:")
    print(f"  📁 Source: {config.source_project_path}")
    print(f"  🌍 Target Language: {config.target_language}")
    print(f"  🤖 Provider: {config.llm_provider}")
    print(f"  📊 Model: {config.model_name}")
    
    # To actually run translation, uncomment:
    # await translator.translate_project()


def example_multilingual_translation():
    """Example of translating to multiple languages"""
    print("\n🌏 Multilingual Translation Example")
    print("=" * 40)
    
    languages = ["English", "French", "German", "Spanish"]
    
    for lang in languages:
        config = TranslationConfig(
            source_project_path="./sample_project",
            target_language=lang,
            source_language="Russian",
            llm_provider="groq",
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="openai/gpt-oss-120b"
        )
        
        print(f"  📝 Ready to translate to: {lang}")
        # translator = ProjectTranslator(config)
        # await translator.translate_project()


def example_custom_instructions():
    """Example with custom translation instructions"""
    print("\n⚙️ Custom Instructions Example")
    print("=" * 40)
    
    custom_instructions = """
    Additional instructions:
    - Preserve all brand names and product names
    - Use technical terminology consistently
    - Maintain formal tone for documentation
    - Keep code examples unchanged
    """
    
    config = TranslationConfig(
        source_project_path="./sample_project",
        target_language="English",
        custom_instructions=custom_instructions,
        llm_provider="groq",
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    print("  📋 Custom instructions configured")
    print("  🎯 Translation will follow specific guidelines")


def example_different_providers():
    """Example showing different LLM providers"""
    print("\n🔄 Multiple Providers Example")
    print("=" * 40)
    
    providers = [
        ("groq", "openai/gpt-oss-120b", "GROQ_API_KEY"),
        ("openai", "gpt-4", "OPENAI_API_KEY"),
        ("anthropic", "claude-3-sonnet-20240229", "ANTHROPIC_API_KEY")
    ]
    
    for provider, model, env_key in providers:
        api_key = os.getenv(env_key)
        if api_key:
            config = TranslationConfig(
                source_project_path="./sample_project",
                target_language="English",
                llm_provider=provider,
                model_name=model,
                api_key=api_key
            )
            print(f"  ✅ {provider.upper()}: {model}")
        else:
            print(f"  ❌ {provider.upper()}: API key not found ({env_key})")


def example_performance_tuning():
    """Example showing performance optimization settings"""
    print("\n🚀 Performance Tuning Example")
    print("=" * 40)
    
    # For large projects
    large_project_config = TranslationConfig(
        source_project_path="./large_project",
        chunk_size=100,  # Smaller chunks for better accuracy
        max_concurrent_requests=20,  # More concurrent requests
        llm_provider="groq",  # Fast provider
        model_name="openai/gpt-oss-120b"  # Fast model
    )
    
    # For small projects with high accuracy
    small_project_config = TranslationConfig(
        source_project_path="./small_project", 
        chunk_size=200,  # Larger chunks for context
        max_concurrent_requests=5,  # Fewer concurrent requests
        llm_provider="openai",
        model_name="gpt-4"  # High-quality model
    )
    
    print("  📊 Large project: Optimized for speed")
    print("  🎯 Small project: Optimized for accuracy")


if __name__ == "__main__":
    print("🌟 TransLLM Usage Examples")
    print("=" * 50)
    
    # Check if API keys are available
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  Set GROQ_API_KEY environment variable to run examples")
        print("   export GROQ_API_KEY='your-key-here'")
        print()
    
    # Run examples
    example_basic_translation()
    example_multilingual_translation() 
    example_custom_instructions()
    example_different_providers()
    example_performance_tuning()
    
    print("\n✨ Examples completed!")
    print("📚 Check README.md for full documentation")
